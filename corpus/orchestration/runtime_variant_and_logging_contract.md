---
title: Runtime Variant And Logging Contract
date: 2026-04-20
license: repository_source
topics: cvrp,orchestration,config
summary: Contract for single-source runtime configuration, fixed corpus root, dataset defaults, RAG overrides, and tee logging.
source_type: orchestration_contract
summary_level: leaf
source_scope: repository
source_paths: implementation/config.py,implementation/funsearch.py,scripts/_runner.py,scripts/run_rag_eval.py
source_anchor: RAGConfig,RuntimeDefaults,run_rag_eval,run_logged_experiment,build_run_metadata
source_id: repo_runtime_config_py
distilled_from: implementation/config.py,implementation/funsearch.py,scripts/_runner.py,scripts/run_rag_eval.py
---

The runtime configuration chain is intentionally single-source. `RAGConfig` now carries one `corpus_root` string, while `RuntimeDefaults.dataset_path` remains the owner of the dataset location and its environment override. `run_rag_eval` builds the fixed RAG variant from the base runtime config, passes the runtime default dataset path into `run_logged_experiment`, and keeps the corpus root in the RAG config. `run_logged_experiment` then tees stdout and stderr into the run log after printing stable header fields such as `RUN_LABEL`, `RUN_MODE`, and `RUN_BUDGET`. Because `funsearch.py` also emits `RUN_METADATA`, this document preserves the config-to-log pipeline end to end instead of treating logs as side effects.
