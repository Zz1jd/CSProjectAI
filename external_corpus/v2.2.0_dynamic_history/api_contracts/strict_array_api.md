---
title: Strict Array API For Evolved Heuristics
url:
date: 2026-04-19
license: Internal reference
topics: api,validator,array_api,sandbox
summary: The evaluator exposes arrays and scalars only, so retrieval should discourage any generated code that assumes route objects, class methods, or hidden helper APIs.
source_type: evaluator_contract
authority_score: 1.0
algorithm_family: funsearch
complexity_class: O(n) preferred
applicability_tags: strict_signature,array_api,no_object_model
scenario_tags: timeout_sensitive,multiprocessing
evidence_level: reference
summary_level: summary
distilled_from: specification.py, sandbox.py, dataset.py
anti_pattern: false
---

This repo does not expose `Route`, `Solution`, or `Node` classes to the evolved heuristic.

Available information is limited to arrays already passed into the evolved function. Therefore generated code should not assume helper methods such as feasibility checks, route insertion routines, or stateful caches.

Validator mindset:
- respect the exact function signature,
- keep output length aligned with node count,
- make infeasible nodes unattractive,
- avoid patterns that depend on unavailable environment abstractions.