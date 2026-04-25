#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import sys
from typing import Any

from scripts.compare_rag import ParsedRun
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import parse_run_log


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RUN_LOG_SUFFIX = ".txt"
DEFAULT_RESULTS_DIR = "results/experiments_repro_20260420_133019"
DEFAULT_LOG_DIR = "../logs/funsearch_rag_compare_repro_20260420_133019"


@dataclasses.dataclass(frozen=True)
class ModelSpec:
    model_name: str
    result_label: str


@dataclasses.dataclass(frozen=True)
class CompareCandidate:
    name: str
    retrieval_mode: str
    use_intent_query: bool
    top_k: int
    score_threshold: float
    max_context_chars: int
    corpus_version: str | None = None
    corpus_roots: tuple[str, ...] | None = None
    chunk_size: int | None = None
    chunk_overlap: int | None = None

    def resolve_corpus_roots(self) -> tuple[str, ...] | None:
        if self.corpus_roots is not None:
            return self.corpus_roots
        if self.corpus_version is None:
            return None
        return (_build_governed_corpus_root(self.corpus_version),)

    def as_rag_overrides(self) -> dict[str, object]:
        overrides: dict[str, object] = {
            "retrieval_mode": self.retrieval_mode,
            "use_intent_query": self.use_intent_query,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "max_context_chars": self.max_context_chars,
            "enable_diagnostics": True,
        }
        if self.corpus_version is not None:
            overrides["corpus_version"] = self.corpus_version
        corpus_roots = self.resolve_corpus_roots()
        if corpus_roots is not None:
            overrides["corpus_roots"] = corpus_roots
        if self.chunk_size is not None:
            overrides["chunk_size"] = self.chunk_size
        if self.chunk_overlap is not None:
            overrides["chunk_overlap"] = self.chunk_overlap
        return overrides


@dataclasses.dataclass(frozen=True)
class CompareRunConfig:
    seed: int = 42
    run_mode: str = "stage_eval"
    budget: int = 100
    results_dir: str = DEFAULT_RESULTS_DIR
    log_dir: str = DEFAULT_LOG_DIR


def build_default_compare_config() -> CompareRunConfig:
    return CompareRunConfig()


def build_smoke_compare_config(budget: int = 2) -> CompareRunConfig:
    return dataclasses.replace(build_default_compare_config(), budget=budget)


def build_repro_candidate_space() -> tuple[CompareCandidate, ...]:
    return (
        CompareCandidate(
            name="smoke_v32_dynamic_history",
            corpus_version="v3.2.0_dynamic_history",
            retrieval_mode="hybrid",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
            chunk_size=1200,
            chunk_overlap=200,
        ),
        CompareCandidate(
            name="smoke_v33_full_corpus",
            corpus_version="v3.3.0_full_corpus",
            retrieval_mode="hybrid",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
            chunk_size=1200,
            chunk_overlap=200,
        ),
    )


def build_repro_model_spec() -> ModelSpec:
    return ModelSpec(
        model_name="gpt-3.5-turbo",
        result_label="repro_gpt_3_5_turbo_20260420",
    )


def _build_governed_corpus_root(corpus_version: str) -> str:
    from implementation import config as config_lib

    return config_lib.build_governed_corpus_root(corpus_version)


def _load_runtime_bindings() -> tuple[Any, Any, Any, Any, Any]:
    from main import RUNTIME_DEFAULTS
    from main import build_runtime_config
    from scripts._runner import build_runtime_variant
    from scripts._runner import make_timestamp
    from scripts._runner import run_logged_experiment

    return RUNTIME_DEFAULTS, build_runtime_config, build_runtime_variant, make_timestamp, run_logged_experiment


def _resolve_results_dir(results_dir: str) -> Path:
    configured = Path(results_dir)
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def _parsed_run_summary(run: ParsedRun, log_path: Path) -> dict[str, object]:
    return {
        "log_path": str(log_path.as_posix()),
        "best": run.best,
        "sample_lines": run.sample_lines,
        "valid_eval_ratio": run.valid_eval_ratio,
        "evals_per_sample": run.evals_per_sample,
        "retrieval_events": run.retrieval_events,
        "retrieval_mean_top_score": run.retrieval_mean_top_score,
        "retrieval_mean_top_score_gap": run.retrieval_mean_top_score_gap,
        "retrieval_mean_confidence": run.retrieval_mean_confidence,
        "retrieval_mean_injected_chars": run.retrieval_mean_injected_chars,
        "retrieval_mean_injected_sources": run.retrieval_mean_injected_sources,
        "retrieval_mean_unique_sources": run.retrieval_mean_unique_sources,
        "retrieval_multi_source_hit_rate": run.retrieval_multi_source_hit_rate,
        "retrieval_policy_counts": run.retrieval_policy_counts,
        "retrieval_skip_ratio": run.retrieval_skip_ratio,
    }


