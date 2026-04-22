# Governed CVRP Corpus Family

This directory now contains two distinct states of the corpus migration.

Legacy migration references:
- v2.0.0_foundation: kept on disk for audit only.
- v2.1.0_solver_atoms: kept on disk for audit only.
- v2.2.0_dynamic_history: kept on disk for audit only.
- v2.3.0_full_corpus: kept on disk for audit only.

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