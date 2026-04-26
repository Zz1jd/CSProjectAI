---
title: VeRyPy Savings and Sweep Execution Modes
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,solver_code
summary: VeRyPy exposes classical constructors as callable execution modes, with parallel savings, sequential savings, and sweep variants each preserving the original algorithm family's control flow.
source_type: classical_heuristic_note
summary_level: leaf
authority_score: 0.83
url: https://github.com/yorak/VeRyPy
source_id: official_verypy_repo
distilled_from: https://github.com/yorak/VeRyPy
---

VeRyPy's main interface exposes many classical CVRP heuristics as distinct callable algorithms instead of folding them into one generalized constructor. Parallel savings, sequential savings, sweep, Wren-Holliday sweep, and other variants each keep their own execution pattern, which is consistent with the library's stated purpose of preserving classical heuristic identities rather than normalizing everything into a single meta-framework.

That distinction matters for retrieval because a request for "savings" or "sweep" should not collapse into a generic constructive-method note. Parallel savings begins with one route per customer and repeatedly accepts the best feasible merge; sequential savings grows one emerging route at a time; sweep orders customers by polar angle and then routes by angular contiguity. The governed corpus should preserve those execution modes as separate solver atoms.