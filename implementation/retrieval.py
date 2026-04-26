from __future__ import annotations

import dataclasses
import math
import re
from collections import Counter
from pathlib import Path
from statistics import mean
from typing import Callable, Sequence

from implementation.corpus_governance import normalize_source_metadata
from implementation.openai_compat import normalize_openai_base_url
from implementation.corpus_governance import parse_front_matter


_TOKEN_PATTERN = re.compile(r"[A-Za-z0-9_]+")
_DEFAULT_ALLOWED_SUFFIXES = (".md", ".markdown", ".txt", ".rst")
_PARAGRAPH_SPLIT_PATTERN = re.compile(r"\n\s*\n+")
_MIN_INFORMATION_DENSITY = 0.25
_SKIP_RETRIEVAL_CONFIDENCE = 0.2
_SUMMARY_ONLY_CONFIDENCE = 0.45
_OPENAI_EMBEDDING_MAX_INPUT_TOKENS = 480
_OPENAI_EMBEDDING_MAX_BATCH_SIZE = 32
_OPENAI_EMBEDDING_RETRY_TOKEN_BUDGETS = (480, 256, 128, 64)
EmbeddingFunction = Callable[[list[str]], list[list[float]]]

_SEMANTIC_HINTS: dict[str, set[str]] = {
    "capacity": {"remaining_capacity", "load", "vehicle_capacity", "feasibility"},
    "distance": {"nearest", "cost", "travel", "routing"},
    "demand": {"customer", "node_demands", "delivery", "load"},
    "feasibility": {"constraint", "valid", "capacity", "infeasible"},
    "numpy": {"vectorized", "array", "broadcast", "np"},
    "vectorized": {"numpy", "no", "loops"},
}


@dataclasses.dataclass(frozen=True)
class KnowledgeChunk:
    """One retrieved chunk of external knowledge.

    The chunk text is cached once so retrieval can reuse it without re-reading files.
    """

    source_path: Path
    chunk_index: int
    text: str
    score: float = 0.0
    metadata: dict[str, object] = dataclasses.field(default_factory=dict)


