---
title: OR-Tools Infeasibility and Dropping Visits
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,feasibility
summary: OR-Tools treats infeasible CVRP instances as a search problem that may require time limits or drop-visit penalties rather than as a special-case modeling branch.
source_type: theory_note
summary_level: leaf
authority_score: 0.9
url: https://developers.google.com/optimization/routing/cvrp
source_id: official_ortools_cvrp_docs
distilled_from: https://developers.google.com/optimization/routing/cvrp
---

The OR-Tools CVRP guide explicitly warns that a constrained routing model can have no feasible solution, and that naive solving may then devolve into an exhaustive search. The practical control knobs it recommends are a hard search time limit and penalties for dropping visits. In governed retrieval terms, feasibility handling is therefore part of the solver contract rather than an afterthought added only when runs start failing.

The same note also points out that total demand less than total vehicle capacity is not enough to certify feasibility. Packing all visits into routes is still a constrained combinatorial decision, and OR-Tools links that intuition to the multiple-knapsack family. A useful corpus takeaway is that capacity totals are only a necessary screen: retrieval should still surface route-construction or penalty guidance when a candidate looks infeasible despite globally sufficient fleet capacity.