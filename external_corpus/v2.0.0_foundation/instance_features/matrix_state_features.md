---
title: Matrix-Derived State Features For Priority Scoring
url:
date: 2026-04-19
license: Internal synthesis
topics: instance_features,geometry,capacity,state_representation
summary: In this project the evolved heuristic sees a distance matrix row and demand vector, so useful features must be derived from matrix structure rather than raw coordinates.
source_type: feature_engineering
authority_score: 0.79
algorithm_family: constructive,adaptive
complexity_class: O(n)
applicability_tags: state_representation,capacity_sensitive
scenario_tags: clustered_customers,random_customers,depot_central
evidence_level: practice
summary_level: leaf
distilled_from: Corpus Design.md, specification.py
anti_pattern: false
---

The evolved `priority()` function does not receive coordinates, route objects, or explicit cluster labels. It receives:
- the current node index,
- one row-accessible view of the working distance matrix,
- remaining capacity,
- the full demand vector.

Features that are safe and cheap in this interface:
- normalized demand: `node_demands / max(node_demands)`;
- feasible mask: `node_demands <= remaining_capacity`;
- local distance rank from `distance_data[current_node]`;
- distance gap between the nearest few feasible candidates;
- remaining-capacity slack after visiting each candidate;
- count of feasible customers left.

Features that are not directly available here:
- raw customer coordinates,
- explicit route load history,
- exact depot-return cost after the working matrix blocks depot moves.

Design rule: prefer features that can be computed for every node with one or two vectorized passes. If a feature needs repeated sorting or nested loops, it is usually too expensive for the sandbox budget.