# Governed CVRP Corpus Family

This directory now contains the active governed corpus family plus temporary V3 migration aliases.

Active authoritative family:
- v3.0.0_official_foundation: active governed default, with repository-sourced runtime contracts and journal-package slots.
- v3.1.0_official_solver_atoms: active governed solver-atom layer sourced from official repositories and docs.
- v3.2.0_official_plus_history: active governed history and adaptive-search contracts from repository code.
- v3.3.0_official_full: active governed full corpus that merges categories 1-7 with retrieval and acceptance contracts.

Legacy V3 aliases kept on disk as migration references:
- v3.2.0_dynamic_history
- v3.3.0_full_corpus

Template rule:
- Files ending with `.md.example` are templates or sample skeletons and are not ingested by the current corpus governance loader.