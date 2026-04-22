---
title: ALNS String Removal Improvement Pattern
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,destroy_repair
summary: The ALNS CVRP example shows that moving from random removal to substring-based removal materially changes solution quality on ORTEC-n242-k12 while keeping the repair side simple.
source_type: operator_pattern_note
summary_level: leaf
authority_score: 0.82
url: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
source_id: official_alns_docs
distilled_from: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
---

In the official ALNS CVRP example, the baseline random-removal plus greedy-repair combination reaches an objective of 135172 on ORTEC-n242-k12, around 9.2 percent above the best known solution of 123750. Replacing the destroy step with a simplified string-removal operator improves the result to 127386, about 2.9 percent above the best known solution, without changing the repair operator. The example therefore isolates the destroy-side neighborhood as the dominant change.

The string-removal routine is structured around a random center customer, nearest-neighbor expansion, and bounded substring extraction from up to a small number of routes. That is different from pure random removal because it deliberately removes geographically related route fragments instead of independent customers. A governed note should preserve that distinction, since retrieval needs to know whether an ALNS candidate is using independent perturbations or route-fragment destruction that better preserves neighborhood structure.