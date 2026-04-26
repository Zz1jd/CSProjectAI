import tempfile
import unittest
from pathlib import Path
import sys
import types
from unittest import mock

from implementation.prompt_engine import PromptEngine
from implementation.retrieval import build_intent_query
from implementation.retrieval import build_enhanced_prompt
from implementation.retrieval import ExternalKnowledgeIndex
from implementation import retrieval as retrieval_lib


class ExternalKnowledgeIndexTests(unittest.TestCase):
    def test_index_prefers_relevant_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()

            (data_dir / "cvrp_notes.md").write_text(
                "CVRP heuristics should balance distance, demand, and remaining capacity.",
                encoding="utf-8",
            )
            (data_dir / "unrelated.txt").write_text(
                "Pasta recipes and gardening tips.",
                encoding="utf-8",
            )

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            hits = index.retrieve("balance remaining capacity with nearest customer", top_k=1)

            self.assertEqual(hits[0].source_path.name, "cvrp_notes.md")
            self.assertIn("capacity", hits[0].text.lower())

    def test_build_intent_query_includes_task_specific_keywords(self) -> None:
        query = build_intent_query(
            "def priority(current_node, distance_data, remaining_capacity, node_demands):\n"
            "    scores = distance_data[current_node]\n"
            "    return -scores"
        )
        self.assertIn("cvrp", query.lower())
        self.assertIn("remaining_capacity", query.lower())
        self.assertIn("vectorized", query.lower())

    def test_retrieve_applies_score_threshold(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()

            (data_dir / "cvrp_notes.md").write_text(
                "capacity feasibility demand distance tradeoff with vectorized heuristic",
                encoding="utf-8",
            )
            (data_dir / "unrelated.txt").write_text(
                "pizza pasta restaurant kitchen recipe",
                encoding="utf-8",
            )

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            hits = index.retrieve(
                "capacity feasibility distance",
                top_k=5,
                mode="hybrid",
                score_threshold=0.2,
            )

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].source_path.name, "cvrp_notes.md")

    def test_retrieve_rejects_unknown_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()
            (data_dir / "cvrp_notes.md").write_text("capacity distance", encoding="utf-8")

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            with self.assertRaises(ValueError):
                index.retrieve("capacity", top_k=1, mode="auto")

    def test_retrieve_rejects_removed_tfidf_mode(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()
            (data_dir / "cvrp_notes.md").write_text("capacity distance", encoding="utf-8")

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            with self.assertRaisesRegex(ValueError, "Unsupported retrieval mode"):
                index.retrieve("capacity", top_k=1, mode="tfidf")

    def test_vector_mode_requires_explicit_vector_index(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()
            (data_dir / "cvrp_notes.md").write_text("capacity distance", encoding="utf-8")

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            with self.assertRaisesRegex(ValueError, "vector index is not enabled"):
                index.retrieve("capacity", top_k=1, mode="vector")

    def test_vector_retrieve_prefers_semantically_aligned_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()

            (data_dir / "cvrp_notes.md").write_text(
                "capacity feasibility demand distance tradeoff with vectorized heuristic",
                encoding="utf-8",
            )
            (data_dir / "kitchen_notes.txt").write_text(
                "pizza pasta restaurant kitchen recipe",
                encoding="utf-8",
            )

            def fake_embed(texts: list[str]) -> list[list[float]]:
                vectors: list[list[float]] = []
                for text in texts:
                    lowered = text.lower()
                    if any(token in lowered for token in ("capacity", "distance", "demand", "feasibility")):
                        vectors.append([1.0, 0.0, 0.0])
                    else:
                        vectors.append([0.0, 1.0, 0.0])
                return vectors

            index = ExternalKnowledgeIndex.from_paths(
                data_dir,
                enable_vector_index=True,
                embedding_function=fake_embed,
            )
            hits = index.retrieve(
                "capacity distance feasibility",
                top_k=1,
                mode="vector",
            )

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].source_path.name, "cvrp_notes.md")

    def test_embedding_builder_uses_explicit_configuration(self) -> None:
        captured: dict[str, str] = {}

        class _FakeEmbeddings:
            def create(self, **kwargs):
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

        class _FakeOpenAI:
            def __init__(self, api_key: str, base_url: str) -> None:
                captured["api_key"] = api_key
                captured["base_url"] = base_url
                self.embeddings = _FakeEmbeddings()

        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        with mock.patch.dict(sys.modules, {"openai": fake_module}):
            retrieval_lib._build_openai_embedding_function(
                model="text-embedding-3-small",
                base_url="https://embed.example/v1",
                api_key="embed-key",
                timeout_seconds=60,
            )

        self.assertEqual(captured["api_key"], "embed-key")
        self.assertEqual(captured["base_url"], "https://embed.example/v1")

    def test_embedding_builder_compacts_overlong_inputs(self) -> None:
        captured: dict[str, object] = {}

        class _FakeEmbeddings:
            def create(self, **kwargs):
                captured["input"] = kwargs["input"]
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

        class _FakeOpenAI:
            def __init__(self, api_key: str, base_url: str) -> None:
                self.embeddings = _FakeEmbeddings()

        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        long_text = " ".join(f"token{i}" for i in range(700))

        with mock.patch.dict(sys.modules, {"openai": fake_module}):
            embed = retrieval_lib._build_openai_embedding_function(
                model="text-embedding-3-small",
                base_url="https://embed.example/v1",
                api_key="embed-key",
                timeout_seconds=60,
            )
            embed([long_text])

        compacted_input = captured["input"][0]
        self.assertLessEqual(len(compacted_input.split()), 480)

    def test_vector_retrieve_compacts_overlong_query(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()
            (data_dir / "cvrp_notes.md").write_text(
                "capacity feasibility demand distance tradeoff with vectorized heuristic",
                encoding="utf-8",
            )

            captured_queries: list[str] = []

            def fake_embed(texts: list[str]) -> list[list[float]]:
                captured_queries.extend(texts)
                return [[1.0, 0.0, 0.0] for _ in texts]

            index = ExternalKnowledgeIndex.from_paths(
                data_dir,
                enable_vector_index=True,
                embedding_function=fake_embed,
            )
            long_query = " ".join(f"token{i % 20}" for i in range(900))

            hits = index.retrieve(long_query, top_k=1, mode="vector")

            self.assertEqual(len(hits), 1)
            self.assertLessEqual(len(captured_queries[-1].split()), 480)

    def test_embedding_builder_retries_with_smaller_budget_after_413(self) -> None:
        captured_inputs: list[list[str]] = []

        class _FakeEmbeddings:
            def create(self, **kwargs):
                batch = kwargs["input"]
                captured_inputs.append(batch)
                if len(batch[0].split()) > 200:
                    raise RuntimeError("Error code: 413 - input must have less than 512 tokens")
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

        class _FakeOpenAI:
            def __init__(self, api_key: str, base_url: str) -> None:
                self.embeddings = _FakeEmbeddings()

        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        long_text = " ".join(f"token{i}" for i in range(700))

        with mock.patch.dict(sys.modules, {"openai": fake_module}):
            embed = retrieval_lib._build_openai_embedding_function(
                model="text-embedding-3-small",
                base_url="https://embed.example/v1",
                api_key="embed-key",
                timeout_seconds=60,
            )
            result = embed([long_text])

        self.assertEqual(result, [[0.1, 0.2]])
        self.assertGreaterEqual(len(captured_inputs), 2)
        self.assertLessEqual(len(captured_inputs[-1][0].split()), 200)

    def test_embedding_builder_splits_large_batches_to_provider_limit(self) -> None:
        captured_inputs: list[list[str]] = []

        class _FakeEmbeddings:
            def create(self, **kwargs):
                batch = kwargs["input"]
                captured_inputs.append(list(batch))
                return types.SimpleNamespace(
                    data=[
                        types.SimpleNamespace(embedding=[float(int(text.split()[1]))])
                        for text in batch
                    ]
                )

        class _FakeOpenAI:
            def __init__(self, api_key: str, base_url: str) -> None:
                self.embeddings = _FakeEmbeddings()

        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        texts = [f"text {index}" for index in range(58)]

        with mock.patch.dict(sys.modules, {"openai": fake_module}):
            embed = retrieval_lib._build_openai_embedding_function(
                model="text-embedding-3-small",
                base_url="https://embed.example/v1",
                api_key="embed-key",
                timeout_seconds=60,
            )
            result = embed(texts)

        self.assertEqual([len(batch) for batch in captured_inputs], [32, 26])
        self.assertEqual(captured_inputs[0][0], "text 0")
        self.assertEqual(captured_inputs[1][0], "text 32")
        self.assertEqual([embedding[0] for embedding in result], [float(index) for index in range(58)])

    def test_embedding_builder_normalizes_endpoint_style_url(self) -> None:
        captured: dict[str, str] = {}

        class _FakeEmbeddings:
            def create(self, **kwargs):
                return types.SimpleNamespace(data=[types.SimpleNamespace(embedding=[0.1, 0.2])])

        class _FakeOpenAI:
            def __init__(self, api_key: str, base_url: str) -> None:
                captured["api_key"] = api_key
                captured["base_url"] = base_url
                self.embeddings = _FakeEmbeddings()

        fake_module = types.SimpleNamespace(OpenAI=_FakeOpenAI)
        with mock.patch.dict(sys.modules, {"openai": fake_module}):
            retrieval_lib._build_openai_embedding_function(
                model="text-embedding-3-small",
                base_url="embed.example/v1/embeddings",
                api_key="embed-key",
                timeout_seconds=60,
            )

        self.assertEqual(captured["api_key"], "embed-key")
        self.assertEqual(captured["base_url"], "https://embed.example/v1")

    def test_retrieve_emits_source_quality_diagnostics_and_strips_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            data_dir = Path(temporary_dir) / "docs"
            data_dir.mkdir()

            (data_dir / "quality_doc.md").write_text(
                "---\n"
                "title: Quality Doc\n"
                "topics: capacity,feasibility\n"
                "source_type: documentation\n"
                "authority_score: 0.9\n"
                "summary_level: summary\n"
                "---\n\n"
                "capacity feasibility demand distance tradeoff with vectorized heuristic\n",
                encoding="utf-8",
            )

            index = ExternalKnowledgeIndex.from_paths(data_dir)
            diagnostics: dict[str, object] = {}
            hits = index.retrieve(
                "capacity feasibility distance",
                top_k=1,
                mode="hybrid",
                diagnostics=diagnostics,
            )

            self.assertEqual(len(hits), 1)
            self.assertNotIn("title:", hits[0].text.lower())
            self.assertEqual(hits[0].metadata.get("source_type"), "documentation")
            self.assertAlmostEqual(float(hits[0].metadata.get("authority_score") or 0.0), 0.9, places=6)
            self.assertIn("retrieval_confidence", diagnostics)
            self.assertIn("top_score_gap", diagnostics)
            self.assertEqual(diagnostics["unique_source_count"], 1)
            self.assertEqual(diagnostics["selected_source_types"], ["documentation"])

    def test_governed_corpus_skips_files_without_front_matter(self) -> None:
        with tempfile.TemporaryDirectory() as temporary_dir:
            governed_root = Path(temporary_dir) / "corpus" / "v1.9.9"
            governed_root.mkdir(parents=True)
            (governed_root / "raw_note.md").write_text(
                "This file should not be indexed because it has no governed front matter.",
                encoding="utf-8",
            )
            (governed_root / "doc.md").write_text(
                "---\n"
                "title: Governed Doc\n"
                "topics: capacity\n"
                "authority_score: 0.9\n"
                "---\n\n"
                "capacity feasibility vectorized scoring\n",
                encoding="utf-8",
            )

            index = ExternalKnowledgeIndex.from_paths(governed_root)
            hits = index.retrieve("capacity feasibility", top_k=5, mode="hybrid")

            self.assertEqual(len(hits), 1)
            self.assertEqual(hits[0].source_path.name, "doc.md")

    def test_build_enhanced_prompt_reports_context_pruned_when_no_chunk_fits(self) -> None:
        class _TightContextRetriever:
            def retrieve(self, query: str, top_k: int = 3, mode: str = "vector", score_threshold: float = 0.0, diagnostics: dict | None = None):
                if diagnostics is not None:
                    diagnostics["retrieval_confidence"] = 0.8
                    diagnostics["should_skip_retrieval"] = False
                return [
                    retrieval_lib.KnowledgeChunk(
                        source_path=Path("summary.md"),
                        chunk_index=0,
                        text="summary " * 100,
                        score=0.9,
                        metadata={"summary_level": "summary"},
                    )
                ]

        diagnostics: dict[str, object] = {}
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=PromptEngine(task_type="CVRP"),
            retriever=_TightContextRetriever(),
            top_k=1,
            max_context_chars=40,
            diagnostics=diagnostics,
        )

        self.assertNotIn("RETRIEVED EXTERNAL KNOWLEDGE", prompt)
        self.assertEqual(diagnostics["applied_retrieval_policy"], "context_pruned")
        self.assertEqual(diagnostics["injected_chars"], 0)


if __name__ == "__main__":
    unittest.main()
