---
title: HGS Split Decoder Variants
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,solver_code
summary: HGS-CVRP exposes split decoding as a separate component with distinct unlimited-fleet and limited-fleet variants, so giant-tour decoding is an independent solver atom rather than an inlined crossover post-step.
source_type: decoder_contract
summary_level: leaf
authority_score: 0.87
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

The HGS code structure names `Split` as one of the main algorithmic classes, and the interface exposes `generalSplit()` together with separate unlimited-fleet and limited-fleet implementations. That organization matters because HGS individuals are represented as giant tours before being decoded into route sets. The decoder is therefore a first-class component between genetic variation and route-level evaluation.

The limited-fleet implementation also contains an explicit acceleration rule: segment extension is bounded by a load cap of `1.5 * vehicleCapacity` while exploring predecessor states. This is not just theoretical split logic; it is a practical decoding constraint that shapes runtime. A governed solver note should preserve the existence of both split variants and the fact that fleet assumptions change the decoding procedure itself.