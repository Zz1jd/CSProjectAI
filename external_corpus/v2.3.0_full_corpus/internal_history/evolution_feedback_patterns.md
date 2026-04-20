---
title: Evolution Feedback Patterns
url:
date: 2026-04-19
license: Internal synthesis
topics: internal_history,feedback,elites,mutation_patterns
summary: Productive mutations in this repo usually preserve vectorized structure and change only a few interpretable ranking terms at a time.
source_type: internal_history
authority_score: 0.93
algorithm_family: funsearch,vectorized_scoring
complexity_class: O(n)
applicability_tags: search_memory,mutation_guidance
scenario_tags: timeout_sensitive,array_api
evidence_level: project_history
summary_level: leaf
distilled_from: results/, specification.py
anti_pattern: false
---

Positive mutation patterns:
- add one capacity-aware correction to a stable distance baseline,
- soften a hard penalty into a graded penalty,
- replace loop-heavy logic with one vectorized pass,
- keep score monotonic so ranking changes are interpretable.

These patterns matter because adaptive search benefits from corpora that reinforce stable mutation directions rather than wide but noisy prompt context.