# v3.0.0 Official Foundation

This version is reserved for governed foundation documents and category-1 journal section packages.

Directory rule:
- Official foundation documents can live under topic folders such as `theory/`, `instance_features/`, and `runtime_contracts/`.
- Journal section packages live under `journals/<journal_slug>/<year>_<first_author>_<paper_slug>/`.
- The first governed examples in this repo live under `runtime_contracts/` and come only from repository source files.

Ingestion rule:
- Only files with supported corpus suffixes and valid front matter are ingested.
- Template files use `.md.example` and stay outside the formal manifest.

Starter template package:
- See `journals/_examples/ejor_2024_smith_adaptive_cvrp_study/` for a ready-to-fill sample skeleton.

Current governed sample scope:
- `runtime_contracts/` contains repository-sourced category-7 documents for `priority`, `evaluate`, dataset shape, sandbox execution, and numba-acceleration constraints.
