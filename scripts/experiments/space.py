from __future__ import annotations

from pathlib import Path

from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig


_RAW_QUERY_SOURCE_VARIANTS = {
    "v3.2.0_dynamic_history",
    "v3.3.0_full_corpus",
}


def _governed_corpus_exists(version: str) -> bool:
    return (Path("external_corpus") / version).exists()


def build_query_phase_candidates(
    iteration_config: RAGIterationConfig | None = None,
) -> tuple[RAGIterationCandidate, ...]:
    resolved_config = iteration_config or RAGIterationConfig()
    control_version = resolved_config.control_corpus_version

    return (
        RAGIterationCandidate(
            name="control_vector_intent_top2_ctx800",
            corpus_version=control_version,
            retrieval_mode="vector",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.00,
            max_context_chars=800,
        ),
        RAGIterationCandidate(
            name="control_vector_raw_top2_ctx800",
            corpus_version=control_version,
            retrieval_mode="vector",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.00,
            max_context_chars=800,
        ),
        RAGIterationCandidate(
            name="control_hybrid_intent_top2_ctx900",
            corpus_version=control_version,
            retrieval_mode="hybrid",
            use_intent_query=True,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
        ),
        RAGIterationCandidate(
            name="control_hybrid_raw_top2_ctx900",
            corpus_version=control_version,
            retrieval_mode="hybrid",
            use_intent_query=False,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
        ),
    )


def build_density_phase_candidates(
    best_query_candidate: RAGIterationCandidate,
) -> tuple[RAGIterationCandidate, ...]:
    return (
        RAGIterationCandidate(
            name=f"{best_query_candidate.corpus_version}_density_top1_threshold10_ctx700",
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=best_query_candidate.retrieval_mode,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=1,
            score_threshold=0.10,
            max_context_chars=700,
        ),
        RAGIterationCandidate(
            name=f"{best_query_candidate.corpus_version}_density_top2_threshold05_ctx900",
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=best_query_candidate.retrieval_mode,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=2,
            score_threshold=0.05,
            max_context_chars=900,
        ),
        RAGIterationCandidate(
            name=f"{best_query_candidate.corpus_version}_density_top3_threshold00_ctx1100",
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=best_query_candidate.retrieval_mode,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=3,
            score_threshold=0.00,
            max_context_chars=1100,
        ),
    )


def build_source_phase_candidates(
    iteration_config: RAGIterationConfig,
    best_control_candidate: RAGIterationCandidate,
) -> tuple[RAGIterationCandidate, ...]:
    candidates: list[RAGIterationCandidate] = []

    for version in iteration_config.source_variant_versions:
        if not _governed_corpus_exists(version):
            continue
        use_intent_query = (
            False if version in _RAW_QUERY_SOURCE_VARIANTS else best_control_candidate.use_intent_query
        )
        candidates.append(
            RAGIterationCandidate(
                name=f"{version}_{best_control_candidate.retrieval_mode}_{'intent' if use_intent_query else 'raw'}_top{best_control_candidate.top_k}_ctx{best_control_candidate.max_context_chars}",
                corpus_version=version,
                retrieval_mode=best_control_candidate.retrieval_mode,
                use_intent_query=use_intent_query,
                top_k=best_control_candidate.top_k,
                score_threshold=best_control_candidate.score_threshold,
                max_context_chars=best_control_candidate.max_context_chars,
            )
        )

    return tuple(candidates)


def build_primary_candidate_space(
    iteration_config: RAGIterationConfig | None = None,
) -> tuple[RAGIterationCandidate, ...]:
    resolved_config = iteration_config or RAGIterationConfig()
    query_candidates = list(build_query_phase_candidates(resolved_config))
    density_candidates = list(build_density_phase_candidates(query_candidates[2]))
    source_candidates = list(build_source_phase_candidates(resolved_config, density_candidates[1]))
    return tuple((query_candidates + density_candidates + source_candidates)[:resolved_config.max_attempts])
