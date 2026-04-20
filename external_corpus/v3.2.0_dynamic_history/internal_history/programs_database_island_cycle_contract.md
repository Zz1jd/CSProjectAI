---
title: ProgramsDatabase Island Cycle Contract
date: 2026-04-20
license: repository_source
topics: cvrp,adaptive_search,internal_history
summary: Contract for island-scoped history, score signatures, cluster sampling, and reset behavior.
source_type: internal_history_contract
summary_level: summary
source_scope: repository
source_paths: implementation/programs_database.py,implementation/config.py
source_anchor: _get_signature,ProgramsDatabase.register_program,ProgramsDatabase.reset_islands,Island.get_prompt,ProgramsDatabaseConfig
source_id: repo_programs_database_py
distilled_from: implementation/programs_database.py,implementation/config.py
---

The repository does not store search history as free-form notes. `ProgramsDatabase` keeps separate islands, groups evaluated programs by a canonical signature built from sorted per-test scores, and samples prompt exemplars from clusters with a temperature schedule controlled by `ProgramsDatabaseConfig`. When `reset_period` is reached, the weaker half of islands is rebuilt and reseeded from strong islands. A governed history document therefore has to preserve the concrete data flow of islands, signatures, clusters, and resets instead of retelling search progress as narrative summary text.