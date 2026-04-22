---
title: ALNS Initialisation and Acceptance Scaffold
date: 2026-04-20
license: official_site_terms
topics: cvrp,theory,adaptive_search
summary: The official ALNS CVRP example couples a nearest-neighbor seed with roulette-wheel operator selection and record-to-record travel acceptance, making the search scaffold explicit apart from the destroy and repair operators.
source_type: metaheuristic_scaffold
summary_level: leaf
authority_score: 0.82
url: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
source_id: official_alns_docs
distilled_from: https://alns.readthedocs.io/en/latest/examples/capacitated_vehicle_routing_problem.html
---

The ALNS CVRP example makes the search scaffold explicit. It seeds the run with a nearest-neighbor constructor, chooses operators with a roulette-wheel policy, fits `RecordToRecordTravel` from the initial objective with a two percent starting threshold, and stops after a fixed number of iterations. Those pieces are orthogonal to the destroy and repair operators themselves, but they strongly influence how much diversification and acceptance pressure the search experiences.

This separation matters for a governed corpus because operator notes alone are not enough to reconstruct search behavior. A retrieval system that only injects destroy or repair descriptions misses the acceptance schedule and operator-selection logic that explain why a run keeps exploring or converges early. The scaffold should therefore live in the foundation layer as a reusable search-control pattern, not be buried inside a single operator note.