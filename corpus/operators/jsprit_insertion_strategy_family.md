---
title: jsprit Insertion Strategy Family
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: jsprit separates best, cheapest, regret, regret-fast, and position-based regret insertions as named factories, so insertion behavior can be weighted and selected independently.
source_type: insertion_reference
summary_level: leaf
authority_score: 0.84
url: https://github.com/graphhopper/jsprit
source_id: official_jsprit_repo
distilled_from: https://github.com/graphhopper/jsprit
---

jsprit exposes insertion strategies through named factories such as `best()`, `cheapest()`, `regretFast()`, `regret(k)`, and position-based regret variants. The factory documentation distinguishes them semantically: best insertion greedily picks the lowest insertion-cost job, cheapest insertion performs true globally cheapest insertion, and regret-based strategies score jobs using the difference between their best and second-best placements together with additional scoring functions.

The implementation also supports concurrent execution, route filtering, scoring customization, and different regret-k settings. That means insertion is not one operator with a few flags; it is an operator family with materially different search behavior. Retrieval should keep those strategies separate so the system can distinguish cheap greedy repair from more exploratory regret-based reinsertion.