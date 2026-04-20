from __future__ import annotations

import dataclasses

from implementation import config as config_lib


@dataclasses.dataclass(frozen=True)
class RAGIterationCandidate:
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
        return (config_lib.build_governed_corpus_root(self.corpus_version),)

    def as_rag_overrides(self) -> dict[str, object]:
        overrides: dict[str, object] = {
            "retrieval_mode": self.retrieval_mode,
            "use_intent_query": self.use_intent_query,
            "top_k": self.top_k,
            "score_threshold": self.score_threshold,
            "max_context_chars": self.max_context_chars,
            "enable_diagnostics": True,
        }
        corpus_roots = self.resolve_corpus_roots()
        if corpus_roots is not None:
            overrides["corpus_roots"] = corpus_roots
        if self.chunk_size is not None:
            overrides["chunk_size"] = self.chunk_size
        if self.chunk_overlap is not None:
            overrides["chunk_overlap"] = self.chunk_overlap
        return overrides


@dataclasses.dataclass(frozen=True)
class RAGIterationConfig:
    seed: int = 42
    run_mode: str = "stage_eval"
    stage1_budget: int = 20
    stage2_budget: int = 100
    relative_gain_threshold_pct: float = 5.0
    max_attempts: int = 10
    results_dir: str = "results/experiments"
    log_dir: str = "../logs/funsearch_rag_iteration"
    control_corpus_version: str = "v3.0.0_official_foundation"
    # V3.1 stays deferred; source-variant search now targets the authored V3.2 and V3.3 families.
    source_variant_versions: tuple[str, ...] = (
        "v3.2.0_dynamic_history",
        "v3.3.0_full_corpus",
    )
