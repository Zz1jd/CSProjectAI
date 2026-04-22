---
title: VeRyPy Classical Heuristics Catalog
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,classical_heuristics
summary: VeRyPy collects a broad catalogue of named CVRP construction and local-search heuristics in one benchmark-oriented codebase.
source_type: solver_code_reference
summary_level: summary
authority_score: 0.81
url: https://github.com/yorak/VeRyPy
source_id: official_verypy_repo
distilled_from: https://github.com/yorak/VeRyPy
---

VeRyPy is valuable because it exposes a broad catalogue of classical CVRP heuristics behind one benchmark-oriented codebase. The project collects construction methods such as parallel savings and sweep alongside local-search operators such as 2-opt, 3-opt, relocate, exchange, one-point move, two-point move, and 2-opt*. That makes it a useful governed source for operator naming and historical algorithm coverage even when a modern solver does not reuse its exact implementation. The important solver-atom lesson is that many apparently new move families are stable, named building blocks with well-known classical counterparts.