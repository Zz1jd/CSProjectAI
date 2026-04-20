---
title: Constructive-To-Improvement Bridge
url:
date: 2026-04-19
license: Internal synthesis
topics: cvrp,construction,local_search,route_quality
summary: Good constructive priorities leave routes that local-search style moves could refine rather than routes that are already structurally blocked.
source_type: survey
authority_score: 0.84
algorithm_family: savings,insertion,2opt,relocate
complexity_class: O(n^2)
applicability_tags: constructive,route_shaping
scenario_tags: cold_start,mid_capacity,mixed_demands
evidence_level: survey
summary_level: summary
distilled_from: Corpus Design.md, external_knowledge/local_search_moves.md
anti_pattern: false
---

Think of route construction as preparation for later edge cleanup.

Signals that usually survive later improvement:
- customers from the same neighborhood stay near each other,
- very large demands are inserted where residual capacity can still absorb them,
- the route does not zig-zag across distant regions.

Signals that create bad downstream structure:
- greedy jumps to isolated customers too early,
- consuming almost all capacity with medium-value nodes,
- ties broken randomly instead of by residual feasibility.

For a one-step priority function, the useful lesson from classical heuristics is not to imitate full route optimization. It is to rank nodes in a way that preserves geometric coherence and capacity slack.