---
title: Failure Mode Catalog
url:
date: 2026-04-19
license: Internal synthesis
topics: internal_history,failures,anti_patterns,sandbox
summary: Common low-value mutations break the array contract, destroy score ordering, or add complexity that the sandbox cannot amortize.
source_type: internal_history
authority_score: 0.91
algorithm_family: funsearch,anti_pattern
complexity_class: O(n^2) or worse
applicability_tags: failure_avoidance,mutation_guidance
scenario_tags: timeout_sensitive,array_api
evidence_level: project_history
summary_level: leaf
distilled_from: results/, sandbox.py, specification.py
anti_pattern: true
---

Avoid these failure patterns:
- returning a scalar or Python list instead of a NumPy score vector,
- formulas that assign nearly identical scores to every feasible node,
- heavy nested loops or repeated full-array sorting,
- assumptions about route objects or helper methods that do not exist,
- unstable divisions that create NaN or inf values.

This document should down-rank prompt ideas that look sophisticated but repeatedly produce invalid or blank evaluations.