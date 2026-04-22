---
title: VeRyPy Sweep Improvement Pipeline
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: VeRyPy's Wren-Holliday sweep variant layers inspect, single-customer improvement, delete, and pair phases on top of the angular sweep constructor instead of stopping at raw route construction.
source_type: operator_pipeline_note
summary_level: leaf
authority_score: 0.82
url: https://github.com/yorak/VeRyPy
source_id: official_verypy_repo
distilled_from: https://github.com/yorak/VeRyPy
---

The base VeRyPy sweep implementation clusters customers by polar angle and can try multiple directions and start nodes, but the Wren-Holliday variant goes further by running an explicit improvement pipeline. It applies route inspection with 2-opt, a single-customer phase that can relocate customers across routes, and additional delete or pair phases when the problem is small enough or the route state warrants it.

This pipeline matters because it shows that classical sweep is not only a clustering scheme in VeRyPy. The library preserves the historical post-optimization logic as a sequence of named phases, including cases where an empty route is temporarily appended to allow improvement. For governed retrieval, that makes Wren-Holliday sweep a richer operator program than a simple "sort by angle and fill until capacity" summary would suggest.