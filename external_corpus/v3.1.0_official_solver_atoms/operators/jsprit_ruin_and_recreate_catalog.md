---
title: jsprit Ruin And Recreate Catalog
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,ruin_recreate,alns
summary: jsprit makes large-neighbourhood search explicit through a catalogue of ruin strategies coupled with separate insertion modules.
source_type: operator_reference
summary_level: summary
authority_score: 0.82
url: https://github.com/graphhopper/jsprit
source_id: official_jsprit_repo
distilled_from: https://github.com/graphhopper/jsprit
---

jsprit makes large-neighbourhood search explicit through ruin-and-recreate modules. The library exposes several ruin strategies such as random, radial, cluster, string, time-related, and worst removal, each parameterised by relative or absolute removal sizes. Reconstruction is then delegated to insertion strategies, and the framework combines ruin and insertion modules rather than hardwiring one pair. This is useful governed material because it names destroy and repair families in a stable API-oriented way.