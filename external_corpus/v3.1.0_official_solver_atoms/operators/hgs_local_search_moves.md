---
title: HGS-CVRP Local Search Move Set
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators,hgs
summary: HGS-CVRP engineers a fixed move set with penalised cost evaluation and specialised handling for expensive cross-route exchanges.
source_type: operator_reference
summary_level: leaf
authority_score: 0.86
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

HGS-CVRP's local search kernel enumerates a fixed move set instead of relying on generic callbacks. The code distinguishes relocate, swap, intra-route 2-opt, inter-route 2-opt*, and `SWAP*`, then evaluates these moves under penalised cost that includes load and duration excess. `SWAP*` is not treated as a brute-force cross product: the implementation first preprocesses promising insertion positions and filters route pairs with geometric sector-overlap tests. This makes the repository a strong source for how operator engineering and delta evaluation interact in a competitive CVRP solver.