---
title: Feasible Frontier Features
url:
date: 2026-04-19
license: Internal synthesis
topics: instance_features,capacity,frontier,feasible_nodes
summary: The most useful short-horizon features estimate how many good candidates remain after each feasible move rather than only the immediate distance.
source_type: feature_engineering
authority_score: 0.8
algorithm_family: constructive,lookahead
complexity_class: O(n)
applicability_tags: capacity_sensitive,state_representation
scenario_tags: tight_capacity,mixed_demands
evidence_level: practice
summary_level: leaf
distilled_from: Corpus Design.md, specification.py
anti_pattern: false
---

For each candidate node, the hidden question is not only "is it close now?" but also "what does it leave for the rest of this route?"

Cheap proxies for future flexibility:
- residual capacity after choosing the node,
- number of customers that would still remain feasible,
- whether the chosen node consumes a rare demand size that is hard to pack later,
- whether the node belongs to the current local distance frontier.

A simple heuristic can approximate this without full lookahead by slightly preferring candidates that leave medium slack over candidates that nearly saturate the vehicle.