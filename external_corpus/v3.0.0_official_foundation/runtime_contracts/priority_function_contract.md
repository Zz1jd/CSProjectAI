---
title: Priority Function Contract
date: 2026-04-20
license: repository_source
topics: cvrp,api_contracts,priority
summary: Contract for the evolving priority function and how its score vector is consumed.
source_type: runtime_contract
summary_level: summary
source_scope: repository
source_paths: specification.py
source_anchor: priority,select_next_node
source_id: repo_specification_py
distilled_from: specification.py
---

`priority` is the evolving function that the search process modifies. The surrounding program calls it with four inputs: the current node index, a working distance matrix, the remaining vehicle capacity, and the node-demand array. The function must return an `np.ndarray` whose positions stay aligned with node indices, because the next-node selector applies masking and then takes `argmax` over that vector. In other words, this contract is about interface shape and score alignment, not about forcing one particular heuristic formula.
