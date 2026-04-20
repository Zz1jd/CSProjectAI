---
title: Sandbox Runtime Checklist
url:
date: 2026-04-19
license: Internal reference
topics: api,sandbox,validator,performance
summary: The sandbox rewards numerically stable vectorized code and rejects contract violations quickly, so correctness and runtime discipline are part of the search space.
source_type: evaluator_contract
authority_score: 1.0
algorithm_family: funsearch
complexity_class: O(n) preferred
applicability_tags: sandbox,timeout_sensitive,strict_signature
scenario_tags: array_api,multiprocessing
evidence_level: reference
summary_level: summary
distilled_from: sandbox.py, specification.py
anti_pattern: false
---

Checklist before trusting a generated heuristic:
- uses the exact evolved function signature,
- returns a NumPy array with one score per node,
- avoids side effects outside local arrays,
- avoids recursion, blocking I/O, and heavy imports,
- avoids unstable division by tiny numbers,
- can finish under multiprocessing sandbox time limits.

If a heuristic is clever but frequently invalid, it is not competitive in this workflow because invalid samples lower effective evaluation coverage.