class ExternalKnowledgeIndex:
    """Simple TF-IDF index for external prompt context.

    The index keeps chunk vectors in memory so retrieval stays lightweight and
    prompt assembly does not need to rebuild text statistics for each LLM call.
    """

    def __init__(
            self,
            chunks: Sequence[KnowledgeChunk],
            term_frequencies: Sequence[Counter[str]],
            document_frequencies: Counter[str],
            embedding_function: EmbeddingFunction | None = None,
            chunk_embeddings: Sequence[Sequence[float]] | None = None,
    ) -> None:
        self._chunks = list(chunks)
        self._term_frequencies = list(term_frequencies)
        self._document_frequencies = document_frequencies
        self._document_count = len(self._chunks)
        self._embedding_function = embedding_function
        self._chunk_vectors: list[dict[str, float]] = []
        self._chunk_norms: list[float] = []
        self._chunk_embeddings: list[list[float]] | None = None
        self._chunk_embedding_norms: list[float] = []

        for frequencies in self._term_frequencies:
            vector = self._build_lexical_vector(frequencies)
            self._chunk_vectors.append(vector)
            self._chunk_norms.append(self._vector_norm(vector))

        if chunk_embeddings is not None:
            self._chunk_embeddings = [self._coerce_dense_vector(vector) for vector in chunk_embeddings]
            if len(self._chunk_embeddings) != len(self._chunks):
                raise ValueError("Vector index size mismatch between chunks and embeddings.")
            self._chunk_embedding_norms = [
                self._dense_vector_norm(vector) for vector in self._chunk_embeddings
            ]

    @classmethod
    def from_paths(
            cls,
            corpus_root: str | Path,
            chunk_size: int = 1200,
            chunk_overlap: int = 200,
            allowed_suffixes: Sequence[str] = _DEFAULT_ALLOWED_SUFFIXES,
            enable_vector_index: bool = False,
            embedding_model: str = "text-embedding-3-small",
            embedding_function: EmbeddingFunction | None = None,
            embedding_base_url: str | None = None,
            embedding_api_key: str | None = None,
            embedding_timeout_seconds: int = 60,
    ) -> "ExternalKnowledgeIndex":
        """Builds an index from a corpus root directory."""
        chunks: list[KnowledgeChunk] = []
        term_frequencies: list[Counter[str]] = []
        document_frequencies: Counter[str] = Counter()
        allowed_suffixes_set = {suffix.lower() for suffix in allowed_suffixes}

        root_path = Path(corpus_root)
        requires_governed_front_matter = _requires_governed_front_matter(root_path)
        for document_path in cls._iter_documents(root_path, allowed_suffixes_set):
                text = document_path.read_text(encoding="utf-8", errors="ignore")
                front_matter, body = parse_front_matter(text)
                if requires_governed_front_matter and not front_matter:
                    continue
                document_text = body if body else text
                source_metadata = normalize_source_metadata(front_matter)
                source_metadata["relative_source_path"] = document_path.as_posix()
                for chunk_index, chunk_text in enumerate(
                        _chunk_text(document_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)):
                    cleaned_text = chunk_text.strip()
                    if not cleaned_text:
                        continue
                    chunk = KnowledgeChunk(
                        source_path=document_path,
                        chunk_index=chunk_index,
                        text=cleaned_text,
                        metadata=source_metadata,
                    )
                    chunks.append(chunk)
                    frequencies = Counter(_tokenize(cleaned_text))
                    term_frequencies.append(frequencies)
                    document_frequencies.update(frequencies.keys())

        resolved_embedding_function = embedding_function
        chunk_embeddings: list[list[float]] | None = None
        if enable_vector_index:
            if resolved_embedding_function is None:
                resolved_embedding_function = _build_openai_embedding_function(
                    model=embedding_model,
                    base_url=embedding_base_url,
                    api_key=embedding_api_key,
                    timeout_seconds=embedding_timeout_seconds,
                )

            chunk_texts = [chunk.text for chunk in chunks]
            chunk_embeddings = resolved_embedding_function(chunk_texts) if chunk_texts else []
            if len(chunk_embeddings) != len(chunks):
                raise ValueError("Embedding function returned unexpected number of vectors.")

        return cls(
            chunks,
            term_frequencies,
            document_frequencies,
            embedding_function=resolved_embedding_function,
            chunk_embeddings=chunk_embeddings,
        )

    def retrieve(
            self,
            query: str,
            top_k: int = 3,
            mode: str = "hybrid",
            score_threshold: float = 0.0,
            diagnostics: dict[str, object] | None = None,
    ) -> list[KnowledgeChunk]:
        """Returns the most relevant chunks for a query."""
        if top_k <= 0 or not self._chunks:
            return []

        if mode not in {"hybrid", "vector"}:
            raise ValueError(f"Unsupported retrieval mode: {mode}")

        if mode == "vector":
            scored_chunks = self._score_chunks_with_vectors(query)
        else:
            query_frequencies = Counter(_tokenize(query))
            if not query_frequencies:
                return []

            query_vector = self._build_query_vector(query_frequencies)
            query_norm = self._vector_norm(query_vector)
            if query_norm == 0:
                return []

            scored_chunks = []
            for chunk, chunk_vector, chunk_norm in zip(self._chunks, self._chunk_vectors, self._chunk_norms):
                score = self._cosine_similarity(query_vector, chunk_vector, query_norm, chunk_norm)
                scored_chunks.append(dataclasses.replace(chunk, score=score))

            scored_chunks = _hybrid_rerank(query=query, chunks=scored_chunks)

        filtered_chunks = [chunk for chunk in scored_chunks if chunk.score >= score_threshold]
        filtered_chunks.sort(key=lambda chunk: (-chunk.score, chunk.source_path.as_posix(), chunk.chunk_index))
        selected_chunks = filtered_chunks[:top_k]

        if diagnostics is not None:
            query_tokens = set(_tokenize(query))
            selected_sources = [
                f"{chunk.source_path.as_posix()}#chunk-{chunk.chunk_index + 1}"
                for chunk in selected_chunks
            ]
            top_score_gap = 0.0
            if len(selected_chunks) >= 2:
                top_score_gap = max(selected_chunks[0].score - selected_chunks[1].score, 0.0)
            elif selected_chunks:
                top_score_gap = max(selected_chunks[0].score, 0.0)

            unique_source_count = len({chunk.source_path.as_posix() for chunk in selected_chunks})
            mean_authority_score = _mean_authority_score(selected_chunks)
            mean_topic_alignment = _mean_topic_alignment(selected_chunks, query_tokens)
            source_agreement = _source_agreement(selected_chunks)
            retrieval_confidence = _compute_retrieval_confidence(
                top_score=selected_chunks[0].score if selected_chunks else 0.0,
                top_score_gap=top_score_gap,
                mean_authority_score=mean_authority_score,
                mean_topic_alignment=mean_topic_alignment,
                source_agreement=source_agreement,
            )

            diagnostics["query"] = query
            diagnostics["mode"] = mode
            diagnostics["score_threshold"] = score_threshold
            diagnostics["candidate_count"] = len(scored_chunks)
            diagnostics["selected_count"] = len(selected_chunks)
            diagnostics["filtered_count"] = max(len(scored_chunks) - len(filtered_chunks), 0)
            diagnostics["selected_sources"] = selected_sources
            diagnostics["selected_scores"] = [round(chunk.score, 6) for chunk in selected_chunks]
            diagnostics["top_score"] = selected_chunks[0].score if selected_chunks else 0.0
            diagnostics["top_score_gap"] = round(top_score_gap, 6)
            diagnostics["unique_source_count"] = unique_source_count
            diagnostics["mean_authority_score"] = round(mean_authority_score, 6)
            diagnostics["mean_topic_alignment"] = round(mean_topic_alignment, 6)
            diagnostics["source_agreement"] = round(source_agreement, 6)
            diagnostics["retrieval_confidence"] = round(retrieval_confidence, 6)
            diagnostics["selected_source_types"] = [
                str(chunk.metadata.get("source_type", "")) for chunk in selected_chunks
            ]
            diagnostics["selected_summary_levels"] = [
                str(chunk.metadata.get("summary_level", "leaf")) for chunk in selected_chunks
            ]
            diagnostics["selected_authority_scores"] = [
                chunk.metadata.get("authority_score") for chunk in selected_chunks
            ]
            diagnostics["should_skip_retrieval"] = retrieval_confidence < 0.2

        return selected_chunks

    def _build_query_vector(self, frequencies: Counter[str]) -> dict[str, float]:
        return {
            term: frequency * self._idf(term)
            for term, frequency in frequencies.items()
        }

    def _build_lexical_vector(self, frequencies: Counter[str]) -> dict[str, float]:
        return {
            term: frequency * self._idf(term)
            for term, frequency in frequencies.items()
        }

    def _idf(self, term: str) -> float:
        # The +1 smoothing keeps rare terms useful without exploding their weight.
        document_frequency = self._document_frequencies.get(term, 0)
        return math.log((1 + self._document_count) / (1 + document_frequency)) + 1.0

    @staticmethod
    def _vector_norm(vector: dict[str, float]) -> float:
        return math.sqrt(sum(weight * weight for weight in vector.values()))

    @staticmethod
    def _dense_vector_norm(vector: Sequence[float]) -> float:
        return math.sqrt(sum(value * value for value in vector))

    @staticmethod
    def _cosine_similarity(
            query_vector: dict[str, float],
            chunk_vector: dict[str, float],
            query_norm: float,
            chunk_norm: float,
    ) -> float:
        if query_norm == 0 or chunk_norm == 0:
            return 0.0
        shared_terms = query_vector.keys() & chunk_vector.keys()
        dot_product = sum(query_vector[term] * chunk_vector[term] for term in shared_terms)
        return dot_product / (query_norm * chunk_norm)

    @staticmethod
    def _dense_cosine_similarity(
            query_vector: Sequence[float],
            chunk_vector: Sequence[float],
            query_norm: float,
            chunk_norm: float,
    ) -> float:
        if query_norm == 0 or chunk_norm == 0:
            return 0.0
        if len(query_vector) != len(chunk_vector):
            raise ValueError("Embedding dimension mismatch between query and chunk vectors.")
        dot_product = sum(left * right for left, right in zip(query_vector, chunk_vector))
        return dot_product / (query_norm * chunk_norm)

    @staticmethod
    def _coerce_dense_vector(vector: Sequence[float]) -> list[float]:
        return [float(value) for value in vector]

    def _score_chunks_with_vectors(self, query: str) -> list[KnowledgeChunk]:
        if self._embedding_function is None or self._chunk_embeddings is None:
            raise ValueError("Vector retrieval requested but vector index is not enabled.")

        query_text = _compact_vector_query(query)
        if not query_text:
            return []

        query_embeddings = self._embedding_function([query_text])
        if len(query_embeddings) != 1:
            raise ValueError("Embedding function must return exactly one query vector.")

        query_vector = self._coerce_dense_vector(query_embeddings[0])
        if not query_vector:
            return []
        if self._chunk_embeddings and len(query_vector) != len(self._chunk_embeddings[0]):
            raise ValueError("Embedding dimension mismatch between query and corpus vectors.")

        query_norm = self._dense_vector_norm(query_vector)
        if query_norm == 0:
            return []

        scored_chunks: list[KnowledgeChunk] = []
        for chunk, chunk_vector, chunk_norm in zip(
                self._chunks, self._chunk_embeddings, self._chunk_embedding_norms):
            score = self._dense_cosine_similarity(query_vector, chunk_vector, query_norm, chunk_norm)
            scored_chunks.append(dataclasses.replace(chunk, score=score))
        return scored_chunks

    @staticmethod
    def _iter_documents(root_path: Path, allowed_suffixes: set[str]):
        if root_path.is_file():
            if root_path.suffix.lower() in allowed_suffixes:
                yield root_path
            return

        if not root_path.exists():
            return

        for file_path in sorted(root_path.rglob("*")):
            if file_path.is_file() and file_path.suffix.lower() in allowed_suffixes:
                yield file_path


