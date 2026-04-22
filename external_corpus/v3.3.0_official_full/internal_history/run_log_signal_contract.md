---
title: Run Log Signal Contract
date: 2026-04-20
license: repository_source
topics: cvrp,adaptive_search,internal_history
summary: Contract for RUN_METADATA, EVAL_SUMMARY, and RETRIEVAL_DIAGNOSTICS as the authoritative runtime signals.
source_type: run_signal_contract
summary_level: leaf
source_scope: repository
source_paths: implementation/funsearch.py,implementation/sampler.py,implementation/evaluator.py,scripts/compare_rag.py
source_anchor: build_run_metadata,main,Sampler.sample,Evaluator.analyse,parse_run_log
source_id: repo_funsearch_py
distilled_from: implementation/funsearch.py,implementation/sampler.py,implementation/evaluator.py,scripts/compare_rag.py
---

The formal runtime history in this repository is line-oriented. `funsearch.py` prints one `RUN_METADATA` JSON object at run start, `Evaluator.analyse` prints `EVAL_SUMMARY` with valid and total evaluations, and `Sampler.sample` prints `RETRIEVAL_DIAGNOSTICS` when retrieval diagnostics are enabled. `scripts/compare_rag.py` parses those exact lines to recover best scores, valid-eval ratios, retrieval confidence, injected character counts, and other paired-run metrics. For governed history corpus construction, these emitted lines are the primary evidence; prose summaries are secondary and must stay anchored to those raw signals.