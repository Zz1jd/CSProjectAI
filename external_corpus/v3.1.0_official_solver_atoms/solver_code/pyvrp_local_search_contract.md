---
title: PyVRP Local Search Contract
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,local_search
summary: PyVRP exposes local improvement as a configurable engine built from neighbour lists and registered operators.
source_type: solver_code_reference
summary_level: summary
authority_score: 0.85
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
---

PyVRP's search layer treats local improvement as a configurable engine rather than one hard-coded neighbourhood. A `LocalSearch` object is built from instance data, neighbourhood lists, and a random generator, after which unary and binary operators are registered explicitly. The engine then explores only supported moves on candidate neighbour lists, applies improving changes to a current solution, and keeps simple move statistics for diagnostics. For corpus purposes, this is a solver-code contract: neighbourhood restriction and operator registration are first-class design choices, not implementation noise.