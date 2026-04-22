---
title: PyVRP SwapTails as 2-opt Star
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: PyVRP's SwapTails operator is the inter-route 2-opt* move, implemented with explicit fixed-cost handling for routes that become empty or non-empty after the exchange.
source_type: operator_reference
summary_level: leaf
authority_score: 0.87
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/search/SwapTails.h
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/search/SwapTails.h
---

PyVRP documents `SwapTails` as the move that replaces arcs `U -> n(U)` and `V -> n(V)` by `U -> n(V)` and `V -> n(U)`. The header note explicitly states that this is the VRP literature's 2-opt* operator. That matters because retrieval can map a generic request for inter-route edge exchange directly to the concrete class that implements it.

The implementation also tracks route fixed costs when the move changes whether a route is empty. If a currently empty route becomes non-empty, the fixed vehicle cost is added; if a route becomes empty, the fixed cost is removed. This makes `SwapTails` more than a pure distance-based edge reconnection, and explains why the operator appears in tests about empty routes, multiple depots, and heterogeneous profiles rather than only in geometric move examples.