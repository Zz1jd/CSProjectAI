---
title: ALNS CVRP Destroy And Repair Pattern
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,destroy_repair,alns
summary: The official ALNS CVRP example ties destroy-repair operators to an explicit mutable route state and measurable benchmark behavior.
source_type: official_theory_note
summary_level: leaf
authority_score: 0.88
url: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
source_id: official_alns_docs
distilled_from: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
---

The ALNS CVRP example represents a solution as a list of routes plus an explicit unassigned set, so destroy and repair operators act on a shared mutable state. Random removal selects a fraction of customers, while greedy repair reinserts each removed customer at the cheapest feasible position and opens a new route only when no feasible insertion exists. The example starts from a nearest-neighbour solution, adapts record-to-record travel thresholds with `RecordToRecordTravel.autofit`, and mixes removal operators through roulette-wheel selection. The official benchmark note on ORTEC-n242-k12 shows why this matters for retrieval: the same page ties destroy-repair design to measurable gap reductions rather than presenting operators as isolated code fragments.