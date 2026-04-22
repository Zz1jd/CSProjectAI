---
title: HGS Penalty-Bounded Move Pruning
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,delta_eval
summary: Several HGS-CVRP route-improvement moves use a quick lower-bound test on supplemental distance terms versus current route penalties before evaluating full load and duration effects.
source_type: delta_eval_note
summary_level: leaf
authority_score: 0.87
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

In HGS-CVRP, relocate-style moves such as `move2()` and `move3()` first compute simplified distance supports for the affected routes. If the sum of those supports is already no better than the current route penalties, the move is discarded immediately with a comment that the check guarantees the move cannot improve even before additional load and duration constraints are examined. This is a true pruning bound, not just a heuristic ordering trick.

The same style appears in 2-opt* evaluation as well, where a fast cost expression can reject a move before the full penalty-adjusted route state is computed. Retrieval should preserve this pattern because it explains why HGS can evaluate a large move family efficiently: the full penalty model is only applied after a cheaper bound says the move remains plausible.