def format_retrieved_chunks(chunks: Sequence[KnowledgeChunk], max_chars: int = 1200) -> str:
    """Formats retrieved chunks into a compact prompt section."""
    fitted_chunks = _fit_chunks_to_context(chunks, max_chars=max_chars)
    if not fitted_chunks:
        return ""

    lines = ["### RETRIEVED EXTERNAL KNOWLEDGE ###"]
    for index, chunk in enumerate(fitted_chunks, start=1):
        source_label = f"{chunk.source_path.as_posix()}#chunk-{chunk.chunk_index + 1}"
        topic_label = chunk.source_path.parent.name
        block = "\n".join([
            f"[{index}] {source_label} (score={chunk.score:.3f}, topic={topic_label})",
            chunk.text.strip(),
            "",
        ])
        lines.extend(block.splitlines())

    return "\n".join(lines).rstrip()


def _fit_chunks_to_context(chunks: Sequence[KnowledgeChunk], max_chars: int) -> list[KnowledgeChunk]:
    if max_chars <= 0:
        return []

    fitted_chunks: list[KnowledgeChunk] = []
    running_text = "### RETRIEVED EXTERNAL KNOWLEDGE ###"
    for index, chunk in enumerate(chunks, start=1):
        source_label = f"{chunk.source_path.as_posix()}#chunk-{chunk.chunk_index + 1}"
        topic_label = chunk.source_path.parent.name
        block = "\n".join([
            f"[{index}] {source_label} (score={chunk.score:.3f}, topic={topic_label})",
            chunk.text.strip(),
            "",
        ])
        if len(running_text) + len(block) >= max_chars:
            break
        fitted_chunks.append(chunk)
        running_text = f"{running_text}\n{block}".rstrip()
    return fitted_chunks


