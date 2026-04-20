---
title: Vectorized Priority Pattern Library
url:
date: 2026-04-19
license: Internal synthesis
topics: solver_code,python,numpy,priority_scoring
summary: Efficient evolved heuristics usually assemble a score from a few vectorized terms: distance, feasibility, residual slack, and a mild tie-breaker.
source_type: code_snippet
authority_score: 0.88
algorithm_family: vectorized_scoring,constructive
complexity_class: O(n)
applicability_tags: python,numpy,sandbox
scenario_tags: timeout_sensitive,array_api
evidence_level: practice
summary_level: leaf
distilled_from: specification.py, external_knowledge/numpy_routing_patterns.md
anti_pattern: false
---

A robust pattern for this repo is:
1. start from the current distance row,
2. build a feasibility mask,
3. reward nodes that fit capacity and stay close,
4. penalize infeasible nodes enough that they almost never win,
5. return the negative of a cost-like array or the positive form of a score array consistently.

Useful vectorized terms:
- `distance_term = distance_data[current_node]`
- `demand_term = np.sqrt(np.maximum(node_demands, 0))`
- `slack_term = remaining_capacity - node_demands`
- `feasible_mask = node_demands <= remaining_capacity`

Good engineering habits:
- copy the current distance row before in-place edits,
- use broadcasting and boolean masks instead of Python loops,
- keep each term monotonic so the combined score is easy to reason about.

Bad engineering habits:
- repeated `argsort()` on the whole array inside the same function,
- nested per-node loops,
- score expressions that can create NaN or overflow without guarding denominators.