---
title: OR-Tools Search Strategy for CVRP
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,search_control
summary: The OR-Tools CVRP example separates the capacity model from the search policy by pairing PATH_CHEAPEST_ARC construction with GUIDED_LOCAL_SEARCH improvement under a strict time limit.
source_type: search_policy_note
summary_level: leaf
authority_score: 0.9
url: https://developers.google.com/optimization/routing/cvrp
source_id: official_ortools_cvrp_docs
distilled_from: https://developers.google.com/optimization/routing/cvrp
---

The official OR-Tools CVRP example does not stop at adding a capacity dimension. It also sets a first-solution heuristic and a local-search metaheuristic: `PATH_CHEAPEST_ARC` for initial route construction, `GUIDED_LOCAL_SEARCH` for improvement, and a one-second time limit to keep the search bounded. This is important because the example frames search configuration as a first-class part of the CVRP recipe, not as optional boilerplate around a complete model.

For retrieval and experiment design, this means model notes and search notes should stay separate. Capacity dimensions explain feasibility accumulation, while search-parameter notes explain how OR-Tools actually explores the route space after the model has been built. When the system is selecting context for a routing run, the search-side note is the relevant retrieval atom whenever the question is about solver behavior, runtime, or incumbent improvement rather than capacity semantics.