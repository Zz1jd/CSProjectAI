#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
from dataclasses import asdict
import json
from pathlib import Path
import sys
from typing import Sequence


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import build_runtime_config
from implementation import config as config_lib
from scripts._runner import build_runtime_variant
from scripts._runner import make_timestamp
from scripts._runner import run_logged_experiment
from scripts.compare_rag import AcceptanceConfig
from scripts.compare_rag import ComparePolicyConfig
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import evaluate_acceptance
from scripts.compare_rag import parse_run_log
from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig
from scripts.experiments.space import build_density_phase_candidates
from scripts.experiments.space import build_primary_candidate_space
from scripts.experiments.space import build_query_phase_candidates
from scripts.experiments.space import build_source_phase_candidates


SCRIPT_CONFIG = RAGIterationConfig()
RUNTIME_DEFAULTS = config_lib.RuntimeDefaults()


def build_stage_acceptance_config(
    iteration_config: RAGIterationConfig,
) -> AcceptanceConfig:
    return AcceptanceConfig(
        policy=ComparePolicyConfig(
            allowed_run_modes=(iteration_config.run_mode,),
            compare_budget_cap=None,
        ),
        min_relative_gain_pct=iteration_config.relative_gain_threshold_pct,
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
    baseline = parse_run_log(baseline_log)
    rag = parse_run_log(rag_log)
    acceptance = evaluate_acceptance(
        baseline=baseline,
        rag=rag,
        target_samples=target_samples,
        acceptance_config=acceptance_config,
    )
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
        "retrieval_mean_unique_sources": rag.retrieval_mean_unique_sources,
        "retrieval_mean_injected_chars": rag.retrieval_mean_injected_chars,
        "retrieval_skip_ratio": rag.retrieval_skip_ratio,
        "acceptance": acceptance,
    }


