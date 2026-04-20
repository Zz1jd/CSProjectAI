---
title: FunSearch Evolution Memory
url:
date: 2026-04-19
license: Internal synthesis
topics: internal_history,elites,feedback,search_memory
summary: High-scoring mutations in this project usually keep the score vector simple, monotonic, and strongly capacity-aware while preserving enough distance signal to avoid random tie-breaking.
source_type: internal_history
authority_score: 0.92
algorithm_family: funsearch,vectorized_scoring
complexity_class: O(n)
applicability_tags: search_memory,mutation_guidance
scenario_tags: timeout_sensitive,array_api
evidence_level: project_history
summary_level: leaf
distilled_from: results/, specification.py
anti_pattern: false
---

Observed positive patterns for this repo:
- vectorized arithmetic with one or two interpretable adjustments,
- explicit treatment of infeasible nodes,
- demand transforms such as square-root damping,
- no dependence on hidden state or helper objects.

Observed weak patterns:
- overfitting to a single term like distance only,
- formulas so aggressive that nearly all feasible nodes receive similar scores,
- logic that behaves like a constant ranking once masking is applied.

Use history as a bias, not as a template. The goal is to preserve proven runtime discipline while still changing ranking behavior.