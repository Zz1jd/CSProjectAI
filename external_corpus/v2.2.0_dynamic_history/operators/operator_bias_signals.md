---
title: Operator Bias Signals
url:
date: 2026-04-19
license: Internal synthesis
topics: operators,route_structure,relocate,2opt,swap
summary: The current score should bias route structure toward shapes that common improvement operators can exploit with small local changes.
source_type: heuristic_operator
authority_score: 0.85
algorithm_family: relocate,swap,2opt,cross_exchange
complexity_class: O(n^2)
applicability_tags: neighborhood_design,route_improvement
scenario_tags: long_edges,clustered_customers,capacity_pressure
evidence_level: reference
summary_level: leaf
distilled_from: external_knowledge/local_search_moves.md
anti_pattern: false
---

Think of the scoring function as encoding a bias toward operator-friendly route geometry.

Useful biases:
- keep short chains of nearby customers together,
- avoid single-node excursions that create long rejoin edges,
- preserve capacity slack so relocate and swap remain feasible.

A candidate is often better when it creates a route segment that can be refined by a single relocate or 2-opt step rather than a segment that would require global reconstruction.