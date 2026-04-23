#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
from dataclasses import asdict
import hashlib
import json
from pathlib import Path
import shutil
import sys
import time
import traceback
from typing import Callable, Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_runtime_config
from implementation import config as config_lib
from implementation import llm_client as llm_client_lib
from scripts._runner import build_runtime_variant
from scripts._runner import make_timestamp
from scripts._runtime_patches import patched_iteration_runtime
from scripts._runtime_patches import probe_reasoning_support
from scripts._runner import run_logged_experiment
from scripts.compare_rag import AcceptanceConfig
from scripts.compare_rag import ComparePolicyConfig
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import evaluate_acceptance
from scripts.compare_rag import parse_run_log
from scripts.experiments.rag_iteration_config import ModelRunSpec
from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig
from scripts.experiments.rag_iteration_config import ReasoningProbeSpec
from scripts.experiments.space import build_density_phase_candidates
from scripts.experiments.space import build_primary_candidate_space
from scripts.experiments.space import build_query_phase_candidates


SCRIPT_CONFIG = RAGIterationConfig()
RUNTIME_DEFAULTS = config_lib.apply_runtime_defaults_environment_overrides()
DEFAULT_RAG_CONFIG = config_lib.RAGConfig()


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _sha256_of_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as file_handle:
        for chunk in iter(lambda: file_handle.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def _serialize_reasoning_probe(reasoning_probe: ReasoningProbeSpec | None) -> dict[str, object] | None:
    if reasoning_probe is None:
        return None
    payload: dict[str, object] = {"request_mode": reasoning_probe.request_mode}
    if reasoning_probe.reasoning_effort is not None:
        payload["reasoning_effort"] = reasoning_probe.reasoning_effort
    return payload


def _build_experiment_dir_name(timestamp: str, model_spec: ModelRunSpec) -> str:
    return f"{timestamp}_{model_spec.result_label}"


def _build_baseline_log_paths(experiment_dir: Path) -> tuple[Path, Path]:
    return experiment_dir / "baseline_stage1.log", experiment_dir / "baseline_stage2.log"


def _build_reasoning_probe_label(reasoning_probe: ReasoningProbeSpec | None) -> str:
    if reasoning_probe is None:
        return "reasoning_off"
    if reasoning_probe.reasoning_effort is None:
        return reasoning_probe.request_mode
    return f"{reasoning_probe.request_mode}_{reasoning_probe.reasoning_effort}"


def _build_baseline_cache_paths(
    *,
    results_dir: Path,
    iteration_config: RAGIterationConfig,
    model_spec: ModelRunSpec,
    reasoning_probe: ReasoningProbeSpec | None,
) -> tuple[Path, Path]:
    probe_label = _build_reasoning_probe_label(reasoning_probe if iteration_config.enable_thinking else None)
    cache_dir = results_dir / "_baseline_cache" / model_spec.result_label
    stage1_log = cache_dir / (
        f"seed{iteration_config.seed}_{iteration_config.run_mode}_{probe_label}"
        f"_stage1_budget{iteration_config.stage1_budget}.log"
    )
    stage2_log = cache_dir / (
        f"seed{iteration_config.seed}_{iteration_config.run_mode}_{probe_label}"
        f"_stage2_budget{iteration_config.stage2_budget}.log"
    )
    return stage1_log, stage2_log


def _copy_log_if_needed(*, source: Path, destination: Path) -> None:
    if source == destination:
        return
    destination.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(source, destination)


def _is_healthy_baseline_log(log_path: Path) -> bool:
    if not log_path.exists():
        return False
    try:
        parsed = parse_run_log(log_path)
    except Exception:
        return False
    return (
        parsed.best is not None
        and parsed.sample_lines > 0
        and parsed.valid_eval_ratio is not None
        and parsed.valid_eval_ratio > 0.0
    )


def _ensure_baseline_log(
    *,
    stage_label: str,
    cache_log_path: Path,
    experiment_log_path: Path,
    runtime_config: config_lib.Config,
    max_sample_nums: int,
    resolved_config: RAGIterationConfig,
) -> str:
    # Cache baseline logs by model and budget so repeated runs reuse identical controls.
    if cache_log_path.exists() and _is_healthy_baseline_log(cache_log_path):
        source = "cache"
        print(f"[BASELINE] reuse | stage={stage_label} | cache={cache_log_path.as_posix()}")
    else:
        source = "regenerated" if cache_log_path.exists() else "generated"
        cache_log_path.parent.mkdir(parents=True, exist_ok=True)
        if source == "regenerated":
            print(f"[BASELINE] regenerate | stage={stage_label} | cache={cache_log_path.as_posix()}")
        else:
            print(f"[BASELINE] generate | stage={stage_label} | cache={cache_log_path.as_posix()}")
        run_logged_experiment(
            label=stage_label,
            runtime_config=runtime_config,
            log_path=cache_log_path,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=max_sample_nums,
            log_dir=resolved_config.log_dir,
            header_fields={"RUN_MODE": resolved_config.run_mode, "RUN_BUDGET": max_sample_nums},
        )
    _copy_log_if_needed(source=cache_log_path, destination=experiment_log_path)
    return source


def _prepare_baseline_logs(
    *,
    experiment_dir: Path,
    results_dir: Path,
    baseline_stage1_config: config_lib.Config,
    baseline_stage2_config: config_lib.Config,
    resolved_config: RAGIterationConfig,
    resolved_model_spec: ModelRunSpec,
    selected_reasoning_probe: ReasoningProbeSpec | None,
) -> tuple[Path, Path, dict[str, str]]:
    baseline_stage1_log, baseline_stage2_log = _build_baseline_log_paths(experiment_dir)
    cached_stage1_log, cached_stage2_log = _build_baseline_cache_paths(
        results_dir=results_dir,
        iteration_config=resolved_config,
        model_spec=resolved_model_spec,
        reasoning_probe=selected_reasoning_probe,
    )
    baseline_sources = {
        "stage1": _ensure_baseline_log(
            stage_label="BASELINE_STAGE1",
            cache_log_path=cached_stage1_log,
            experiment_log_path=baseline_stage1_log,
            runtime_config=baseline_stage1_config,
            max_sample_nums=resolved_config.stage1_budget,
            resolved_config=resolved_config,
        ),
        "stage2": "pending",
    }
    return baseline_stage1_log, baseline_stage2_log, baseline_sources


def _ensure_stage2_baseline_log(
    *,
    experiment_log_path: Path,
    results_dir: Path,
    baseline_stage2_config: config_lib.Config,
    resolved_config: RAGIterationConfig,
    resolved_model_spec: ModelRunSpec,
    selected_reasoning_probe: ReasoningProbeSpec | None,
) -> str:
    _, cached_stage2_log = _build_baseline_cache_paths(
        results_dir=results_dir,
        iteration_config=resolved_config,
        model_spec=resolved_model_spec,
        reasoning_probe=selected_reasoning_probe,
    )
    return _ensure_baseline_log(
        stage_label="BASELINE_STAGE2",
        cache_log_path=cached_stage2_log,
        experiment_log_path=experiment_log_path,
        runtime_config=baseline_stage2_config,
        max_sample_nums=resolved_config.stage2_budget,
        resolved_config=resolved_config,
    )


def _resolve_chunk_settings(candidate: RAGIterationCandidate) -> tuple[int, int]:
    chunk_size = candidate.chunk_size if candidate.chunk_size is not None else DEFAULT_RAG_CONFIG.chunk_size
    chunk_overlap = (
        candidate.chunk_overlap if candidate.chunk_overlap is not None else DEFAULT_RAG_CONFIG.chunk_overlap
    )
    return chunk_size, chunk_overlap


def _describe_candidate(candidate: RAGIterationCandidate) -> str:
    chunk_size, chunk_overlap = _resolve_chunk_settings(candidate)
    corpus_label = candidate.corpus_version or ",".join(candidate.corpus_roots or ("default",))
    query_mode = "intent" if candidate.use_intent_query else "raw"
    return (
        f"corpus={corpus_label} mode={candidate.retrieval_mode} query={query_mode} "
        f"top_k={candidate.top_k} threshold={candidate.score_threshold:.2f} "
        f"ctx={candidate.max_context_chars} chunk={chunk_size}/{chunk_overlap}"
    )


def _format_relative_gain(value: object) -> str:
    if isinstance(value, (int, float)):
        return f"{float(value):.2f}%"
    return "NA"


def _format_failure_causes(value: object) -> str:
    if not isinstance(value, Sequence) or isinstance(value, (str, bytes)):
        return "None"

    parts: list[str] = []
    for item in value:
        if not isinstance(item, dict):
            continue
        kind = item.get("kind")
        count = item.get("count")
        if isinstance(kind, str) and isinstance(count, int):
            parts.append(f"{kind}:{count}")
    return ", ".join(parts) if parts else "None"


def _format_seconds(value: float | None) -> str:
    return "NA" if value is None else f"{value:.1f}s"


def _stage_accepted(stage_result: object) -> bool:
    if not isinstance(stage_result, dict):
        return False
    acceptance = stage_result.get("acceptance")
    return isinstance(acceptance, dict) and bool(acceptance.get("accepted"))


def _best_stage1_relative_gain(attempts: Sequence[dict[str, object]]) -> float | None:
    best_gain: float | None = None
    for attempt in attempts:
        stage1 = attempt.get("stage1")
        if not isinstance(stage1, dict):
            continue
        acceptance = stage1.get("acceptance")
        if not isinstance(acceptance, dict):
            continue
        relative_gain = acceptance.get("relative_gain_pct")
        if not isinstance(relative_gain, (int, float)):
            continue
        gain_value = float(relative_gain)
        best_gain = gain_value if best_gain is None else max(best_gain, gain_value)
    return best_gain


def _estimate_remaining_seconds(
    *,
    attempts: Sequence[dict[str, object]],
    max_attempts: int,
    elapsed_seconds: float,
) -> float | None:
    if not attempts:
        return None
    remaining_attempts = max(max_attempts - len(attempts), 0)
    return (elapsed_seconds / len(attempts)) * remaining_attempts


def _serialize_exception(exception: Exception, *, stage: str) -> dict[str, str]:
    return {
        "stage": stage,
        "type": exception.__class__.__name__,
        "message": str(exception),
        "traceback": traceback.format_exc(),
    }


def _top_failure_causes(parsed_run, *, limit: int = 3) -> list[dict[str, object]]:
    counts = getattr(parsed_run, "sandbox_failure_counts", {})
    examples = getattr(parsed_run, "sandbox_failure_examples", {})
    if not isinstance(counts, dict):
        return []

    ranked_items = sorted(counts.items(), key=lambda item: (-item[1], item[0]))
    results: list[dict[str, object]] = []
    for kind, count in ranked_items[:limit]:
        entry: dict[str, object] = {"kind": kind, "count": count}
        example = examples.get(kind) if isinstance(examples, dict) else None
        if isinstance(example, str) and example:
            entry["example"] = example
        results.append(entry)
    return results


def _run_reasoning_precheck(
    *,
    base_config: config_lib.Config,
    model_spec: ModelRunSpec,
    enable_reasoning: bool,
) -> tuple[dict[str, object], ReasoningProbeSpec | None]:
    if not enable_reasoning:
        return {
            "enabled": False,
            "passed": True,
            "selected_probe": None,
            "attempts": [],
        }, None

    client = llm_client_lib.LLMClient(
        model=model_spec.model_name,
        base_url=base_config.api.base_url,
        api_key=base_config.api.api_key,
        timeout_seconds=min(base_config.api.timeout_seconds, 20),
        max_retries=0,
    )
    attempts: list[dict[str, object]] = []
    for reasoning_probe in model_spec.reasoning_probes:
        probe_payload = _serialize_reasoning_probe(reasoning_probe)
        try:
            probe_reasoning_support(client, reasoning_probe)
            attempts.append({"probe": probe_payload, "passed": True})
            return {
                "enabled": True,
                "passed": True,
                "selected_probe": probe_payload,
                "attempts": attempts,
            }, reasoning_probe
        except Exception as exception:  # pragma: no cover - exercised via tests with patched probe helper
            attempts.append(
                {
                    "probe": probe_payload,
                    "passed": False,
                    "error": _serialize_exception(exception, stage="reasoning_precheck"),
                }
            )

    return {
        "enabled": True,
        "passed": False,
        "selected_probe": None,
        "attempts": attempts,
    }, None


def _write_summary_artifacts(*, experiment_dir: Path, summary: dict[str, object]) -> None:
    _write_json(experiment_dir / "summary.json", summary)
    (experiment_dir / "final_report.md").write_text(build_final_report(summary), encoding="utf-8")


def build_stage_acceptance_config(
    iteration_config: RAGIterationConfig,
) -> AcceptanceConfig:
    return AcceptanceConfig(
        policy=ComparePolicyConfig(
            allowed_run_modes=(iteration_config.run_mode,),
            compare_budget_cap=None,
        ),
        min_valid_eval_ratio=iteration_config.acceptance_min_valid_eval_ratio,
        max_valid_eval_drop=iteration_config.acceptance_max_valid_eval_drop,
        min_relative_gain_pct=iteration_config.acceptance_min_relative_gain_pct,
    )


def build_candidate_runtime_config(
    *,
    base_config: config_lib.Config,
    candidate: RAGIterationCandidate,
    enable_rag: bool,
    iteration_config: RAGIterationConfig,
) -> config_lib.Config:
    rag_overrides = candidate.as_rag_overrides() if enable_rag else {"enable_diagnostics": False}
    return build_runtime_variant(
        enable_rag=enable_rag,
        run_mode=iteration_config.run_mode,
        base_config=base_config,
        random_seed=iteration_config.seed,
        rag_overrides=rag_overrides,
    )


def evaluate_stage_pair(
    *,
    baseline_log: Path,
    rag_log: Path,
    report_path: Path,
    target_samples: int,
    acceptance_config: AcceptanceConfig,
) -> dict[str, object]:
    baseline_log_sha256 = _sha256_of_file(baseline_log)
    rag_log_sha256 = _sha256_of_file(rag_log)
    logs_identical = baseline_log_sha256 == rag_log_sha256

    baseline = parse_run_log(baseline_log)
    rag = parse_run_log(rag_log)
    acceptance = evaluate_acceptance(
        baseline=baseline,
        rag=rag,
        target_samples=target_samples,
        acceptance_config=acceptance_config,
    )
    if logs_identical:
        warning = "Baseline and RAG logs are byte-identical; possible pipeline aliasing or deterministic collapse."
        warnings = acceptance.setdefault("warnings", [])
        if warning not in warnings:
            warnings.append(warning)
        acceptance["accepted"] = False
        acceptance["log_identity_guard"] = False
    else:
        acceptance["log_identity_guard"] = True
    report_path.write_text(
        build_pair_markdown(
            baseline_log=baseline_log,
            rag_log=rag_log,
            baseline=baseline,
            rag=rag,
            target_samples=target_samples,
            acceptance_config=acceptance_config,
        ),
        encoding="utf-8",
    )
    return {
        "baseline_log": baseline_log.as_posix(),
        "rag_log": rag_log.as_posix(),
        "baseline_log_sha256": baseline_log_sha256,
        "rag_log_sha256": rag_log_sha256,
        "logs_identical": logs_identical,
        "report": report_path.as_posix(),
        "baseline_best": baseline.best,
        "rag_best": rag.best,
        "baseline_valid_eval_ratio": baseline.valid_eval_ratio,
        "rag_valid_eval_ratio": rag.valid_eval_ratio,
        "baseline_samples": baseline.sample_lines,
        "rag_samples": rag.sample_lines,
        "retrieval_mean_confidence": rag.retrieval_mean_confidence,
        "retrieval_mean_top_score": rag.retrieval_mean_top_score,
        "retrieval_mean_top_score_gap": rag.retrieval_mean_top_score_gap,
        "retrieval_mean_injected_sources": rag.retrieval_mean_injected_sources,
        "retrieval_mean_unique_sources": rag.retrieval_mean_unique_sources,
        "retrieval_multi_source_hit_rate": rag.retrieval_multi_source_hit_rate,
        "retrieval_policy_counts": rag.retrieval_policy_counts,
        "retrieval_mean_injected_chars": rag.retrieval_mean_injected_chars,
        "retrieval_skip_ratio": rag.retrieval_skip_ratio,
        "baseline_failure_top_causes": _top_failure_causes(baseline),
        "rag_failure_top_causes": _top_failure_causes(rag),
        "acceptance": acceptance,
    }


def build_final_report(summary: dict[str, object]) -> str:
    attempts: Sequence[dict[str, object]] = summary.get("attempts", [])
    reasoning_precheck = summary.get("reasoning_precheck") if isinstance(summary.get("reasoning_precheck"), dict) else None
    lines = [
        "# Two-Stage RAG Iteration Report",
        "",
        "## Setup",
        f"- Timestamp: {summary.get('timestamp', 'NA')}",
        f"- Model: {summary.get('llm_model', 'NA')}",
        f"- Model label: {summary.get('model_label', 'NA')}",
        f"- Seed: {summary.get('seed', 'NA')}",
        f"- Stage 1 budget: {summary.get('stage1_budget', 'NA')}",
        f"- Stage 2 budget: {summary.get('stage2_budget', 'NA')}",
        f"- Relative gain threshold: {summary.get('relative_gain_threshold_pct', 'NA')}%",
        f"- Acceptance relative gain guard: {summary.get('acceptance_min_relative_gain_pct', 'NA')}%",
        f"- Acceptance valid ratio floor: {summary.get('acceptance_min_valid_eval_ratio', 'NA')}",
        f"- Acceptance valid ratio drop: {summary.get('acceptance_max_valid_eval_drop', 'NA')}",
        f"- Baseline stage 1 source: {summary.get('baseline_stage1_source', 'NA')}",
        f"- Baseline stage 2 source: {summary.get('baseline_stage2_source', 'NA')}",
        f"- Attempt count: {len(attempts)}",
        "",
        "## Attempts",
    ]

    if reasoning_precheck is not None:
        lines[9:9] = [
            f"- Reasoning precheck: {'Passed' if reasoning_precheck.get('passed') else 'Failed'}",
            f"- Reasoning probe: {reasoning_precheck.get('selected_probe', 'None')}",
        ]

    if not attempts:
        lines.append("- No attempts were executed.")
    for attempt in attempts:
        stage1 = attempt.get("stage1") if isinstance(attempt.get("stage1"), dict) else {}
        stage1_acceptance = stage1.get("acceptance", {}) if isinstance(stage1, dict) else {}
        attempt_error = attempt.get("error") if isinstance(attempt.get("error"), dict) else None
        lines.extend([
            f"### Attempt {attempt.get('attempt'):02d}: {attempt.get('candidate_name', 'unknown')}",
            f"- Phase: {attempt.get('phase', 'unknown')}",
            f"- Params: {attempt.get('candidate_summary', 'NA')}",
            f"- Status: {attempt.get('status', 'unknown')}",
            f"- Elapsed: {_format_seconds(attempt.get('elapsed_seconds') if isinstance(attempt.get('elapsed_seconds'), (int, float)) else None)}",
        ])

        if attempt_error is not None:
            lines.extend([
                f"- Failed stage: {attempt.get('failed_stage', attempt_error.get('stage', 'unknown'))}",
                f"- Error: {attempt_error.get('type', 'Error')}: {attempt_error.get('message', '')}",
                "",
            ])
            continue

        lines.extend([
            f"- Stage 1 accepted: {'Yes' if stage1_acceptance.get('accepted') else 'No'}",
            f"- Stage 1 relative gain pct: {_format_relative_gain(stage1_acceptance.get('relative_gain_pct'))}",
            f"- Stage 1 log identity guard: {'Yes' if stage1_acceptance.get('log_identity_guard', True) else 'No'}",
            f"- Stage 1 failure top causes: {_format_failure_causes(stage1.get('rag_failure_top_causes'))}",
            f"- Stage 1 report: {stage1.get('report', 'NA')}",
        ])

        stage2 = attempt.get("stage2") if isinstance(attempt.get("stage2"), dict) else None
        if stage2 and isinstance(stage2.get("error"), dict):
            stage2_error = stage2["error"]
            lines.extend([
                "- Stage 2 executed: Failed",
                f"- Stage 2 error: {stage2_error.get('type', 'Error')}: {stage2_error.get('message', '')}",
            ])
        elif stage2:
            stage2 = attempt["stage2"]
            stage2_acceptance = stage2.get("acceptance", {})
            lines.extend([
                f"- Stage 2 accepted: {'Yes' if stage2_acceptance.get('accepted') else 'No'}",
                f"- Stage 2 relative gain pct: {_format_relative_gain(stage2_acceptance.get('relative_gain_pct'))}",
                f"- Stage 2 log identity guard: {'Yes' if stage2_acceptance.get('log_identity_guard', True) else 'No'}",
                f"- Stage 2 failure top causes: {_format_failure_causes(stage2.get('rag_failure_top_causes'))}",
                f"- Stage 2 report: {stage2.get('report', 'NA')}",
            ])
        else:
            lines.append("- Stage 2 executed: No")
        lines.append("")

    fatal_error = summary.get("error") if isinstance(summary.get("error"), dict) else None
    if fatal_error is not None:
        lines.extend([
            "## Fatal Error",
            f"- Stage: {fatal_error.get('stage', 'unknown')}",
            f"- Error: {fatal_error.get('type', 'Error')}: {fatal_error.get('message', '')}",
            "",
        ])

    winner = summary.get("winner")
    lines.extend([
        "## Outcome",
        f"- Success: {'Yes' if summary.get('success') else 'No'}",
        f"- Winner: {winner if winner else 'None'}",
        f"- Adaptive search enabled: {'Yes' if summary.get('adaptive_search') else 'No'}",
        f"- Stop reason: {summary.get('stop_reason', 'NA')}",
    ])
    return "\n".join(lines) + "\n"


def _rank_attempt_record(attempt_record: dict[str, object]) -> tuple[float, float, float, float, float]:
    stage1 = attempt_record.get("stage1", {})
    acceptance = stage1.get("acceptance", {})
    relative_gain = acceptance.get("relative_gain_pct")
    valid_eval_ratio = stage1.get("rag_valid_eval_ratio")
    injected_chars = stage1.get("retrieval_mean_injected_chars")
    retrieval_confidence = stage1.get("retrieval_mean_confidence")
    return (
        1.0 if acceptance.get("accepted") else 0.0,
        float(relative_gain) if isinstance(relative_gain, (int, float)) else float("-inf"),
        float(valid_eval_ratio) if isinstance(valid_eval_ratio, (int, float)) else float("-inf"),
        -(float(injected_chars)) if isinstance(injected_chars, (int, float)) else float("-inf"),
        float(retrieval_confidence) if isinstance(retrieval_confidence, (int, float)) else float("-inf"),
    )


def _select_best_candidate(attempt_records: Sequence[tuple[RAGIterationCandidate, dict[str, object]]]) -> RAGIterationCandidate:
    return max(attempt_records, key=lambda item: _rank_attempt_record(item[1]))[0]


def _execute_candidate_attempt(
    *,
    attempt_index: int,
    candidate: RAGIterationCandidate,
    phase: str,
    base_config: config_lib.Config,
    resolved_config: RAGIterationConfig,
    acceptance_config: AcceptanceConfig,
    experiment_dir: Path,
    baseline_stage1_log: Path,
    ensure_stage2_baseline_log: Callable[[], Path],
) -> dict[str, object]:
    attempt_dir = experiment_dir / f"attempt_{attempt_index:02d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)
    attempt_path = experiment_dir / f"attempt_{attempt_index:02d}.json"
    attempt_started_at = time.perf_counter()

    rag_stage1_log = attempt_dir / "rag_stage1.log"
    rag_stage1_report = attempt_dir / "stage1_report.md"
    rag_stage1_config = build_candidate_runtime_config(
        base_config=base_config,
        candidate=candidate,
        enable_rag=True,
        iteration_config=resolved_config,
    )
    attempt_record: dict[str, object] = {
        "attempt": attempt_index,
        "phase": phase,
        "candidate_name": candidate.name,
        "candidate_summary": _describe_candidate(candidate),
        "candidate": asdict(candidate),
    }
    current_stage = "stage1"

    print(
        f"[ATTEMPT {attempt_index:02d}/{resolved_config.max_attempts}] start | "
        f"phase={phase} | candidate={candidate.name}"
    )
    print(f"[ATTEMPT {attempt_index:02d}] params | {attempt_record['candidate_summary']}")

    try:
        run_logged_experiment(
            label=f"ATTEMPT_{attempt_index:02d}_RAG_STAGE1",
            runtime_config=rag_stage1_config,
            log_path=rag_stage1_log,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=resolved_config.stage1_budget,
            log_dir=resolved_config.log_dir,
            header_fields={
                "RUN_MODE": resolved_config.run_mode,
                "RUN_BUDGET": resolved_config.stage1_budget,
                "SEARCH_PHASE": phase,
            },
        )
        stage1 = evaluate_stage_pair(
            baseline_log=baseline_stage1_log,
            rag_log=rag_stage1_log,
            report_path=rag_stage1_report,
            target_samples=resolved_config.stage1_budget,
            acceptance_config=acceptance_config,
        )
        attempt_record["stage1"] = stage1
        print(
            f"[ATTEMPT {attempt_index:02d}] stage1 | "
            f"accepted={'yes' if _stage_accepted(stage1) else 'no'} | "
            f"relative_gain={_format_relative_gain(stage1['acceptance'].get('relative_gain_pct'))} | "
            f"valid_ratio={stage1.get('rag_valid_eval_ratio', 'NA')} | "
            f"failures={_format_failure_causes(stage1.get('rag_failure_top_causes'))}"
        )

        if not _stage_accepted(stage1):
            attempt_record["stage2"] = None
            attempt_record["status"] = "stage1_rejected"
            return attempt_record

        current_stage = "stage2"
        rag_stage2_log = attempt_dir / "rag_stage2.log"
        rag_stage2_report = attempt_dir / "stage2_report.md"
        baseline_stage2_log = ensure_stage2_baseline_log()
        run_logged_experiment(
            label=f"ATTEMPT_{attempt_index:02d}_RAG_STAGE2",
            runtime_config=rag_stage1_config,
            log_path=rag_stage2_log,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=resolved_config.stage2_budget,
            log_dir=resolved_config.log_dir,
            header_fields={
                "RUN_MODE": resolved_config.run_mode,
                "RUN_BUDGET": resolved_config.stage2_budget,
                "SEARCH_PHASE": phase,
            },
        )
        stage2 = evaluate_stage_pair(
            baseline_log=baseline_stage2_log,
            rag_log=rag_stage2_log,
            report_path=rag_stage2_report,
            target_samples=resolved_config.stage2_budget,
            acceptance_config=acceptance_config,
        )
        attempt_record["stage2"] = stage2
        attempt_record["status"] = "stage2_accepted" if _stage_accepted(stage2) else "stage2_rejected"
        print(
            f"[ATTEMPT {attempt_index:02d}] stage2 | "
            f"accepted={'yes' if _stage_accepted(stage2) else 'no'} | "
            f"relative_gain={_format_relative_gain(stage2['acceptance'].get('relative_gain_pct'))} | "
            f"failures={_format_failure_causes(stage2.get('rag_failure_top_causes'))}"
        )
    except Exception as exception:
        error = _serialize_exception(exception, stage=current_stage)
        attempt_record["status"] = "failed"
        attempt_record["failed_stage"] = current_stage
        attempt_record["error"] = error
        if current_stage == "stage1":
            attempt_record["stage1"] = {"status": "failed", "error": error}
            attempt_record["stage2"] = None
        else:
            attempt_record["stage2"] = {"status": "failed", "error": error}
        print(
            f"[ATTEMPT {attempt_index:02d}] failed | "
            f"stage={current_stage} | type={error['type']} | message={error['message']}"
        )
    finally:
        attempt_record["elapsed_seconds"] = round(time.perf_counter() - attempt_started_at, 3)
        _write_json(attempt_path, attempt_record)
    return attempt_record


def _run_candidate_batch(
    *,
    candidates: Sequence[RAGIterationCandidate],
    phase: str,
    start_attempt_index: int,
    max_attempts: int,
    attempts: list[dict[str, object]],
    base_config: config_lib.Config,
    resolved_config: RAGIterationConfig,
    acceptance_config: AcceptanceConfig,
    experiment_dir: Path,
    baseline_stage1_log: Path,
    ensure_stage2_baseline_log: Callable[[], Path],
    iteration_started_at: float,
) -> tuple[list[tuple[RAGIterationCandidate, dict[str, object]]], str | None, str | None, int]:
    phase_results: list[tuple[RAGIterationCandidate, dict[str, object]]] = []
    next_attempt_index = start_attempt_index
    winner: str | None = None
    stop_reason: str | None = None

    for candidate in candidates:
        if next_attempt_index > max_attempts:
            stop_reason = "max_attempts_reached"
            break
        attempt_record = _execute_candidate_attempt(
            attempt_index=next_attempt_index,
            candidate=candidate,
            phase=phase,
            base_config=base_config,
            resolved_config=resolved_config,
            acceptance_config=acceptance_config,
            experiment_dir=experiment_dir,
            baseline_stage1_log=baseline_stage1_log,
            ensure_stage2_baseline_log=ensure_stage2_baseline_log,
        )
        attempts.append(attempt_record)
        phase_results.append((candidate, attempt_record))
        elapsed_seconds = time.perf_counter() - iteration_started_at
        estimated_remaining_seconds = _estimate_remaining_seconds(
            attempts=attempts,
            max_attempts=max_attempts,
            elapsed_seconds=elapsed_seconds,
        )
        print(
            f"[ITERATION_PROGRESS] attempts={len(attempts)}/{max_attempts} | "
            f"best_stage1_gain={_format_relative_gain(_best_stage1_relative_gain(attempts))} | "
            f"elapsed={_format_seconds(elapsed_seconds)} | "
            f"est_remaining={_format_seconds(estimated_remaining_seconds)}"
        )
        if _stage_accepted(attempt_record.get("stage2")):
            winner = candidate.name
            stop_reason = f"attempt_{next_attempt_index:02d}_passed_stage2"
            break
        next_attempt_index += 1

    return phase_results, winner, stop_reason, next_attempt_index


def run_iteration(
    iteration_config: RAGIterationConfig | None = None,
    candidate_space: Sequence[RAGIterationCandidate] | None = None,
    model_spec: ModelRunSpec | None = None,
    timestamp: str | None = None,
) -> dict[str, object]:
    resolved_config = iteration_config or SCRIPT_CONFIG
    resolved_model_spec = model_spec or resolved_config.model_specs[0]
    acceptance_config = build_stage_acceptance_config(resolved_config)
    explicit_candidate_space = tuple(candidate_space) if candidate_space is not None else None
    iteration_started_at = time.perf_counter()

    resolved_timestamp = timestamp or make_timestamp()
    experiment_dir = Path(resolved_config.results_dir) / _build_experiment_dir_name(
        resolved_timestamp,
        resolved_model_spec,
    )
    experiment_dir.mkdir(parents=True, exist_ok=True)
    results_dir = Path(resolved_config.results_dir)

    base_config = build_runtime_config()
    base_config = dataclasses.replace(
        base_config,
        random_seed=resolved_config.seed,
        llm_model=resolved_model_spec.model_name,
    )
    reasoning_precheck, selected_reasoning_probe = _run_reasoning_precheck(
        base_config=base_config,
        model_spec=resolved_model_spec,
        enable_reasoning=resolved_config.enable_thinking,
    )

    baseline_stage1_log, baseline_stage2_log = _build_baseline_log_paths(experiment_dir)
    attempts: list[dict[str, object]] = []

    summary: dict[str, object] = {
        "timestamp": resolved_timestamp,
        "experiment_dir": experiment_dir.as_posix(),
        "llm_model": resolved_model_spec.model_name,
        "model_label": resolved_model_spec.result_label,
        "reasoning_precheck": reasoning_precheck,
        "seed": resolved_config.seed,
        "run_mode": resolved_config.run_mode,
        "stage1_budget": resolved_config.stage1_budget,
        "stage2_budget": resolved_config.stage2_budget,
        "relative_gain_threshold_pct": resolved_config.relative_gain_threshold_pct,
        "acceptance_min_relative_gain_pct": acceptance_config.min_relative_gain_pct,
        "acceptance_min_valid_eval_ratio": acceptance_config.min_valid_eval_ratio,
        "acceptance_max_valid_eval_drop": acceptance_config.max_valid_eval_drop,
        "max_attempts": resolved_config.max_attempts,
        "adaptive_search": explicit_candidate_space is None,
        "success": False,
        "winner": None,
        "stop_reason": "not_started",
        "baseline_stage1_log": baseline_stage1_log.as_posix(),
        "baseline_stage2_log": baseline_stage2_log.as_posix(),
        "baseline_stage1_source": "pending",
        "baseline_stage2_source": "pending",
        "attempts": attempts,
    }

    baseline_stage1_config = build_candidate_runtime_config(
        base_config=base_config,
        candidate=RAGIterationCandidate(
            name="baseline_control",
            corpus_version=resolved_config.control_corpus_version,
            retrieval_mode=base_config.rag.retrieval_mode,
            use_intent_query=base_config.rag.use_intent_query,
            top_k=base_config.rag.top_k,
            score_threshold=base_config.rag.score_threshold,
            max_context_chars=base_config.rag.max_context_chars,
        ),
        enable_rag=False,
        iteration_config=resolved_config,
    )
    baseline_stage2_config = baseline_stage1_config

    print(
        f"[ITERATION] start | timestamp={resolved_timestamp} | model={resolved_model_spec.model_name} | "
        f"stage1={resolved_config.stage1_budget} | "
        f"stage2={resolved_config.stage2_budget} | threshold={resolved_config.relative_gain_threshold_pct:.2f}% | "
        f"max_attempts={resolved_config.max_attempts}"
    )

    if resolved_config.enable_thinking and not reasoning_precheck.get("passed"):
        summary["stop_reason"] = "reasoning_precheck_failed"
        _write_summary_artifacts(experiment_dir=experiment_dir, summary=summary)
        print(
            f"[ITERATION] blocked | model={resolved_model_spec.model_name} | "
            f"reasoning_precheck={reasoning_precheck}"
        )
        return summary

    current_stage = "baseline_stage1"
    try:
        with patched_iteration_runtime(
            enable_thinking=resolved_config.enable_thinking,
            zero_context_means_unlimited=True,
            reasoning_probe=selected_reasoning_probe,
        ):
            baseline_stage1_log, baseline_stage2_log, baseline_sources = _prepare_baseline_logs(
                experiment_dir=experiment_dir,
                results_dir=results_dir,
                baseline_stage1_config=baseline_stage1_config,
                baseline_stage2_config=baseline_stage2_config,
                resolved_config=resolved_config,
                resolved_model_spec=resolved_model_spec,
                selected_reasoning_probe=selected_reasoning_probe,
            )
            summary["baseline_stage1_source"] = baseline_sources["stage1"]
            summary["baseline_stage2_source"] = baseline_sources["stage2"]

            def ensure_stage2_baseline_log() -> Path:
                if summary["baseline_stage2_source"] == "pending":
                    summary["baseline_stage2_source"] = _ensure_stage2_baseline_log(
                        experiment_log_path=baseline_stage2_log,
                        results_dir=results_dir,
                        baseline_stage2_config=baseline_stage2_config,
                        resolved_config=resolved_config,
                        resolved_model_spec=resolved_model_spec,
                        selected_reasoning_probe=selected_reasoning_probe,
                    )
                return baseline_stage2_log

            current_stage = "candidate_search"

            winner: str | None = None
            stop_reason = "candidate_space_exhausted"

            if explicit_candidate_space is not None:
                _, winner, batch_stop_reason, _ = _run_candidate_batch(
                    candidates=explicit_candidate_space,
                    phase="explicit",
                    start_attempt_index=1,
                    max_attempts=resolved_config.max_attempts,
                    attempts=attempts,
                    base_config=base_config,
                    resolved_config=resolved_config,
                    acceptance_config=acceptance_config,
                    experiment_dir=experiment_dir,
                    baseline_stage1_log=baseline_stage1_log,
                    ensure_stage2_baseline_log=ensure_stage2_baseline_log,
                    iteration_started_at=iteration_started_at,
                )
                if batch_stop_reason is not None:
                    stop_reason = batch_stop_reason
                if winner is None and len(attempts) >= resolved_config.max_attempts:
                    stop_reason = "max_attempts_reached"
            else:
                print("[ADAPTIVE_SEARCH] phase=query_alignment")
                query_results, winner, batch_stop_reason, next_attempt_index = _run_candidate_batch(
                    candidates=build_query_phase_candidates(resolved_config),
                    phase="query_alignment",
                    start_attempt_index=1,
                    max_attempts=resolved_config.max_attempts,
                    attempts=attempts,
                    base_config=base_config,
                    resolved_config=resolved_config,
                    acceptance_config=acceptance_config,
                    experiment_dir=experiment_dir,
                    baseline_stage1_log=baseline_stage1_log,
                    ensure_stage2_baseline_log=ensure_stage2_baseline_log,
                    iteration_started_at=iteration_started_at,
                )
                if batch_stop_reason is not None:
                    stop_reason = batch_stop_reason
                if winner is None and query_results and next_attempt_index <= resolved_config.max_attempts:
                    best_query_candidate = _select_best_candidate(query_results)
                    print(f"[ADAPTIVE_SEARCH] best_query_candidate={best_query_candidate.name}")
                    density_candidates = build_density_phase_candidates(best_query_candidate)
                    print("[ADAPTIVE_SEARCH] phase=density_refinement")
                    density_results, winner, batch_stop_reason, next_attempt_index = _run_candidate_batch(
                        candidates=density_candidates,
                        phase="density_refinement",
                        start_attempt_index=next_attempt_index,
                        max_attempts=resolved_config.max_attempts,
                        attempts=attempts,
                        base_config=base_config,
                        resolved_config=resolved_config,
                        acceptance_config=acceptance_config,
                        experiment_dir=experiment_dir,
                        baseline_stage1_log=baseline_stage1_log,
                        ensure_stage2_baseline_log=ensure_stage2_baseline_log,
                        iteration_started_at=iteration_started_at,
                    )
                    if batch_stop_reason is not None:
                        stop_reason = batch_stop_reason

                if winner is None and len(attempts) >= resolved_config.max_attempts:
                    stop_reason = "max_attempts_reached"

        summary["success"] = winner is not None
        summary["winner"] = winner
        summary["stop_reason"] = stop_reason
    except Exception as exception:
        error = _serialize_exception(exception, stage=current_stage)
        summary["error"] = error
        summary["stop_reason"] = f"{current_stage}_failed"
        _write_summary_artifacts(experiment_dir=experiment_dir, summary=summary)
        print(
            f"[ITERATION] failed | stage={current_stage} | "
            f"type={error['type']} | message={error['message']}"
        )
        print(f"[ITERATION] failure summary={ (experiment_dir / 'summary.json').as_posix() }")
        raise

    _write_summary_artifacts(experiment_dir=experiment_dir, summary=summary)
    print(f"[ITERATION] summary={ (experiment_dir / 'summary.json').as_posix() }")
    return summary


def run_all_model_iterations(
    iteration_config: RAGIterationConfig | None = None,
    candidate_space: Sequence[RAGIterationCandidate] | None = None,
) -> dict[str, object]:
    resolved_config = iteration_config or SCRIPT_CONFIG
    suite_timestamp = make_timestamp()
    model_runs: list[dict[str, object]] = []

    for index, model_spec in enumerate(resolved_config.model_specs, start=1):
        print(
            f"[MODEL_RUN {index}/{len(resolved_config.model_specs)}] start | "
            f"model={model_spec.model_name} | label={model_spec.result_label}"
        )
        summary = run_iteration(
            iteration_config=resolved_config,
            candidate_space=candidate_space,
            model_spec=model_spec,
            timestamp=suite_timestamp,
        )
        model_runs.append(
            {
                "model_name": model_spec.model_name,
                "result_label": model_spec.result_label,
                "experiment_dir": summary.get("experiment_dir"),
                "summary_path": str(Path(summary["experiment_dir"]) / "summary.json"),
                "success": summary.get("success"),
                "winner": summary.get("winner"),
                "stop_reason": summary.get("stop_reason"),
                "reasoning_precheck": summary.get("reasoning_precheck"),
            }
        )

    suite_summary = {
        "timestamp": suite_timestamp,
        "results_dir": resolved_config.results_dir,
        "model_runs": model_runs,
    }
    _write_json(Path(resolved_config.results_dir) / f"{suite_timestamp}_suite_summary.json", suite_summary)
    return suite_summary


def main() -> int:
    try:
        summary = run_all_model_iterations()
    except Exception:
        return 1
    print(f"Iteration suite summary written for {summary['timestamp']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
