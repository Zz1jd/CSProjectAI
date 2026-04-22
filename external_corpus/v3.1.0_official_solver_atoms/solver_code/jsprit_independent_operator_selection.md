---
title: jsprit Independent Operator Selection
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,solver_code
summary: jsprit can select ruin and insertion operators independently with weighted selectors, making operator composition a first-class search configuration rather than a fixed paired strategy list.
source_type: search_composition_note
summary_level: leaf
authority_score: 0.84
url: https://github.com/graphhopper/jsprit
source_id: official_jsprit_repo
distilled_from: https://github.com/graphhopper/jsprit
---

jsprit's builder supports independent operator selection mode, where insertion operators and ruin operators are registered with separate weights and selected independently each iteration. If no custom insertion operators are provided, the algorithm defaults to regret insertion, but when custom operators are present the builder constructs weighted selectors for both insertion and ruin families.

This design is stronger than a hardcoded ruin-and-recreate pair list. It lets the algorithm mix, for example, string ruin with cheapest insertion or radial ruin with regret insertion without encoding every pair as a named strategy. Retrieval should preserve that composition model because it explains how jsprit can vary search behavior by operator weighting instead of only by changing a single monolithic strategy identifier.