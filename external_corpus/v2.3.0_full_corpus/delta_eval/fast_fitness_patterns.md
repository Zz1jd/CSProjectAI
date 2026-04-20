---
title: Fast Fitness Patterns
url:
date: 2026-04-19
license: Internal synthesis
topics: delta_eval,fast_fitness,complexity,performance
summary: The route-quality signal should be estimated from local edge and slack changes, because full route simulation per candidate is too expensive for repeated FunSearch evaluation.
source_type: optimization_note
authority_score: 0.88
algorithm_family: delta_eval,constructive,local_search
complexity_class: O(n)
applicability_tags: performance,sandbox
scenario_tags: large_instances,timeout_sensitive
evidence_level: reference
summary_level: leaf
distilled_from: Corpus Design.md
anti_pattern: false
---

Fast evaluation heuristics usually rely on local structure:
- edge length relative to the current frontier,
- residual capacity after service,
- whether a node choice creates an obvious outlier edge,
- whether the remaining feasible set collapses too quickly.

The guiding principle is identical to delta evaluation in local search: estimate only what changes materially.