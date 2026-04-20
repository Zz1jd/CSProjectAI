---
title: Sandbox Guardrails
url:
date: 2026-04-19
license: Internal reference
topics: api,validator,sandbox,array_api,runtime
summary: The safest prompt context for this repo reminds the model that it operates inside a strict array-based sandbox with no hidden routing helpers.
source_type: evaluator_contract
authority_score: 1.0
algorithm_family: funsearch
complexity_class: O(n) preferred
applicability_tags: strict_signature,sandbox,no_object_model
scenario_tags: timeout_sensitive,multiprocessing,array_api
evidence_level: reference
summary_level: summary
distilled_from: specification.py, sandbox.py, dataset.py
anti_pattern: false
---

Non-negotiable guardrails:
- use the exact `priority()` signature,
- return one numeric score per node,
- do not rely on route classes or validators outside the provided arrays,
- keep complexity near one vectorized pass over the nodes,
- treat invalid and timeout-prone code as worse than modest but stable improvements.

This document is useful as a high-confidence summary node when the retrieved leaf set is noisy.