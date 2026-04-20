---
title: Atomic Operator Catalog For CVRP
url:
date: 2026-04-19
license: Internal synthesis
topics: operators,relocate,swap,2opt,oropt
summary: Atomic operators explain what route structures are easy to repair later and what structures are expensive to fix once constructed.
source_type: heuristic_operator
authority_score: 0.86
algorithm_family: relocate,swap,2opt,oropt,cross_exchange
complexity_class: O(n^2)
applicability_tags: neighborhood_design,route_improvement
scenario_tags: clustered_customers,long_edges,capacity_pressure
evidence_level: reference
summary_level: leaf
distilled_from: Corpus Design.md, external_knowledge/local_search_moves.md
anti_pattern: false
---

Operator intuition that matters to a constructive priority:

Relocate:
- strong when one customer is clearly misplaced,
- easier if routes have spare capacity and moderate edge lengths.

Swap:
- useful when two customers have complementary demand or geometry,
- harder to exploit if the constructor creates very unbalanced loads.

2-opt and 2-opt*:
- remove edge crossings and long detours,
- benefit from routes that are already locally coherent.

Or-opt and cross-exchange:
- move short customer sequences rather than single nodes,
- work better when the constructor keeps mini-clusters intact.

Scoring implication: reward nodes that extend a coherent frontier instead of creating isolated single-customer detours that later require heavy repair.