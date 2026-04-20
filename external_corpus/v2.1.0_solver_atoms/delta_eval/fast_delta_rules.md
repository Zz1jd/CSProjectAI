---
title: Fast Delta Rules For Route Changes
url:
date: 2026-04-19
license: Internal synthesis
topics: delta_eval,complexity,fast_fitness,edges
summary: Good routing logic compares local edge changes instead of recomputing an entire route whenever only a few arcs differ.
source_type: optimization_note
authority_score: 0.87
algorithm_family: delta_eval,2opt,swap
complexity_class: O(1) to O(k)
applicability_tags: performance,local_search
scenario_tags: long_routes,large_instances
evidence_level: reference
summary_level: leaf
distilled_from: Corpus Design.md
anti_pattern: false
---

The fast-evaluation principle is simple: if only a few edges change, only those edges need to be re-scored.

Examples:
- Relocate changes two cut edges and two reconnect edges.
- Swap changes the incident edges around two customers.
- 2-opt replaces two edges and reverses a segment.

For this project, the evolved function does not execute these moves directly, but the same performance lesson still applies. A good `priority()` should estimate route quality from local structure and vectorized summaries, not by simulating long future routes.