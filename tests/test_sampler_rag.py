import unittest
from pathlib import Path

from implementation.prompt_engine import PromptEngine
from implementation.retrieval import KnowledgeChunk
from implementation.retrieval import build_enhanced_prompt


class FakeRetriever:
    def retrieve(
            self,
            query: str,
            top_k: int = 3,
        mode: str = "vector",
            score_threshold: float = 0.0,
            diagnostics: dict | None = None,
    ):
        if diagnostics is not None:
            diagnostics["query"] = query
            diagnostics["mode"] = mode
            diagnostics["score_threshold"] = score_threshold
        return [
            KnowledgeChunk(
                source_path=Path("cvrp_notes.md"),
                chunk_index=0,
                text="CVRP heuristics should balance distance, demand, and remaining capacity.",
                score=0.918,
            )
        ][:top_k]


class DiagnosticsRetriever:
    def __init__(self, *, confidence: float, should_skip: bool = False) -> None:
        self._confidence = confidence
        self._should_skip = should_skip

    def retrieve(
            self,
            query: str,
            top_k: int = 3,
            mode: str = "vector",
            score_threshold: float = 0.0,
            diagnostics: dict | None = None,
    ):
        if diagnostics is not None:
            diagnostics["query"] = query
            diagnostics["mode"] = mode
            diagnostics["score_threshold"] = score_threshold
            diagnostics["retrieval_confidence"] = self._confidence
            diagnostics["should_skip_retrieval"] = self._should_skip
        return [
            KnowledgeChunk(
                source_path=Path("summary.md"),
                chunk_index=0,
                text="Summary node: keep capacity feasibility explicit and preserve vectorization.",
                score=0.91,
                metadata={"summary_level": "summary"},
            ),
            KnowledgeChunk(
                source_path=Path("leaf.md"),
                chunk_index=0,
                text="Leaf detail: use np.where penalties so infeasible nodes cannot outrank feasible nodes.",
                score=0.84,
                metadata={"summary_level": "leaf"},
            ),
        ][:top_k]


class SamplerRagTests(unittest.TestCase):
    def test_build_enhanced_prompt_includes_retrieved_context(self) -> None:
        prompt_engine = PromptEngine(task_type="CVRP")
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=prompt_engine,
            retriever=FakeRetriever(),
            top_k=1,
        )

        self.assertIn("CVRP heuristics should balance distance, demand, and remaining capacity.", prompt)
        self.assertIn("cvrp_notes.md", prompt)

    def test_build_enhanced_prompt_emits_retrieval_diagnostics(self) -> None:
        prompt_engine = PromptEngine(task_type="CVRP")
        diagnostics: dict[str, object] = {}
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=prompt_engine,
            retriever=FakeRetriever(),
            top_k=1,
            retrieval_mode="hybrid",
            score_threshold=0.1,
            diagnostics=diagnostics,
        )

        self.assertIn("RETRIEVED EXTERNAL KNOWLEDGE", prompt)
        self.assertEqual(diagnostics["mode"], "hybrid")
        self.assertEqual(diagnostics["score_threshold"], 0.1)
        self.assertIn("query", diagnostics)

    def test_build_enhanced_prompt_skips_low_confidence_retrieval(self) -> None:
        prompt_engine = PromptEngine(task_type="CVRP")
        diagnostics: dict[str, object] = {}
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=prompt_engine,
            retriever=DiagnosticsRetriever(confidence=0.1, should_skip=True),
            top_k=2,
            diagnostics=diagnostics,
        )

        self.assertNotIn("RETRIEVED EXTERNAL KNOWLEDGE", prompt)
        self.assertEqual(diagnostics["applied_retrieval_policy"], "skip")
        self.assertEqual(diagnostics["injected_chars"], 0)

    def test_build_enhanced_prompt_prefers_summary_only_for_medium_confidence(self) -> None:
        prompt_engine = PromptEngine(task_type="CVRP")
        diagnostics: dict[str, object] = {}
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=prompt_engine,
            retriever=DiagnosticsRetriever(confidence=0.35),
            top_k=2,
            diagnostics=diagnostics,
        )

        self.assertIn("Summary node:", prompt)
        self.assertNotIn("Leaf detail:", prompt)
        self.assertEqual(diagnostics["applied_retrieval_policy"], "summary_only")
        self.assertEqual(diagnostics["injected_summary_count"], 1)
        self.assertEqual(diagnostics["injected_leaf_count"], 0)

    def test_build_enhanced_prompt_uses_summary_plus_leaf_for_high_confidence(self) -> None:
        prompt_engine = PromptEngine(task_type="CVRP")
        diagnostics: dict[str, object] = {}
        prompt = build_enhanced_prompt(
            base_code="def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            prompt_engine=prompt_engine,
            retriever=DiagnosticsRetriever(confidence=0.72),
            top_k=2,
            diagnostics=diagnostics,
        )

        self.assertIn("Summary node:", prompt)
        self.assertIn("Leaf detail:", prompt)
        self.assertEqual(diagnostics["applied_retrieval_policy"], "summary_plus_leaf")
        self.assertEqual(diagnostics["injected_summary_count"], 1)
        self.assertEqual(diagnostics["injected_leaf_count"], 1)


if __name__ == "__main__":
    unittest.main()