def _is_summary_chunk(chunk: KnowledgeChunk) -> bool:
    return str(chunk.metadata.get("summary_level", "leaf")).strip().lower() == "summary"


def _requires_governed_front_matter(root_path: Path) -> bool:
    return any(parent.name == "corpus" for parent in (root_path, *root_path.parents))


def _select_chunks_for_injection(
        chunks: Sequence[KnowledgeChunk],
        diagnostics: dict[str, object] | None,
) -> tuple[list[KnowledgeChunk], str]:
    if not chunks:
        return [], "none"

    retrieval_confidence: float | None = None
    if diagnostics is not None:
        raw_confidence = diagnostics.get("retrieval_confidence")
        if isinstance(raw_confidence, (int, float)):
            retrieval_confidence = float(raw_confidence)
        if diagnostics.get("should_skip_retrieval") is True:
            return [], "skip"

    if retrieval_confidence is not None and retrieval_confidence < _SKIP_RETRIEVAL_CONFIDENCE:
        return [], "skip"

    summary_chunks = [chunk for chunk in chunks if _is_summary_chunk(chunk)]
    leaf_chunks = [chunk for chunk in chunks if not _is_summary_chunk(chunk)]

    if retrieval_confidence is None:
        return list(chunks), "top_chunks"

    if retrieval_confidence < _SUMMARY_ONLY_CONFIDENCE:
        if summary_chunks:
            return [summary_chunks[0]], "summary_only"
        return [chunks[0]], "top1_only"

    if summary_chunks:
        selected = [summary_chunks[0]]
        for leaf_chunk in leaf_chunks:
            if leaf_chunk.source_path != summary_chunks[0].source_path or leaf_chunk.chunk_index != summary_chunks[0].chunk_index:
                selected.append(leaf_chunk)
                break
        if len(selected) == 1:
            for chunk in chunks:
                if chunk.source_path != selected[0].source_path or chunk.chunk_index != selected[0].chunk_index:
                    selected.append(chunk)
                    break
        return selected, "summary_plus_leaf" if len(selected) > 1 else "summary_only"

    return list(chunks[:2]), "top_chunks"


