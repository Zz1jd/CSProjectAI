class PromptEngine:
    """
    针对 CVRP 优化的 CoT 增强引擎
    """
    def __init__(self, task_type="CVRP"):
        self.task_type = task_type
        self.cot_guidelines = {
            "CVRP": (
                "CRITICAL LOGIC RULES:\n"
                "1. HIGHER SCORE = HIGHER PRIORITY: The framework uses np.argmax(). To pick the NEAREST node, your final return should usually be negative distance (e.g., return -scores).\n"
                "2. BE CREATIVE: Don't just copy the base code. Try new heuristics: combine distance, demand, and remaining_capacity in unique ways (e.g., use ratios, exponential weights, or cost-to-fill estimates).\n"
                "3. FULL BODY: Start with '    scores = distance_data[current_node].copy()' and end with a return statement.\n"
                "4. NUMPY ONLY: No Python loops. Use np.where, np.clip, np.power for complex logic.\n"
            )
        }

    def get_enhanced_prompt(self, base_code: str) -> str:
        cot_part = self.cot_guidelines.get(self.task_type, "")
        enhanced_prompt = (
            f"You are a world-class Heuristic Algorithm Designer. Your goal is to find a much better priority function than the one provided.\n\n"
            f"### THE CHALLENGE ###\n"
            f"Current best distance is around 1161. Can you redesign the logic to reach < 1000?\n\n"
            f"### CONSTRAINTS ###\n"
            f"{cot_part}\n"
            f"### BASE CODE FOR REFERENCE ###\n"
            f"```python\n"
            f"{base_code}\n"
            f"```\n\n"
            f"### YOUR TASK ###\n"
            f"Write the FULL improved function body. Think about the trade-off between distance and capacity. GO!"
        )
        return enhanced_prompt
