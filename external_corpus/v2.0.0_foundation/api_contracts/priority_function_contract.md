---
title: FunSearch CVRP Priority Contract
url:
date: 2026-04-19
license: Internal reference
topics: api,validator,runtime,sandbox
summary: The evolved function must satisfy a strict array-based signature and return a numeric score vector with one entry per node.
source_type: evaluator_contract
authority_score: 1.0
algorithm_family: funsearch
complexity_class: O(n) preferred
applicability_tags: sandbox,strict_signature,no_side_effects
scenario_tags: timeout_sensitive,array_api
evidence_level: reference
summary_level: summary
distilled_from: specification.py, sandbox.py
anti_pattern: false
---

Required signature:

`priority(current_node: int, distance_data: np.ndarray, remaining_capacity: int, node_demands: np.ndarray) -> np.ndarray`

Hard constraints for generated code:
- Return a NumPy array of scores with the same length as `node_demands`.
- Higher scores are preferred because the caller uses `argmax` after masking excluded nodes.
- Do not mutate global state or rely on persistent caches that are not rebuilt inside the function.
- Keep the function self-contained and numerically stable. Returning non-numeric values causes sandbox failure.

Evaluator details that matter:
- `distance_data` already has self-loops blocked and depot returns disabled during route construction.
- Capacity feasibility is checked after node selection, so the heuristic should still strongly down-rank infeasible nodes.
- The sandbox accepts only a scalar numeric score from `evaluate()`. If generated code breaks the program contract, the run is marked invalid.

Implementation guidance:
- Prefer vectorized NumPy expressions.
- Avoid Python-level loops over all nodes unless the logic is extremely small.
- Avoid fallback branches that return constant scores for every node, because they erase useful ranking signal.