def build_intent_query(base_code: str, task_label: str = "CVRP") -> str:
    """Builds a focused retrieval query from prompt code intent."""
    tokens = set(_tokenize(base_code))
    intent_terms = [
        task_label.lower(),
        "priority",
        "heuristic",
        "capacity",
        "feasibility",
        "constraint",
        "distance",
        "demand",
        "numpy",
        "vectorized",
        "no_loops",
    ]
    intent_terms.extend(sorted(token for token in tokens if token in {
        "remaining_capacity",
        "node_demands",
        "distance_data",
        "current_node",
        "depot",
    }))

    return " ".join(_dedup_preserve_order(intent_terms))


def build_enhanced_prompt(
        base_code: str,
        prompt_engine: object,
        retriever: ExternalKnowledgeIndex | None = None,
        top_k: int = 3,
        retrieval_query: str | None = None,
    retrieval_mode: str = "vector",
        score_threshold: float = 0.0,
        max_context_chars: int = 1200,
        use_intent_query: bool = True,
        diagnostics: dict[str, object] | None = None,
) -> str:
    """Builds the final prompt from base code and optional external knowledge."""
    # Keep retrieval and formatting in one place so sampler does not duplicate prompt logic.
    external_context = ""
    if retriever is not None:
        if retrieval_query is not None:
            query = retrieval_query
        elif use_intent_query:
            query = build_intent_query(base_code)
        else:
            query = base_code

        retrieved_chunks = retriever.retrieve(
            query,
            top_k=top_k,
            mode=retrieval_mode,
            score_threshold=score_threshold,
            diagnostics=diagnostics,
        )
        injected_chunks, retrieval_policy = _select_chunks_for_injection(
            retrieved_chunks,
            diagnostics=diagnostics,
        )
        fitted_chunks = _fit_chunks_to_context(injected_chunks, max_chars=max_context_chars)
        if injected_chunks and not fitted_chunks and retrieval_policy != "skip":
            retrieval_policy = "context_pruned"
        external_context = format_retrieved_chunks(fitted_chunks, max_chars=max_context_chars)
        if diagnostics is not None:
            diagnostics["applied_retrieval_policy"] = retrieval_policy
            diagnostics["applied_selected_sources"] = [
                f"{chunk.source_path.as_posix()}#chunk-{chunk.chunk_index + 1}"
                for chunk in fitted_chunks
            ]
            diagnostics["injected_source_count"] = len({chunk.source_path.as_posix() for chunk in fitted_chunks})
            diagnostics["injected_summary_count"] = sum(1 for chunk in fitted_chunks if _is_summary_chunk(chunk))
            diagnostics["injected_leaf_count"] = sum(1 for chunk in fitted_chunks if not _is_summary_chunk(chunk))
            diagnostics["injected_chars"] = len(external_context)

    return prompt_engine.get_enhanced_prompt(base_code, external_context=external_context)


