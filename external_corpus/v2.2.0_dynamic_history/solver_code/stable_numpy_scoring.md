---
title: Stable NumPy Scoring Patterns
url:
date: 2026-04-19
license: Internal synthesis
topics: solver_code,numpy,numerical_stability,priority_scoring
summary: Stable heuristics use a small set of vectorized terms with bounded transforms so that score ordering is informative and runtime stays predictable.
source_type: code_snippet
authority_score: 0.89
algorithm_family: vectorized_scoring,constructive
complexity_class: O(n)
applicability_tags: python,numpy,sandbox
scenario_tags: timeout_sensitive,array_api
evidence_level: practice
summary_level: leaf
distilled_from: specification.py, sandbox.py
anti_pattern: false
---

Patterns that tend to survive repeated evaluation:
- additive or affine combinations of distance and demand terms,
- square-root or log-like damping instead of explosive exponents,
- explicit masking for infeasible nodes,
- one final conversion step to turn a cost-like quantity into an argmax-friendly score.

Patterns that often become brittle:
- repeated division by raw distances without clipping,
- large powers that magnify noise,
- mixing signs inconsistently so lower cost and higher score logic collide.

If two expressions provide similar ranking information, choose the simpler one. In this sandbox, stable signal beats algebraic cleverness.