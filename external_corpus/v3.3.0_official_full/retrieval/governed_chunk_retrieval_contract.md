---
title: Governed Chunk Retrieval Contract
date: 2026-04-20
license: repository_source
topics: cvrp,retrieval,governed_corpus
summary: Contract for governed chunk scoring, summary and leaf selection, skip policy, and context pruning.
source_type: retrieval_contract
summary_level: summary
source_scope: repository
source_paths: implementation/retrieval.py
source_anchor: ExternalKnowledgeIndex.retrieve,build_enhanced_prompt,_select_chunks_for_injection,_mean_authority_score,_requires_governed_front_matter
source_id: repo_retrieval_py
distilled_from: implementation/retrieval.py
---

Retrieval is not a raw top-k dump. `ExternalKnowledgeIndex.retrieve` ranks chunks, filters by score threshold, and records diagnostics such as selected source types, summary levels, authority scores, retrieval confidence, and `should_skip_retrieval`. `build_enhanced_prompt` then applies a second policy layer that may inject only a summary chunk, a summary-plus-leaf pair, two top chunks, or nothing at all if confidence is too low or context is pruned away. Within this runtime, governed front matter is operational metadata: `summary_level`, `authority_score`, and related fields directly influence what context can reach the LLM.