def build_final_report(summary: dict[str, object]) -> str:
    attempts: Sequence[dict[str, object]] = summary.get("attempts", [])
    lines = [
        "# Two-Stage RAG Iteration Report",
        "",
        "## Setup",
        f"- Timestamp: {summary.get('timestamp', 'NA')}",
        f"- Seed: {summary.get('seed', 'NA')}",
        f"- Stage 1 budget: {summary.get('stage1_budget', 'NA')}",
        f"- Stage 2 budget: {summary.get('stage2_budget', 'NA')}",
        f"- Relative gain threshold: {summary.get('relative_gain_threshold_pct', 'NA')}%",
        f"- Attempt count: {len(attempts)}",
        "",
        "## Attempts",
    ]

    if not attempts:
        lines.append("- No attempts were executed.")
    for attempt in attempts:
        stage1 = attempt.get("stage1", {})
        stage1_acceptance = stage1.get("acceptance", {})
        lines.extend([
            f"### Attempt {attempt.get('attempt'):02d}: {attempt.get('candidate_name', 'unknown')}",
            f"- Phase: {attempt.get('phase', 'unknown')}",
            f"- Stage 1 accepted: {'Yes' if stage1_acceptance.get('accepted') else 'No'}",
            f"- Stage 1 relative gain pct: {stage1_acceptance.get('relative_gain_pct', 'NA')}",
            f"- Stage 1 report: {stage1.get('report', 'NA')}",
        ])

        if attempt.get("stage2"):
            stage2 = attempt["stage2"]
            stage2_acceptance = stage2.get("acceptance", {})
            lines.extend([
                f"- Stage 2 accepted: {'Yes' if stage2_acceptance.get('accepted') else 'No'}",
                f"- Stage 2 relative gain pct: {stage2_acceptance.get('relative_gain_pct', 'NA')}",
                f"- Stage 2 report: {stage2.get('report', 'NA')}",
            ])
        else:
            lines.append("- Stage 2 executed: No")
        lines.append("")

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
    baseline_stage2_log: Path,
) -> dict[str, object]:
    attempt_dir = experiment_dir / f"attempt_{attempt_index:02d}"
    attempt_dir.mkdir(parents=True, exist_ok=True)

    rag_stage1_log = attempt_dir / "rag_stage1.log"
    rag_stage1_report = attempt_dir / "stage1_report.md"
    rag_stage1_config = build_candidate_runtime_config(
        base_config=base_config,
        candidate=candidate,
        enable_rag=True,
        iteration_config=resolved_config,
    )
    run_logged_experiment(
        label=f"ATTEMPT_{attempt_index:02d}_RAG_STAGE1",
        runtime_config=rag_stage1_config,
        log_path=rag_stage1_log,
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=resolved_config.stage1_budget,
        log_dir=resolved_config.log_dir,
        header_fields={"RUN_MODE": resolved_config.run_mode, "RUN_BUDGET": resolved_config.stage1_budget, "SEARCH_PHASE": phase},
    )
    stage1 = evaluate_stage_pair(
        baseline_log=baseline_stage1_log,
        rag_log=rag_stage1_log,
        report_path=rag_stage1_report,
        target_samples=resolved_config.stage1_budget,
        acceptance_config=acceptance_config,
    )

    attempt_record: dict[str, object] = {
        "attempt": attempt_index,
        "phase": phase,
        "candidate_name": candidate.name,
        "candidate": asdict(candidate),
        "stage1": stage1,
    }

    if stage1["acceptance"]["accepted"]:
        rag_stage2_log = attempt_dir / "rag_stage2.log"
        rag_stage2_report = attempt_dir / "stage2_report.md"
        run_logged_experiment(
            label=f"ATTEMPT_{attempt_index:02d}_RAG_STAGE2",
            runtime_config=rag_stage1_config,
            log_path=rag_stage2_log,
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=resolved_config.stage2_budget,
            log_dir=resolved_config.log_dir,
            header_fields={"RUN_MODE": resolved_config.run_mode, "RUN_BUDGET": resolved_config.stage2_budget, "SEARCH_PHASE": phase},
        )
        attempt_record["stage2"] = evaluate_stage_pair(
            baseline_log=baseline_stage2_log,
            rag_log=rag_stage2_log,
            report_path=rag_stage2_report,
            target_samples=resolved_config.stage2_budget,
            acceptance_config=acceptance_config,
        )
    else:
        attempt_record["stage2"] = None

    attempt_path = experiment_dir / f"attempt_{attempt_index:02d}.json"
    attempt_path.write_text(json.dumps(attempt_record, ensure_ascii=False, indent=2), encoding="utf-8")
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
    baseline_stage2_log: Path,
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
            baseline_stage2_log=baseline_stage2_log,
        )
        attempts.append(attempt_record)
        phase_results.append((candidate, attempt_record))
        if attempt_record.get("stage2") and attempt_record["stage2"]["acceptance"]["accepted"]:
            winner = candidate.name
            stop_reason = f"attempt_{next_attempt_index:02d}_passed_stage2"
            break
        next_attempt_index += 1

    return phase_results, winner, stop_reason, next_attempt_index


