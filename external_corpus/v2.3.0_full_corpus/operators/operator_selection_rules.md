---
title: Operator Selection Rules
url:
date: 2026-04-19
license: Internal synthesis
topics: operators,relocate,swap,2opt,route_structure
summary: A constructive score should prefer moves that leave the route close to the neighborhoods targeted by relocate, swap, and 2-opt style repair operators.
source_type: heuristic_operator
authority_score: 0.88
algorithm_family: relocate,swap,2opt,oropt,cross_exchange
complexity_class: O(n^2)
applicability_tags: neighborhood_design,route_improvement
scenario_tags: long_edges,clustered_customers,mixed_demands
evidence_level: reference
summary_level: summary
distilled_from: external_knowledge/local_search_moves.md
anti_pattern: false
---

Route-shaping rules of thumb:
- avoid isolated outlier customers unless demand pressure forces them,
- keep short customer chains contiguous,
- treat near-capacity saturation as a strategic choice rather than a default.

These rules are small enough to guide mutation while still being specific about what later operators can fix.