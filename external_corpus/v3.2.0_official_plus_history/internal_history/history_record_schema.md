---
title: Search History Record Schema
date: 2026-04-20
license: repository_source
topics: cvrp,adaptive_search,internal_history
summary: Schema for reconstructing governed search-history records from emitted runtime lines rather than from prose summaries.
source_type: internal_history_schema
summary_level: summary
source_scope: repository
source_paths: implementation/funsearch.py,implementation/evaluator.py,implementation/sampler.py,scripts/compare_rag.py,scripts/run_rag_iteration.py
source_anchor: build_run_metadata,Evaluator.analyse,Sampler.sample,parse_run_log,run_iteration
source_id: repo_run_rag_iteration_py
distilled_from: implementation/funsearch.py,implementation/evaluator.py,implementation/sampler.py,scripts/compare_rag.py,scripts/run_rag_iteration.py
---

A governed history record in this repository is assembled from emitted machine signals, not from prose run notes. `RUN_METADATA` defines seed, model, RAG toggle, run mode, and sample budget; best-score lines provide the incumbent trajectory; `EVAL_SUMMARY` gives valid and total counts; and `RETRIEVAL_DIAGNOSTICS` adds top score, score gap, confidence, source counts, and injected characters when retrieval is enabled. The minimal durable schema therefore needs identifiers for the run label and candidate name, control fields for corpus version and retrieval settings, outcome fields for best score and valid ratio, and evidence pointers back to the log path that produced them. Failure labels should be attached only when one of those primary signals is missing or explicitly reports invalid execution.