def run_iteration(
    iteration_config: RAGIterationConfig | None = None,
    candidate_space: Sequence[RAGIterationCandidate] | None = None,
) -> dict[str, object]:
    resolved_config = iteration_config or SCRIPT_CONFIG
    acceptance_config = build_stage_acceptance_config(resolved_config)
    explicit_candidate_space = tuple(candidate_space) if candidate_space is not None else None

    timestamp = make_timestamp()
    experiment_dir = Path(resolved_config.results_dir) / timestamp
    experiment_dir.mkdir(parents=True, exist_ok=True)

    base_config = build_runtime_config()
    base_config = dataclasses.replace(base_config, random_seed=resolved_config.seed)

    baseline_stage1_log = experiment_dir / "baseline_stage1.log"
    baseline_stage2_log = experiment_dir / "baseline_stage2.log"

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

    run_logged_experiment(
        label="BASELINE_STAGE1",
        runtime_config=baseline_stage1_config,
        log_path=baseline_stage1_log,
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=resolved_config.stage1_budget,
        log_dir=resolved_config.log_dir,
        header_fields={"RUN_MODE": resolved_config.run_mode, "RUN_BUDGET": resolved_config.stage1_budget},
    )
    run_logged_experiment(
        label="BASELINE_STAGE2",
        runtime_config=baseline_stage2_config,
        log_path=baseline_stage2_log,
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=resolved_config.stage2_budget,
        log_dir=resolved_config.log_dir,
        header_fields={"RUN_MODE": resolved_config.run_mode, "RUN_BUDGET": resolved_config.stage2_budget},
    )

    attempts: list[dict[str, object]] = []
    winner: str | None = None
    stop_reason = "candidate_space_exhausted"

    if explicit_candidate_space is not None:
        _, winner, stop_reason, _ = _run_candidate_batch(
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
            baseline_stage2_log=baseline_stage2_log,
        )
        if winner is None and len(attempts) >= resolved_config.max_attempts:
            stop_reason = "max_attempts_reached"
    else:
        print("[ADAPTIVE_SEARCH] phase=query_alignment")
        query_results, winner, stop_reason, next_attempt_index = _run_candidate_batch(
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
            baseline_stage2_log=baseline_stage2_log,
        )
        if winner is None and query_results and next_attempt_index <= resolved_config.max_attempts:
            best_query_candidate = _select_best_candidate(query_results)
            print(f"[ADAPTIVE_SEARCH] best_query_candidate={best_query_candidate.name}")
            density_candidates = build_density_phase_candidates(best_query_candidate)
            print("[ADAPTIVE_SEARCH] phase=density_refinement")
            density_results, winner, stop_reason, next_attempt_index = _run_candidate_batch(
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
                baseline_stage2_log=baseline_stage2_log,
            )
            if winner is None and next_attempt_index <= resolved_config.max_attempts:
                best_control_candidate = _select_best_candidate(query_results + density_results)
                print(f"[ADAPTIVE_SEARCH] best_control_candidate={best_control_candidate.name}")
                source_candidates = build_source_phase_candidates(resolved_config, best_control_candidate)
                print("[ADAPTIVE_SEARCH] phase=source_variants")
                _, winner, stop_reason, next_attempt_index = _run_candidate_batch(
                    candidates=source_candidates,
                    phase="source_variants",
                    start_attempt_index=next_attempt_index,
                    max_attempts=resolved_config.max_attempts,
                    attempts=attempts,
                    base_config=base_config,
                    resolved_config=resolved_config,
                    acceptance_config=acceptance_config,
                    experiment_dir=experiment_dir,
                    baseline_stage1_log=baseline_stage1_log,
                    baseline_stage2_log=baseline_stage2_log,
                )

        if winner is None and len(attempts) >= resolved_config.max_attempts:
            stop_reason = "max_attempts_reached"

    summary = {
        "timestamp": timestamp,
        "seed": resolved_config.seed,
        "run_mode": resolved_config.run_mode,
        "stage1_budget": resolved_config.stage1_budget,
        "stage2_budget": resolved_config.stage2_budget,
        "relative_gain_threshold_pct": resolved_config.relative_gain_threshold_pct,
        "max_attempts": resolved_config.max_attempts,
        "adaptive_search": explicit_candidate_space is None,
        "success": winner is not None,
        "winner": winner,
        "stop_reason": stop_reason,
        "baseline_stage1_log": baseline_stage1_log.as_posix(),
        "baseline_stage2_log": baseline_stage2_log.as_posix(),
        "attempts": attempts,
    }
    summary_path = experiment_dir / "summary.json"
    summary_path.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    final_report_path = experiment_dir / "final_report.md"
    final_report_path.write_text(build_final_report(summary), encoding="utf-8")
    return summary


def main() -> int:
    summary = run_iteration()
    print(f"Iteration summary written for {summary['timestamp']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
