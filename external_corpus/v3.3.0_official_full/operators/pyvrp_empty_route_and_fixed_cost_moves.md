---
title: PyVRP Empty Route and Fixed Cost Moves
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: PyVRP treats empty routes as a special move context because relocate and tail-swap operators can change route usage and therefore fixed-vehicle costs.
source_type: operator_behavior_note
summary_level: leaf
authority_score: 0.86
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/search
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/search
---

PyVRP's local-search engine does not test empty-route moves at the start of the search because doing so too early would encourage unnecessary fleet growth. Instead, it tries them later when a client still cannot be inserted or when subsequent search steps justify exploring additional route usage. This design tells us that empty routes are not just another route object: they represent a controlled escape hatch for diversification and feasibility.

The operator-level tests reinforce the same point. `Exchange10`, `Exchange20`, `Exchange30`, and `SwapTails` all have cases where the delta cost changes because a second route becomes used or an original route becomes empty, which alters fixed vehicle costs. A governed operator note should preserve that behavior so retrieval does not incorrectly frame relocate-style moves as pure arc-distance updates.