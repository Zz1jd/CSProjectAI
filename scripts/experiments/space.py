from __future__ import annotations

from pathlib import Path

from implementation import config as config_lib
from scripts.experiments.rag_iteration_config import RAGIterationCandidate
from scripts.experiments.rag_iteration_config import RAGIterationConfig


# Fixed parameters shared by every candidate in the search space.
# Corpus, retrieval mode, and context budget are not search dimensions;
# they are constants validated by the corpus build plan.
_FIXED_RETRIEVAL_MODE = "hybrid"
# A scripts-layer runtime patch interprets 0 as "inject all retrieved chunks".
_NO_LIMIT_CONTEXT_CHARS = 0

_DEFAULT_RAG_CONFIG = config_lib.RAGConfig()
_DEFAULT_CHUNK_SIZE = _DEFAULT_RAG_CONFIG.chunk_size
_DEFAULT_CHUNK_OVERLAP = _DEFAULT_RAG_CONFIG.chunk_overlap

# Keep threshold naming derived from the numeric value so search-space labels stay in sync.
_UNIFIED_SCORE_THRESHOLD = 0.05
_QUERY_PHASE_SCORE_THRESHOLD = _UNIFIED_SCORE_THRESHOLD
_DENSITY_TOP3_SCORE_THRESHOLD = _UNIFIED_SCORE_THRESHOLD
_DENSITY_TOP5_SCORE_THRESHOLD = _UNIFIED_SCORE_THRESHOLD
_DENSITY_TOP5_CHUNKED_SCORE_THRESHOLD = _UNIFIED_SCORE_THRESHOLD
_DENSITY_TOP10_SCORE_THRESHOLD = _UNIFIED_SCORE_THRESHOLD


def _build_chunk_suffix(candidate: RAGIterationCandidate) -> str:
    chunk_size = candidate.chunk_size if candidate.chunk_size is not None else _DEFAULT_CHUNK_SIZE
    chunk_overlap = (
        candidate.chunk_overlap if candidate.chunk_overlap is not None else _DEFAULT_CHUNK_OVERLAP
    )
    if chunk_size == _DEFAULT_CHUNK_SIZE and chunk_overlap == _DEFAULT_CHUNK_OVERLAP:
        return ""
    return f"_chunk{chunk_size}_overlap{chunk_overlap}"


def _build_threshold_suffix(score_threshold: float) -> str:
    return f"threshold{int(round(score_threshold * 100)):02d}"


def _build_source_candidate_name(
    version: str,
    best_control_candidate: RAGIterationCandidate,
    use_intent_query: bool,
) -> str:
    # retrieval_mode and max_context_chars are fixed constants for all source variants;
    # the name only encodes dimensions that still vary (query strategy, top_k, chunk).
    base_name = (
        f"{version}_{_FIXED_RETRIEVAL_MODE}_"
        f"{'intent' if use_intent_query else 'raw'}_"
        f"top{best_control_candidate.top_k}"
    )
    return f"{base_name}{_build_chunk_suffix(best_control_candidate)}"


def _governed_corpus_exists(version: str) -> bool:
    return (Path("external_corpus") / version).exists()


def build_query_phase_candidates(
    iteration_config: RAGIterationConfig | None = None,
) -> tuple[RAGIterationCandidate, ...]:
    """Search over query strategy (intent vs raw) with fixed hybrid retrieval and corpus."""
    resolved_config = iteration_config or RAGIterationConfig()
    control_version = resolved_config.control_corpus_version

    return (
        RAGIterationCandidate(
            name="control_hybrid_intent_top3",
            corpus_version=control_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=True,
            top_k=3,
            score_threshold=_QUERY_PHASE_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
        ),
        RAGIterationCandidate(
            name="control_hybrid_raw_top3",
            corpus_version=control_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=False,
            top_k=3,
            score_threshold=_QUERY_PHASE_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
        ),
    )


def build_density_phase_candidates(
    best_query_candidate: RAGIterationCandidate,
) -> tuple[RAGIterationCandidate, ...]:
    """Search over retrieval density: top_k, threshold, and chunk granularity."""
    return (
        RAGIterationCandidate(
            name=(
                f"{best_query_candidate.corpus_version}_density_top3_"
                f"{_build_threshold_suffix(_DENSITY_TOP3_SCORE_THRESHOLD)}"
            ),
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=3,
            score_threshold=_DENSITY_TOP3_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
        ),
        RAGIterationCandidate(
            name=(
                f"{best_query_candidate.corpus_version}_density_top5_"
                f"{_build_threshold_suffix(_DENSITY_TOP5_SCORE_THRESHOLD)}"
            ),
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=5,
            score_threshold=_DENSITY_TOP5_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
        ),
        RAGIterationCandidate(
            name=(
                f"{best_query_candidate.corpus_version}_density_top5_"
                f"{_build_threshold_suffix(_DENSITY_TOP5_CHUNKED_SCORE_THRESHOLD)}"
                "_chunk900_overlap150"
            ),
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=5,
            score_threshold=_DENSITY_TOP5_CHUNKED_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
            chunk_size=900,
            chunk_overlap=150,
        ),
        RAGIterationCandidate(
            name=(
                f"{best_query_candidate.corpus_version}_density_top10_"
                f"{_build_threshold_suffix(_DENSITY_TOP10_SCORE_THRESHOLD)}"
                "_chunk1500_overlap300"
            ),
            corpus_version=best_query_candidate.corpus_version,
            retrieval_mode=_FIXED_RETRIEVAL_MODE,
            use_intent_query=best_query_candidate.use_intent_query,
            top_k=10,
            score_threshold=_DENSITY_TOP10_SCORE_THRESHOLD,
            max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
            chunk_size=1500,
            chunk_overlap=300,
        ),
    )


def build_source_phase_candidates(
    iteration_config: RAGIterationConfig,
    best_control_candidate: RAGIterationCandidate,
) -> tuple[RAGIterationCandidate, ...]:
    """Build optional source-variant ablation candidates when explicitly configured."""
    candidates: list[RAGIterationCandidate] = []

    for version in iteration_config.source_variant_versions:
        if not _governed_corpus_exists(version):
            continue
        # All source variants use the fixed retrieval mode and context limit;
        # keep use_intent_query from the best query-phase result.
        candidates.append(
            RAGIterationCandidate(
                name=_build_source_candidate_name(
                    version, best_control_candidate, best_control_candidate.use_intent_query
                ),
                corpus_version=version,
                retrieval_mode=_FIXED_RETRIEVAL_MODE,
                use_intent_query=best_control_candidate.use_intent_query,
                top_k=best_control_candidate.top_k,
                score_threshold=best_control_candidate.score_threshold,
                max_context_chars=_NO_LIMIT_CONTEXT_CHARS,
                chunk_size=best_control_candidate.chunk_size,
                chunk_overlap=best_control_candidate.chunk_overlap,
            )
        )

    return tuple(candidates)


def build_primary_candidate_space(
    iteration_config: RAGIterationConfig | None = None,
) -> tuple[RAGIterationCandidate, ...]:
    resolved_config = iteration_config or RAGIterationConfig()
    query_candidates = list(build_query_phase_candidates(resolved_config))
    density_candidates = list(build_density_phase_candidates(query_candidates[0]))
    # The default two-stage search stops after density refinement.
    return tuple((query_candidates + density_candidates)[:resolved_config.max_attempts])
