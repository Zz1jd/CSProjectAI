#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import sys
from typing import Any

from scripts.compare_rag import ParsedRun
from scripts.compare_rag import parse_run_log


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

RUN_LOG_SUFFIX = ".txt"
DEFAULT_RESULTS_DIR = "results/experiments"
DEFAULT_LOG_DIR = "../logs/funsearch_rag"


@dataclasses.dataclass(frozen=True)
class ModelSpec:
    """Specifies the LLM model to test and the output label."""

    model_name: str
    result_label: str


@dataclasses.dataclass(frozen=True)
class RagRetrievalConfig:
    """A RAG retrieval configuration to evaluate."""

    name: str
    retrieval_mode: str
    use_intent_query: bool
    top_k: int
    score_threshold: float
    max_context_chars: int
    corpus_roots: tuple[str, ...]
    chunk_size: int | None = None
    chunk_overlap: int | None = None

    def as_rag_overrides(self) -> dict[str, object]:
        overrides: dict[str, object] = {
            "retrieval_mode": self.retrieval_mode,
            "use_intent_query": self.use_intent_query,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "max_context_chars": self.max_context_chars,
            "enable_diagnostics": True,
            "corpus_roots": self.corpus_roots,
        }
        if self.chunk_size is not None:
            overrides["chunk_size"] = self.chunk_size
        if self.chunk_overlap is not None:
            overrides["chunk_overlap"] = self.chunk_overlap
        return overrides


@dataclasses.dataclass(frozen=True)
class ExperimentRunConfig:
    """Runtime configuration for RAG evaluation experiments."""

    seed: int = 42
    run_mode: str = "stage_eval"
    budget: int = 100
    results_dir: str = DEFAULT_RESULTS_DIR
    log_dir: str = DEFAULT_LOG_DIR


def build_default_experiment_config() -> ExperimentRunConfig:
    return ExperimentRunConfig()


def build_quick_verify_config(budget: int = 2) -> ExperimentRunConfig:
    """Builds a low-budget configuration for quick verification."""
    return dataclasses.replace(build_default_experiment_config(), budget=budget)


def build_rag_configurations() -> tuple[RagRetrievalConfig, ...]:
    """Builds the RAG retrieval configuration for evaluation."""
    return (
        RagRetrievalConfig(
            name="default",
            corpus_roots=("corpus/",),
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
            chunk_size=1200,
            chunk_overlap=200,
        ),
    )


def build_test_model_spec() -> ModelSpec:
    """Builds the LLM model specification for testing."""
    return ModelSpec(
        model_name="gpt-3.5-turbo",
        result_label="test_gpt_3_5_turbo",
    )


def _load_runtime_bindings() -> tuple[Any, Any, Any, Any, Any]:
    from main import RUNTIME_DEFAULTS
    from main import build_runtime_config
    from scripts._runner import build_runtime_variant
    from scripts._runner import make_timestamp
    from scripts._runner import run_logged_experiment

    return (
        RUNTIME_DEFAULTS,
        build_runtime_config,
        build_runtime_variant,
        make_timestamp,
        run_logged_experiment,
    )


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
        "retrieval_skip_ratio": run.retrieval_skip_ratio,
    }


def _run_baseline(
    *,
    experiment_dir: Path,
    experiment_config: ExperimentRunConfig,
    model_spec: ModelSpec,
) -> tuple[Path, ParsedRun]:
    (
        runtime_defaults,
        build_runtime_config,
        build_runtime_variant,
        _,
        run_logged_experiment,
    ) = _load_runtime_bindings()
    base_config = dataclasses.replace(
        build_runtime_config(),
        llm_model=model_spec.model_name,
        random_seed=experiment_config.seed,
    )
    baseline_log = experiment_dir / f"baseline{RUN_LOG_SUFFIX}"
    baseline_config = build_runtime_variant(
        enable_rag=False,
        run_mode=experiment_config.run_mode,
        base_config=base_config,
        random_seed=experiment_config.seed,
        model_track="baseline",
    )
    run_logged_experiment(
        label="BASELINE",
        runtime_config=baseline_config,
        log_path=baseline_log,
        dataset_path=runtime_defaults.dataset_path,
        max_sample_nums=experiment_config.budget,
        log_dir=experiment_config.log_dir,
        header_fields={
            "RUN_MODE": experiment_config.run_mode,
            "RUN_BUDGET": experiment_config.budget,
        },
    )
    return baseline_log, parse_run_log(baseline_log)


def _run_single_rag_config(
    *,
    experiment_dir: Path,
    experiment_config: ExperimentRunConfig,
    rag_config: RagRetrievalConfig,
    model_spec: ModelSpec,
) -> tuple[Path, ParsedRun]:
    (
        runtime_defaults,
        build_runtime_config,
        build_runtime_variant,
        _,
        run_logged_experiment,
    ) = _load_runtime_bindings()
    base_config = dataclasses.replace(
        build_runtime_config(),
        llm_model=model_spec.model_name,
        random_seed=experiment_config.seed,
    )
    rag_log = experiment_dir / f"rag_{rag_config.name}{RUN_LOG_SUFFIX}"
    rag_config_obj = build_runtime_variant(
        enable_rag=True,
        run_mode=experiment_config.run_mode,
        base_config=base_config,
        random_seed=experiment_config.seed,
        model_track="rag",
        rag_overrides=rag_config.as_rag_overrides(),
    )
    run_logged_experiment(
        label=f"RAG_{rag_config.name}",
        runtime_config=rag_config_obj,
        log_path=rag_log,
        dataset_path=runtime_defaults.dataset_path,
        max_sample_nums=experiment_config.budget,
        log_dir=experiment_config.log_dir,
        header_fields={
            "RUN_MODE": experiment_config.run_mode,
            "RUN_BUDGET": experiment_config.budget,
            "RAG_CONFIG": rag_config.name,
        },
    )
    return rag_log, parse_run_log(rag_log)


def run_single_rag_config(
    *,
    experiment_config: ExperimentRunConfig,
    rag_config: RagRetrievalConfig,
    model_spec: ModelSpec,
) -> dict[str, object]:
    _, _, _, make_timestamp, _ = _load_runtime_bindings()
    timestamp = make_timestamp()
    results_dir = _resolve_results_dir(experiment_config.results_dir)
    experiment_dir = (
        results_dir / f"{timestamp}_{model_spec.result_label}_{rag_config.name}"
    )
    experiment_dir.mkdir(parents=True, exist_ok=True)

    rag_log, rag = _run_single_rag_config(
        experiment_dir=experiment_dir,
        experiment_config=experiment_config,
        rag_config=rag_config,
        model_spec=model_spec,
    )

    summary = {
        "timestamp": timestamp,
        "experiment_dir": str(experiment_dir.as_posix()),
        "summary_path": str(
            (experiment_dir / f"{rag_config.name}_summary.json").as_posix()
        ),
        "llm_model": model_spec.model_name,
        "seed": experiment_config.seed,
        "run_mode": experiment_config.run_mode,
        "budget": experiment_config.budget,
        "config": dataclasses.asdict(rag_config),
        "run": _parsed_run_summary(rag, rag_log),
    }
    _write_json(experiment_dir / f"{rag_config.name}_summary.json", summary)
    return summary
