---
title: HGS Granular Route Improvement
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: HGS-CVRP runs route-improvement moves under a granular correlated-vertex restriction and skips stale route pairs by remembering when nodes and routes were last modified.
source_type: operator_execution_note
summary_level: leaf
authority_score: 0.86
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

HGS local search does not enumerate all node pairs uniformly. It shuffles node and route visitation order, limits route-improvement move testing to correlated vertices, and only reevaluates a node-route pair when one of the relevant routes has been modified since the last test. That makes the route-improvement phase granular in both the neighborhood and the update schedule.

The move set itself is broad: relocate variants, swap variants, intra-route 2-opt, and inter-route 2-opt* all sit inside the same search loop. Empty-route moves are withheld until later loops to avoid inflating fleet size too early. This governed note is useful when retrieval needs to explain why HGS local search behaves like a filtered move engine rather than like a blind enumeration over every pair of route positions.