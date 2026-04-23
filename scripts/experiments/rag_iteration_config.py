from __future__ import annotations

import dataclasses

from implementation import config as config_lib


@dataclasses.dataclass(frozen=True)
class ReasoningProbeSpec:
    request_mode: str
    reasoning_effort: str | None = None


@dataclasses.dataclass(frozen=True)
class ModelRunSpec:
    model_name: str
    result_label: str
    reasoning_probes: tuple[ReasoningProbeSpec, ...]


def _default_model_specs() -> tuple[ModelRunSpec, ...]:
    # Keep probe order explicit so the runtime can fail fast per model without fallback behavior.
    return (
        ModelRunSpec(
            model_name="qwen3.5-397b-a17b",
            result_label="qwen3_5_397b_a17b",
            reasoning_probes=(ReasoningProbeSpec(request_mode="enable_thinking"),),
        ),
        ModelRunSpec(
            model_name="gpt-5.4",
            result_label="gpt_5_4",
            reasoning_probes=(
                ReasoningProbeSpec(request_mode="reasoning_effort", reasoning_effort="medium"),
            ),
        ),
    )


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
class RAGIterationConfig:
    seed: int = 42
    run_mode: str = "stage_eval"
    stage1_budget: int = 20
    stage2_budget: int = 100
    relative_gain_threshold_pct: float = 10.0
    # Acceptance gates for stage comparisons. Defaults preserve current behavior.
    acceptance_min_valid_eval_ratio: float = 0.0
    acceptance_max_valid_eval_drop: float = 0.02
    acceptance_min_relative_gain_pct: float = 0.0
    max_attempts: int = 10
    results_dir: str = "results/experiments"
    log_dir: str = "../logs/funsearch_rag_iteration"
    # Applied by scripts-layer runtime patching so implementation/ stays unchanged.
    enable_thinking: bool = True
    model_specs: tuple[ModelRunSpec, ...] = dataclasses.field(default_factory=_default_model_specs)
    control_corpus_version: str = "v3.3.0_official_full"
    # Source-variant ablations are disabled by default; opt in explicitly if needed.
    source_variant_versions: tuple[str, ...] = ()
