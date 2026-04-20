---
title: CVRP Heuristic Playbook
url:
date: 2026-04-19
license: Internal synthesis
topics: cvrp,construction,local_search,metaheuristics
summary: Construction heuristics shape the first route skeleton, while improvement methods rebalance distance and capacity after the first pass.
source_type: survey
authority_score: 0.82
algorithm_family: savings,nearest_neighbor,insertion,tabu_search,alns
complexity_class: O(n^2)
applicability_tags: constructive,global_guidance
scenario_tags: cold_start,clustered_customers,random_customers
evidence_level: survey
summary_level: summary
distilled_from: Corpus Design.md, external_knowledge/cvrp_heuristics.md
anti_pattern: false
---

Use this document as a route-construction map rather than as literal code.

Clarke-Wright style logic rewards pairs of customers that are expensive to visit from the depot separately but cheap to connect directly. That idea is useful even in a single-node scoring function: prefer a customer when it is close to the current node, has a demand that fits remaining capacity, and is likely to keep the route inside the same neighborhood.

Nearest-neighbor logic is strong when the instance is spatially clustered. Its weakness is myopic dead-end behavior, so a good score should not only reward short distance but also reserve space for a few medium-demand nodes that are otherwise hard to serve later.

Insertion heuristics suggest evaluating marginal disruption rather than absolute distance. A node can be attractive when adding it now avoids a long detour or prevents a future capacity deadlock.

Local-search and metaheuristic families matter because they explain what a constructive heuristic should leave behind. Good constructive priorities tend to:
- keep geographically coherent partial routes,
- avoid filling the vehicle too early with awkward demand values,
- leave room for later edge exchanges or relocations.

Practical scoring implication: combine local distance, demand fit, and a coarse cluster-preservation signal instead of optimizing only one term.