def _run_baseline(
    *,
    experiment_dir: Path,
    compare_config: CompareRunConfig,
    model_spec: ModelSpec,
) -> tuple[Path, ParsedRun]:
    runtime_defaults, build_runtime_config, build_runtime_variant, _, run_logged_experiment = _load_runtime_bindings()
    base_config = dataclasses.replace(
        build_runtime_config(),
        llm_model=model_spec.model_name,
        random_seed=compare_config.seed,
    )
    baseline_log = experiment_dir / f"baseline{RUN_LOG_SUFFIX}"
    baseline_config = build_runtime_variant(
        enable_rag=False,
        run_mode=compare_config.run_mode,
        base_config=base_config,
        random_seed=compare_config.seed,
        model_track="baseline",
    )
    run_logged_experiment(
        label="BASELINE",
        runtime_config=baseline_config,
        log_path=baseline_log,
        dataset_path=runtime_defaults.dataset_path,
        max_sample_nums=compare_config.budget,
        log_dir=compare_config.log_dir,
        header_fields={"RUN_MODE": compare_config.run_mode, "RUN_BUDGET": compare_config.budget},
    )
    return baseline_log, parse_run_log(baseline_log)


def _run_rag_candidate(
    *,
    experiment_dir: Path,
    compare_config: CompareRunConfig,
    candidate: CompareCandidate,
    model_spec: ModelSpec,
) -> tuple[Path, ParsedRun]:
    runtime_defaults, build_runtime_config, build_runtime_variant, _, run_logged_experiment = _load_runtime_bindings()
    base_config = dataclasses.replace(
        build_runtime_config(),
        llm_model=model_spec.model_name,
        random_seed=compare_config.seed,
    )
    rag_log = experiment_dir / f"rag_{candidate.name}{RUN_LOG_SUFFIX}"
    rag_config = build_runtime_variant(
        enable_rag=True,
        run_mode=compare_config.run_mode,
        base_config=base_config,
        random_seed=compare_config.seed,
        model_track="rag",
        rag_overrides=candidate.as_rag_overrides(),
    )
    run_logged_experiment(
        label=f"RAG_{candidate.name}",
        runtime_config=rag_config,
        log_path=rag_log,
        dataset_path=runtime_defaults.dataset_path,
        max_sample_nums=compare_config.budget,
        log_dir=compare_config.log_dir,
        header_fields={
            "RUN_MODE": compare_config.run_mode,
            "RUN_BUDGET": compare_config.budget,
            "RAG_CANDIDATE": candidate.name,
        },
    )
    return rag_log, parse_run_log(rag_log)


def _build_suite_markdown(
    *,
    baseline_log: Path,
    baseline: ParsedRun,
    rag_runs: list[dict[str, object]],
    best_rag: dict[str, object],
    target_samples: int,
) -> str:
    lines = [
        "# Baseline vs Two-RAG Comparison Report",
        "",
        "## Baseline",
        f"- Log: `{baseline_log.as_posix()}`",
        f"- Best score: {baseline.best if baseline.best is not None else 'NA'}",
        f"- Valid eval ratio: {baseline.valid_eval_ratio if baseline.valid_eval_ratio is not None else 'NA'}",
        f"- Sample progress evidence: {baseline.sample_lines}/{target_samples}",
        "",
        "## RAG Candidates",
    ]
    for rag_run in rag_runs:
        candidate = rag_run["candidate"]
        run = rag_run["run"]
        lines.extend([
            f"### {candidate['name']}",
            f"- Log: `{rag_run['log_path']}`",
            f"- Best score: {run['best'] if run['best'] is not None else 'NA'}",
            f"- Valid eval ratio: {run['valid_eval_ratio'] if run['valid_eval_ratio'] is not None else 'NA'}",
            f"- Retrieval events: {run['retrieval_events']}",
            f"- Mean retrieval confidence: {run['retrieval_mean_confidence'] if run['retrieval_mean_confidence'] is not None else 'NA'}",
            f"- Sample progress evidence: {run['sample_lines']}/{target_samples}",
            "",
        ])
    lines.extend([
        "## Best RAG",
        f"- Candidate: {best_rag['candidate']['name']}",
        f"- Best score: {best_rag['run']['best'] if best_rag['run']['best'] is not None else 'NA'}",
        "",
        "## Pairwise View Against Best RAG",
        build_pair_markdown(
            baseline_log=baseline_log,
            rag_log=Path(str(best_rag["log_path"])),
            baseline=baseline,
            rag=best_rag["parsed_run"],
            target_samples=target_samples,
        ).strip(),
        "",
    ])
    return "\n".join(lines)