def _metadata_float(chunk: KnowledgeChunk, key: str, default: float = 0.0) -> float:
    value = chunk.metadata.get(key)
    if isinstance(value, (int, float)):
        return float(value)
    return default


def _metadata_tokens(chunk: KnowledgeChunk, key: str) -> set[str]:
    value = chunk.metadata.get(key)
    if isinstance(value, str):
        return set(_tokenize(value))
    if isinstance(value, Sequence):
        tokens: set[str] = set()
        for item in value:
            if isinstance(item, str):
                tokens.update(_tokenize(item))
        return tokens
    return set()


def _mean_authority_score(chunks: Sequence[KnowledgeChunk]) -> float:
    if not chunks:
        return 0.0
    return mean(_metadata_float(chunk, "authority_score") for chunk in chunks)


def _mean_topic_alignment(chunks: Sequence[KnowledgeChunk], query_tokens: set[str]) -> float:
    if not chunks or not query_tokens:
        return 0.0

    alignments: list[float] = []
    for chunk in chunks:
        topic_tokens = _metadata_tokens(chunk, "topics")
        topic_tokens.update(_metadata_tokens(chunk, "applicability_tags"))
        topic_tokens.update(_metadata_tokens(chunk, "scenario_tags"))
        if not topic_tokens:
            alignments.append(0.0)
            continue
        union = topic_tokens | query_tokens
        alignments.append(len(topic_tokens & query_tokens) / len(union) if union else 0.0)
    return mean(alignments)


def _source_agreement(chunks: Sequence[KnowledgeChunk]) -> float:
    if len(chunks) <= 1:
        return 1.0 if chunks else 0.0

    topic_sets: list[set[str]] = []
    for chunk in chunks:
        topic_tokens = _metadata_tokens(chunk, "topics")
        topic_tokens.update(_metadata_tokens(chunk, "algorithm_family"))
        topic_sets.append(topic_tokens)

    similarities: list[float] = []
    for left_index in range(len(topic_sets)):
        for right_index in range(left_index + 1, len(topic_sets)):
            left = topic_sets[left_index]
            right = topic_sets[right_index]
            union = left | right
            similarities.append(len(left & right) / len(union) if union else 0.0)
    return mean(similarities) if similarities else 0.0


