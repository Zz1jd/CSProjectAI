---
title: Dataset Instance Contract
date: 2026-04-20
license: repository_source
topics: cvrp,api_contracts,dataset
summary: Contract for how CVRP instances are loaded and which keys the evaluator reads.
source_type: runtime_contract
summary_level: leaf
source_scope: repository
source_paths: dataset.py,specification.py
source_anchor: load_cvrp_dataset,evaluate
source_id: repo_dataset_py
distilled_from: dataset.py,specification.py
---

The dataset loader reads `.vrp` files through `vrplib` and stores them under the `B` split keyed by instance name. Downstream evaluation code expects each instance dictionary to expose `capacity`, `demand`, and `edge_weight`, because those keys are passed directly into `vehicle_routing`. A governed category-7 document should preserve that exact instance shape instead of inventing higher-level object models that the sandbox never sees.
