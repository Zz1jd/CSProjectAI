---
title: Solver Pattern Signals
url:
date: 2026-04-19
license: Internal synthesis
topics: solver_code,python,numpy,score_composition
summary: Effective code patterns in this project combine a distance backbone with one or two well-scaled demand or slack adjustments under explicit feasibility masking.
source_type: code_snippet
authority_score: 0.9
algorithm_family: vectorized_scoring,constructive
complexity_class: O(n)
applicability_tags: python,numpy,sandbox
scenario_tags: timeout_sensitive,array_api
evidence_level: practice
summary_level: leaf
distilled_from: specification.py, external_knowledge/numpy_routing_patterns.md
anti_pattern: false
---

Preferred score composition pattern:
- start from a distance-like base array,
- damp or amplify demands with a bounded transform,
- apply a feasibility-aware correction,
- preserve score ordering with simple arithmetic.

This pattern is easier to mutate productively than dense branch-heavy code because each term can be tuned independently.