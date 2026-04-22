---
title: OR-Tools CVRP Capacity Dimension Contract
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,capacity_constraints
summary: OR-Tools models CVRP capacity feasibility with a demand callback and a routing dimension.
source_type: official_theory_note
summary_level: summary
authority_score: 0.90
url: https://developers.google.com/optimization/routing/cvrp
source_id: official_ortools_cvrp_docs
distilled_from: https://developers.google.com/optimization/routing/cvrp
---

OR-Tools treats CVRP as a routing model plus a capacity dimension. A unary demand callback returns the load contribution of each visited node, and `AddDimensionWithVehicleCapacity` accumulates those demands along each route against per-vehicle capacities. The same modelling pattern generalises to multiple cargo types by adding one callback and one dimension per conserved resource. The official example also makes the operational point clear: if total demand cannot be assigned within the declared fleet capacities, the solver must either declare infeasibility or rely on extra modelling devices such as penalties or larger limits.