def _compute_retrieval_confidence(
    *,
    top_score: float,
    top_score_gap: float,
    mean_authority_score: float,
    mean_topic_alignment: float,
    source_agreement: float,
) -> float:
    confidence = (
        (0.35 * max(min(top_score, 1.0), 0.0))
        + (0.15 * max(min(top_score_gap, 1.0), 0.0))
        + (0.20 * max(min(mean_authority_score, 1.0), 0.0))
        + (0.15 * max(min(mean_topic_alignment, 1.0), 0.0))
        + (0.15 * max(min(source_agreement, 1.0), 0.0))
    )
    return max(min(confidence, 1.0), 0.0)


def _tokenize(text: str) -> list[str]:
    return [token.lower() for token in _TOKEN_PATTERN.findall(text)]


def _build_openai_embedding_function(
        model: str,
        base_url: str | None,
        api_key: str | None,
        timeout_seconds: int,
) -> EmbeddingFunction:
    if not api_key or not base_url:
        raise ValueError(
            "Vector retrieval requires embedding API configuration. "
            "Set RAGConfig.embedding_api_key and RAGConfig.embedding_base_url "
            "in implementation/config.py."
        )

    from openai import OpenAI

    client = OpenAI(api_key=api_key, base_url=normalize_openai_base_url(base_url))

    def _embed_texts(texts: list[str]) -> list[list[float]]:
        if not texts:
            return []
        last_error: Exception | None = None
        for max_tokens in _OPENAI_EMBEDDING_RETRY_TOKEN_BUDGETS:
            compacted_texts = [_compact_embedding_input(text, max_tokens=max_tokens) for text in texts]
            try:
                embeddings: list[list[float]] = []
                for start in range(0, len(compacted_texts), _OPENAI_EMBEDDING_MAX_BATCH_SIZE):
                    batch = compacted_texts[start:start + _OPENAI_EMBEDDING_MAX_BATCH_SIZE]
                    response = client.embeddings.create(
                        model=model,
                        input=batch,
                        timeout=timeout_seconds,
                    )
                    embeddings.extend(list(item.embedding) for item in response.data)
                return embeddings
            except Exception as error:
                last_error = error
                if not _is_embedding_input_limit_error(error):
                    raise

        if last_error is not None:
            raise last_error
        return []

    return _embed_texts


