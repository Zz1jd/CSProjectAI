---
title: Matrix Frontier State Features
url:
date: 2026-04-19
license: Internal synthesis
topics: instance_features,state_representation,capacity,frontier
summary: The highest-value state features in this interface are frontier features derived from the current distance row, feasible set size, and post-choice residual slack.
source_type: feature_engineering
authority_score: 0.83
algorithm_family: constructive,adaptive
complexity_class: O(n)
applicability_tags: state_representation,capacity_sensitive
scenario_tags: tight_capacity,clustered_customers,random_customers
evidence_level: practice
summary_level: leaf
distilled_from: specification.py, external_knowledge/capacity_distance_tradeoffs.md
anti_pattern: false
---

Useful features in the actual interface:
- nearest-feasible distance,
- feasible-set count,
- candidate demand normalized by current slack,
- gap between the current candidate and the next-best local option,
- degree of route saturation after service.

Feature rule: every useful term should either refine local travel ranking or preserve future packing flexibility.