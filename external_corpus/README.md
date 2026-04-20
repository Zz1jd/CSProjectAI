# Governed CVRP Corpus Family

This directory now contains two distinct states of the corpus migration.

Legacy migration references:
- v2.0.0_foundation: kept on disk for audit only.
- v2.1.0_solver_atoms: kept on disk for audit only.
- v2.2.0_dynamic_history: kept on disk for audit only.
- v2.3.0_full_corpus: kept on disk for audit only.

Active authoritative family:
- v3.0.0_official_foundation: active governed default, with repository-sourced runtime contracts and journal-package slots.
- v3.2.0_dynamic_history: active governed history and adaptive-search contracts from repository code.
- v3.3.0_full_corpus: active governed integration contracts for retrieval, runtime logging, and acceptance.

Future V3 family slots:
- v3.1.0_solver_atoms: not authored yet.

Template rule:
- Files ending with `.md.example` are templates or sample skeletons and are not ingested by the current corpus governance loader.