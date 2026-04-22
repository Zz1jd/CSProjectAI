---
title: PyVRP VRPLIB Format Contract
date: 2026-04-20
license: official_site_terms
topics: cvrp,benchmark,instance_features,vrplib
summary: PyVRP documents the VRPLIB fields and defaults that determine how a benchmark file becomes an in-memory instance.
source_type: dataset_reference
summary_level: leaf
authority_score: 0.86
url: https://pyvrp.readthedocs.io/en/stable/dev/supported_vrplib_fields.html
source_id: official_pyvrp_docs
distilled_from: https://pyvrp.readthedocs.io/en/stable/dev/supported_vrplib_fields.html
---

PyVRP documents the exact VRPLIB fields it interprets when loading benchmark files. Core specifications such as `CAPACITY`, `DIMENSION`, `EDGE_WEIGHT_TYPE`, `EDGE_WEIGHT_FORMAT`, and optional `VEHICLES` values determine how an instance is materialised; if `VEHICLES` is absent, PyVRP assumes an effectively unlimited fleet capped by the number of clients. Supported sections include coordinates, demands, depots, explicit distance matrices, service times, and time windows, while unknown sections are ignored. For governed corpus use, this page is valuable because it turns file-format variation into explicit instance features that retrieval can surface before heuristic code is generated.