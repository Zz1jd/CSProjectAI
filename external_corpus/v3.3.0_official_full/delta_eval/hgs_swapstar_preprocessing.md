---
title: HGS-CVRP SWAP Star Preprocessing
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,delta_evaluation,swap_star
summary: HGS-CVRP makes expensive cross-route SWAP star moves practical by preprocessing insertion costs and pruning route pairs before full evaluation.
source_type: delta_evaluation_reference
summary_level: leaf
authority_score: 0.86
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

HGS-CVRP accelerates cross-route `SWAP*` by preprocessing insertion costs before trying full exchanges. For a pair of routes, the code caches the best admissible insertion positions and then evaluates only a reduced set of composite moves under penalised distance, duration, and load cost. Additional geometric filters skip route pairs whose angular sectors barely overlap, which avoids paying quadratic evaluation cost for clearly poor candidates. The implementation therefore shows a concrete pattern for making expensive neighbourhoods usable inside an iterative search loop.