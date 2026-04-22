---
title: VeRyPy Inter-Route Move Family
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: VeRyPy implements inter-route 2-opt*, one-point, and two-point exchange moves with explicit capacity checks and first-accept or best-accept search strategies.
source_type: operator_reference
summary_level: leaf
authority_score: 0.83
url: https://github.com/yorak/VeRyPy
source_id: official_verypy_repo
distilled_from: https://github.com/yorak/VeRyPy
---

VeRyPy's inter-route operators are written as direct move procedures over route data, not just as labels in a heuristic catalogue. The 2-opt* implementation considers both reconnection patterns across two routes, computes the edge delta for each, and only accepts the move after capacity feasibility checks on the recombined prefixes and suffixes. The two-point move likewise evaluates a cross-route node swap with explicit demand updates for both routes.

These operators also expose acceptance modes through `FIRST_ACCEPT` and `BEST_ACCEPT`, which means the local-search behavior depends on more than the move definition itself. Retrieval should therefore surface the operator plus its acceptance strategy, especially when comparing VeRyPy's educational-style explicit move logic with more integrated local-search engines such as PyVRP or HGS.