#!/usr/bin/env python3
"""Single-RAG evaluation runner."""
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
class ExperimentRunConfig:
    """Runtime configuration for RAG evaluation experiments."""

    seed: int = 42
    run_mode: str = "stage_eval"
    budget: int = 100
    results_dir: str = DEFAULT_RESULTS_DIR
    log_dir: str = DEFAULT_LOG_DIR


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


def run_rag_eval(
    *,
    experiment_config: ExperimentRunConfig,
    model_spec: ModelSpec,
) -> dict[str, object]:
    (
        _,
        build_runtime_config,
        build_runtime_variant,
        make_timestamp,
        run_logged_experiment,
    ) = _load_runtime_bindings()

    timestamp = make_timestamp()
    results_dir = _resolve_results_dir(experiment_config.results_dir)
    experiment_dir = results_dir / f"{timestamp}_{model_spec.result_label}_rag"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    base_config = dataclasses.replace(
        build_runtime_config(),
        llm_model=model_spec.model_name,
        random_seed=experiment_config.seed,
    )

    rag_config = dataclasses.replace(
        base_config.rag,
        enabled=True,
        corpus_root="corpus/",
        retrieval_mode="hybrid",
        use_intent_query=True,
        top_k=2,
        score_threshold=0.05,
        max_context_chars=900,
        chunk_size=1200,
        chunk_overlap=200,
        enable_diagnostics=True,
    )

    runtime_config = dataclasses.replace(
        base_config,
        run_mode=experiment_config.run_mode,
        random_seed=experiment_config.seed,
        model_track="rag",
        rag=rag_config,
    )

    rag_log = experiment_dir / f"rag{RUN_LOG_SUFFIX}"

    run_logged_experiment(
        label="RAG",
        runtime_config=runtime_config,
        log_path=rag_log,
        dataset_path=PROJECT_ROOT / "./cvrplib/setB",
        max_sample_nums=experiment_config.budget,
        log_dir=experiment_config.log_dir,
        header_fields={
            "RUN_MODE": experiment_config.run_mode,
            "RUN_BUDGET": experiment_config.budget,
        },
    )

    rag = parse_run_log(rag_log)

    config_snapshot = {
        "llm_model": model_spec.model_name,
        "seed": experiment_config.seed,
        "run_mode": experiment_config.run_mode,
        "budget": experiment_config.budget,
        "rag_corpus_root": rag_config.corpus_root,
        "rag_retrieval_mode": rag_config.retrieval_mode,
        "rag_use_intent_query": rag_config.use_intent_query,
        "rag_top_k": rag_config.top_k,
        "rag_score_threshold": rag_config.score_threshold,
        "rag_max_context_chars": rag_config.max_context_chars,
        "rag_chunk_size": rag_config.chunk_size,
        "rag_chunk_overlap": rag_config.chunk_overlap,
    }

    summary = {
        "timestamp": timestamp,
        "experiment_dir": str(experiment_dir.as_posix()),
        "summary_path": str((experiment_dir / "rag_summary.json").as_posix()),
        "config": config_snapshot,
        "run": _parsed_run_summary(rag, rag_log),
    }
    _write_json(experiment_dir / "rag_summary.json", summary)
    return summary
