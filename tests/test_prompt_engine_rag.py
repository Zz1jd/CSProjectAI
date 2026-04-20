import unittest

from implementation.prompt_engine import PromptEngine


class PromptEngineRagTests(unittest.TestCase):
    def test_enhanced_prompt_includes_external_context_section(self) -> None:
        engine = PromptEngine(task_type="CVRP")
        prompt = engine.get_enhanced_prompt(
            "def priority(current_node, distance_data, remaining_capacity, node_demands):\n    return distance_data[current_node]",
            external_context=(
                "### RETRIEVED EXTERNAL KNOWLEDGE ###\n"
                "[1] cvrp_notes.md#chunk-1 (score=0.918)\n"
                "CVRP heuristics should balance distance, demand, and remaining capacity."
            ),
        )

        self.assertIn("### RETRIEVED EXTERNAL KNOWLEDGE ###", prompt)
        self.assertIn("cvrp_notes.md", prompt)
        self.assertIn("balance distance, demand, and remaining capacity", prompt)


if __name__ == "__main__":
    unittest.main()