def _chunk_text(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    cleaned_text = text.strip()
    if not cleaned_text:
        return []
    if chunk_size <= 0:
        raise ValueError("chunk_size must be positive")
    if chunk_overlap < 0:
        raise ValueError("chunk_overlap must be non-negative")
    if chunk_overlap >= chunk_size:
        raise ValueError("chunk_overlap must be smaller than chunk_size")
    if len(cleaned_text) <= chunk_size:
        return [cleaned_text]

    paragraphs = [paragraph.strip() for paragraph in _PARAGRAPH_SPLIT_PATTERN.split(cleaned_text) if paragraph.strip()]
    if not paragraphs:
        return _sliding_chunks(cleaned_text, chunk_size=chunk_size, chunk_overlap=chunk_overlap)

    chunks: list[str] = []
    current = ""
    for paragraph in paragraphs:
        candidate = f"{current}\n\n{paragraph}".strip() if current else paragraph
        if len(candidate) <= chunk_size:
            current = candidate
            continue

        if current:
            chunks.append(current)
        if len(paragraph) > chunk_size:
            chunks.extend(_sliding_chunks(paragraph, chunk_size=chunk_size, chunk_overlap=chunk_overlap))
            current = ""
            continue

        overlap_text = chunks[-1][-chunk_overlap:] if chunks and chunk_overlap > 0 else ""
        current = f"{overlap_text}\n\n{paragraph}".strip() if overlap_text else paragraph

    if current:
        chunks.append(current)

    return [chunk for chunk in chunks if _is_informative_chunk(chunk)]


def _sliding_chunks(text: str, chunk_size: int, chunk_overlap: int) -> list[str]:
    chunks: list[str] = []
    start = 0
    while start < len(text):
        end = min(len(text), start + chunk_size)
        chunk = text[start:end].strip()
        if chunk:
            chunks.append(chunk)
        if end >= len(text):
            break
        start = end - chunk_overlap
    return chunks


def _is_informative_chunk(text: str, min_density: float = _MIN_INFORMATION_DENSITY) -> bool:
    if not text.strip():
        return False

    alnum_count = sum(1 for char in text if char.isalnum())
    density = alnum_count / max(len(text), 1)
    token_count = len(_tokenize(text))
    return density >= min_density and token_count >= 10


def _hybrid_rerank(query: str, chunks: Sequence[KnowledgeChunk]) -> list[KnowledgeChunk]:
    if not chunks:
        return []

    lexical_scores = [max(chunk.score, 0.0) for chunk in chunks]
    max_lexical = max(lexical_scores) if lexical_scores else 0.0
    query_tokens = _expand_semantic_tokens(_tokenize(query))

    reranked: list[KnowledgeChunk] = []
    for chunk, lexical_score in zip(chunks, lexical_scores):
        chunk_tokens = _expand_semantic_tokens(_tokenize(chunk.text))
        semantic_score = _semantic_overlap(query_tokens, chunk_tokens)
        lexical_norm = lexical_score / max_lexical if max_lexical > 0 else 0.0
        combined = (0.65 * lexical_norm) + (0.35 * semantic_score)
        reranked.append(dataclasses.replace(chunk, score=combined))
    return reranked


def _expand_semantic_tokens(tokens: Sequence[str]) -> set[str]:
    expanded = set(tokens)
    for token in list(expanded):
        expanded.update(_SEMANTIC_HINTS.get(token, set()))
    return expanded


def _semantic_overlap(left_tokens: set[str], right_tokens: set[str]) -> float:
    if not left_tokens or not right_tokens:
        return 0.0
    intersection = len(left_tokens & right_tokens)
    union = len(left_tokens | right_tokens)
    jaccard = intersection / union if union else 0.0

    # Reward partial topic alignment so lexical ties are less brittle.
    topic_hits = [
        1.0 if token in right_tokens else 0.0
        for token in ("capacity", "distance", "demand", "feasibility", "numpy")
        if token in left_tokens
    ]
    topic_alignment = mean(topic_hits) if topic_hits else 0.0
    return (0.8 * jaccard) + (0.2 * topic_alignment)


def _dedup_preserve_order(items: Sequence[str]) -> list[str]:
    seen: set[str] = set()
    ordered: list[str] = []
    for item in items:
        if item in seen:
            continue
        seen.add(item)
        ordered.append(item)
    return ordered


def _compact_embedding_input(text: str, max_tokens: int = _OPENAI_EMBEDDING_MAX_INPUT_TOKENS) -> str:
    stripped = text.strip()
    if not stripped:
        return ""

    tokens = _tokenize(stripped)
    if len(tokens) <= max_tokens:
        return stripped
    return " ".join(tokens[:max_tokens])


def _compact_vector_query(query: str, max_tokens: int = _OPENAI_EMBEDDING_MAX_INPUT_TOKENS) -> str:
    stripped = query.strip()
    if not stripped:
        return ""

    tokens = _tokenize(stripped)
    if len(tokens) <= max_tokens:
        return stripped

    compacted_tokens = _dedup_preserve_order(tokens)
    return " ".join(compacted_tokens[:max_tokens])


def _is_embedding_input_limit_error(error: Exception) -> bool:
    message = str(error).lower()
    return (
        ("413" in message and "token" in message)
        or "input must have less than 512 tokens" in message
        or "input too long" in message
    )
