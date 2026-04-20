---
title: Residual Capacity Landscape Features
url:
date: 2026-04-19
license: Internal synthesis
topics: instance_features,capacity,residual_slack,demand_profile
summary: Residual capacity should be modeled as a landscape over the remaining customer set, not only as a hard feasibility cutoff.
source_type: feature_engineering
authority_score: 0.81
algorithm_family: constructive,adaptive
complexity_class: O(n)
applicability_tags: capacity_sensitive,state_representation
scenario_tags: tight_capacity,heterogeneous_demands
evidence_level: practice
summary_level: leaf
distilled_from: Corpus Design.md, external_knowledge/capacity_distance_tradeoffs.md
anti_pattern: false
---

Two nodes may both fit capacity now but have very different downstream effects.

Heuristic signals worth approximating:
- whether selecting the node leaves only tiny residual slack,
- whether the remaining demand histogram becomes awkward,
- whether many feasible nodes remain after the choice,
- whether the node is one of the few customers with a large demand.

This usually argues for a soft residual-capacity bonus instead of a pure feasible-versus-infeasible split.