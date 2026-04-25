#!/usr/bin/env python3
from __future__ import annotations

import dataclasses
import json
from pathlib import Path
import sys

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from main import RUNTIME_DEFAULTS
from main import build_runtime_config
from scripts._runner import build_runtime_variant
from scripts._runner import make_timestamp
from scripts._runner import run_logged_experiment
from scripts.compare_rag import AcceptanceConfig
from scripts.compare_rag import ComparePolicyConfig
from scripts.compare_rag import build_pair_markdown
from scripts.compare_rag import evaluate_acceptance
from scripts.compare_rag import parse_run_log
from scripts.experiments.rag_iteration_config import ModelRunSpec
from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig


# Keep one suffix constant so all run logs switch together (DRY).
RUN_LOG_SUFFIX = ".txt"


def build_repro_compare_config() -> RAGIterationConfig:
    # Pure baseline-vs-RAG comparison: run both sides at the same fixed budget.
    # Note: we keep run_mode="stage_eval" to avoid compare-mode budget capping.
    return RAGIterationConfig(
        seed=42,
        run_mode="stage_eval",
        stage2_budget=100,
        results_dir="results/experiments_repro_20260420_133019",
        log_dir="../logs/funsearch_rag_compare_repro_20260420_133019",
        enable_thinking=False,
        control_corpus_version="v3.0.0_official_foundation",
        source_variant_versions=(),
    )


def build_repro_candidate_space() -> tuple[RAGIterationCandidate, ...]:
    return (
        RAGIterationCandidate(
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
        RAGIterationCandidate(
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


def build_repro_model_spec() -> ModelRunSpec:
    return ModelRunSpec(
        model_name="gpt-3.5-turbo",
        result_label="repro_gpt_3_5_turbo_20260420",
        reasoning_probes=(),
    )


def _resolve_results_dir(results_dir: str) -> Path:
    configured = Path(results_dir)
    return configured if configured.is_absolute() else PROJECT_ROOT / configured


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")


def run_pure_compare(
    *,
    compare_config: RAGIterationConfig,
    candidate_space: tuple[RAGIterationCandidate, ...],
    model_spec: ModelRunSpec,
) -> dict[str, object]:
    results_dir = _resolve_results_dir(compare_config.results_dir)
    timestamp = make_timestamp()
    budget = int(compare_config.stage2_budget)

    experiment_dir = results_dir / f"{timestamp}_{model_spec.result_label}_compare"
    experiment_dir.mkdir(parents=True, exist_ok=True)

    base_config = build_runtime_config()
    base_config = dataclasses.replace(
        base_config,
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
        dataset_path=RUNTIME_DEFAULTS.dataset_path,
        max_sample_nums=budget,
        log_dir=compare_config.log_dir,
        header_fields={"RUN_MODE": compare_config.run_mode, "RUN_BUDGET": budget},
    )
    baseline = parse_run_log(baseline_log)

    policy = ComparePolicyConfig(
        allowed_run_modes=(compare_config.run_mode,),
        compare_budget_cap=None,
        require_same_run_mode=True,
    )
    acceptance_config = AcceptanceConfig(
        policy=policy,
        min_valid_eval_ratio=0.0,
        max_valid_eval_drop=1.0,
        max_completion_drop=1.0,
        min_relative_gain_pct=0.0,
        require_same_seed=True,
    )

    best_candidate: RAGIterationCandidate | None = None
    best_rag_log: Path | None = None
    best_rag = None
    best_rag_score = float("-inf")
    best_acceptance: dict[str, object] | None = None

    for candidate in candidate_space:
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
            dataset_path=RUNTIME_DEFAULTS.dataset_path,
            max_sample_nums=budget,
            log_dir=compare_config.log_dir,
            header_fields={
                "RUN_MODE": compare_config.run_mode,
                "RUN_BUDGET": budget,
                "RAG_CANDIDATE": candidate.name,
            },
        )
        rag = parse_run_log(rag_log)
        rag_best = rag.best if rag.best is not None else float("-inf")
        if best_candidate is None or rag_best > best_rag_score:
            best_candidate = candidate
            best_rag_log = rag_log
            best_rag = rag
            best_rag_score = rag_best
            best_acceptance = evaluate_acceptance(
                baseline=baseline,
                rag=rag,
                target_samples=budget,
                acceptance_config=acceptance_config,
            )

    if best_candidate is None or best_rag_log is None or best_rag is None:
        raise RuntimeError("No RAG candidates executed; candidate_space is empty.")

    report_path = experiment_dir / "compare_report.md"
    report_path.write_text(
        build_pair_markdown(
            baseline_log=baseline_log,
            rag_log=best_rag_log,
            baseline=baseline,
            rag=best_rag,
            target_samples=budget,
            acceptance_config=acceptance_config,
        ),
        encoding="utf-8",
    )

    summary: dict[str, object] = {
        "timestamp": timestamp,
        "experiment_dir": str(experiment_dir.as_posix()),
        "llm_model": model_spec.model_name,
        "seed": compare_config.seed,
        "run_mode": compare_config.run_mode,
        "budget": budget,
        "baseline_log": str(baseline_log.as_posix()),
        "rag_log": str(best_rag_log.as_posix()),
        "rag_candidate_name": best_candidate.name,
        "rag_candidate": dataclasses.asdict(best_candidate),
        "baseline_best": baseline.best,
        "rag_best": best_rag.best,
        "baseline_valid_eval_ratio": baseline.valid_eval_ratio,
        "rag_valid_eval_ratio": best_rag.valid_eval_ratio,
        "acceptance": best_acceptance,
        "report_path": str(report_path.as_posix()),
    }
    _write_json(experiment_dir / "compare_summary.json", summary)
    return summary


def main() -> int:
    summary = run_pure_compare(
        compare_config=build_repro_compare_config(),
        candidate_space=build_repro_candidate_space(),
        model_spec=build_repro_model_spec(),
    )
    print(f"Compare summary: {summary['experiment_dir']}/compare_summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

