---
title: Runtime Variant And Logging Contract
date: 2026-04-20
license: repository_source
topics: cvrp,orchestration,config
summary: Contract for single-source runtime configuration, derived corpus roots, RAG overrides, and tee logging.
source_type: orchestration_contract
summary_level: leaf
source_scope: repository
source_paths: implementation/config.py,implementation/funsearch.py,scripts/_runner.py
source_anchor: build_governed_corpus_root,RAGConfig,build_runtime_variant,run_logged_experiment,build_run_metadata
source_id: repo_runtime_config_py
distilled_from: implementation/config.py,implementation/funsearch.py,scripts/_runner.py
---

The runtime configuration chain is intentionally single-source. `RAGConfig` derives `corpus_roots` from `corpus_version`, `build_runtime_variant` applies only the requested overrides on top of a base config, and `run_logged_experiment` tees stdout and stderr into a run log after printing a stable `RUN_LABEL` plus any header fields such as `RUN_MODE` and `RUN_BUDGET`. Because `funsearch.py` also emits `RUN_METADATA`, a governed integration document has to preserve that config-to-log pipeline end to end rather than treating logs as side effects.