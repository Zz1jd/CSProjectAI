#!/usr/bin/env python3
from __future__ import annotations

from scripts.experiments.rag_iteration_config import ModelRunSpec
from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig
from scripts.run_rag_iteration import run_iteration


def build_repro_iteration_config() -> RAGIterationConfig:
    # Lock the orchestration to the historical batch budgets and acceptance gate.
    return RAGIterationConfig(
        seed=42,
        run_mode="stage_eval",
        stage1_budget=2,
        stage2_budget=4,
        relative_gain_threshold_pct=5.0,
        acceptance_min_valid_eval_ratio=0.0,
        acceptance_max_valid_eval_drop=0.02,
        acceptance_min_relative_gain_pct=5.0,
        max_attempts=2,
        results_dir="results/experiments_repro_20260420_133019",
        log_dir="../logs/funsearch_rag_iteration_repro_20260420_133019",
        enable_thinking=False,
        control_corpus_version="v3.0.0_official_foundation",
        source_variant_versions=(),
    )


def build_repro_candidate_space() -> tuple[RAGIterationCandidate, ...]:
    # Keep attempt order and parameters identical to the historical batch.
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
    # Historical batch used gpt-3.5-turbo without reasoning probes.
    return ModelRunSpec(
        model_name="gpt-3.5-turbo",
        result_label="repro_gpt_3_5_turbo_20260420",
        reasoning_probes=(),
    )


def main() -> int:
    summary = run_iteration(
        iteration_config=build_repro_iteration_config(),
        candidate_space=build_repro_candidate_space(),
        model_spec=build_repro_model_spec(),
    )
    print(f"Reproduction summary: {summary['experiment_dir']}/summary.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
