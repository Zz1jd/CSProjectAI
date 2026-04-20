---
title: Incremental Reasoning Without Full Simulation
url:
date: 2026-04-19
license: Internal synthesis
topics: delta_eval,fast_fitness,simulation_cost,complexity
summary: Even when the heuristic cannot execute explicit move evaluation, it should still reason from local deltas and avoid expensive route simulation inside the score function.
source_type: optimization_note
authority_score: 0.86
algorithm_family: delta_eval,constructive
complexity_class: O(n)
applicability_tags: performance,sandbox
scenario_tags: large_instances,timeout_sensitive
evidence_level: reference
summary_level: leaf
distilled_from: Corpus Design.md
anti_pattern: false
---

The score function should estimate consequences from local evidence.

Good proxies:
- current travel cost to the candidate,
- residual capacity after service,
- shape of the feasible frontier,
- whether the move likely creates an outlier edge.

Poor proxies:
- reconstructing long hypothetical routes for every candidate,
- nested scanning over all pairs of customers,
- repeatedly sorting the full candidate set when a simple mask and affine transform would suffice.