def run_compare_suite(
    *,
    compare_config: CompareRunConfig,
    candidate_space: tuple[CompareCandidate, ...],
    model_spec: ModelSpec,
) -> dict[str, object]:
    if not candidate_space:
        raise RuntimeError("candidate_space is empty.")

    _, _, _, make_timestamp, _ = _load_runtime_bindings()
    timestamp = make_timestamp()
    results_dir = _resolve_results_dir(compare_config.results_dir)
    experiment_dir = results_dir / f"{timestamp}_{model_spec.result_label}_compare"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    baseline_log, baseline = _run_baseline(
        experiment_dir=experiment_dir,
        compare_config=compare_config,
        model_spec=model_spec,
    )

    rag_runs: list[dict[str, object]] = []
    best_rag: dict[str, object] | None = None
    best_score = float("-inf")

    for candidate in candidate_space:
        rag_log, rag = _run_rag_candidate(
            experiment_dir=experiment_dir,
            compare_config=compare_config,
            candidate=candidate,
            model_spec=model_spec,
        )
        rag_summary = {
            "candidate": dataclasses.asdict(candidate),
            "log_path": str(rag_log.as_posix()),
            "run": _parsed_run_summary(rag, rag_log),
            "parsed_run": rag,
        }
        rag_runs.append(rag_summary)
        candidate_best = rag.best if rag.best is not None else float("-inf")
        if candidate_best > best_score:
            best_score = candidate_best
            best_rag = rag_summary

    if best_rag is None:
        raise RuntimeError("No RAG runs were recorded.")

    report_path = experiment_dir / "compare_report.md"
    report_path.write_text(
        _build_suite_markdown(
            baseline_log=baseline_log,
            baseline=baseline,
            rag_runs=rag_runs,
            best_rag=best_rag,
            target_samples=compare_config.budget,
        ),
        encoding="utf-8",
    )

    serializable_rag_runs = [
        {key: value for key, value in rag_run.items() if key != "parsed_run"}
        for rag_run in rag_runs
    ]
    serializable_best_rag = {
        key: value for key, value in best_rag.items() if key != "parsed_run"
    }

    summary: dict[str, object] = {
        "timestamp": timestamp,
        "experiment_dir": str(experiment_dir.as_posix()),
        "summary_path": str((experiment_dir / "compare_summary.json").as_posix()),
        "report_path": str(report_path.as_posix()),
        "llm_model": model_spec.model_name,
        "seed": compare_config.seed,
        "run_mode": compare_config.run_mode,
        "budget": compare_config.budget,
        "baseline": _parsed_run_summary(baseline, baseline_log),
        "rag_runs": serializable_rag_runs,
        "best_rag": serializable_best_rag,
    }
    _write_json(experiment_dir / "compare_summary.json", summary)
    return summary


def run_single_rag_candidate(
    *,
    compare_config: CompareRunConfig,
    candidate: CompareCandidate,
    model_spec: ModelSpec,
) -> dict[str, object]:
    _, _, _, make_timestamp, _ = _load_runtime_bindings()
    timestamp = make_timestamp()
    results_dir = _resolve_results_dir(compare_config.results_dir)
    experiment_dir = results_dir / f"{timestamp}_{model_spec.result_label}_{candidate.name}"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    rag_log, rag = _run_rag_candidate(
        experiment_dir=experiment_dir,
        compare_config=compare_config,
        candidate=candidate,
        model_spec=model_spec,
    )

    summary = {
        "timestamp": timestamp,
        "experiment_dir": str(experiment_dir.as_posix()),
        "summary_path": str((experiment_dir / f"{candidate.name}_summary.json").as_posix()),
        "llm_model": model_spec.model_name,
        "seed": compare_config.seed,
        "run_mode": compare_config.run_mode,
        "budget": compare_config.budget,
        "candidate": dataclasses.asdict(candidate),
        "run": _parsed_run_summary(rag, rag_log),
    }
    _write_json(experiment_dir / f"{candidate.name}_summary.json", summary)
    return summary


def main() -> int:
    summary = run_compare_suite(
        compare_config=build_default_compare_config(),
        candidate_space=build_repro_candidate_space(),
        model_spec=build_repro_model_spec(),
    )
    print(f"Compare summary: {summary['summary_path']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
