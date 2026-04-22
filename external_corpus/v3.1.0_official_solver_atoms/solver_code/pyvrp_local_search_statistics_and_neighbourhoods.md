---
title: PyVRP Local Search Statistics and Neighbourhoods
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,solver_code
summary: PyVRP exposes local-search operators, neighbourhood lists, and per-run statistics as explicit interfaces, so neighbourhood control is part of the public search contract rather than hidden implementation state.
source_type: solver_contract
summary_level: leaf
authority_score: 0.86
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
---

PyVRP's `LocalSearch` interface exposes unary operators, binary operators, a configurable neighbourhood structure, and statistics for the most recently improved solution. The C++ and Python bindings both treat those pieces as named interfaces, which means search configuration is explicit: a caller can inspect what operators are active and what neighbourhoods are being explored instead of treating local search as a monolithic black box.

The headers also show that local search enforces structural feasibility before search, updates route state after accepted moves, and can search exhaustively when asked. For retrieval, this makes `LocalSearch` a solver-assembly atom rather than a single operator note. When the system needs context about how a PyVRP search pass is organized, the relevant information is the operator inventory plus the neighbourhood restriction and statistics surfaces, not just one specific move class.