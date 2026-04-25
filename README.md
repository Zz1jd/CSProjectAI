# CS5491 Compare-Only Repro

This worktree is a minimal compare-only repro focused on baseline vs two fixed RAG candidates plus two single-RAG smoke notebooks.

## Primary Entrypoints

Full compare run:

```bash
python scripts/run_rag_compare_repro_20260420_133019.py
```

Single-RAG smoke notebooks:

- `notebook_rag_smoke_v32_dynamic_history.ipynb`
- `notebook_rag_smoke_v33_full_corpus.ipynb`

Both notebooks default to a low-cost smoke budget and do not run baseline.

## Runtime Configuration

Edit `implementation/config.py` for API credentials, model settings, retrieval settings, dataset path, and runtime defaults.

The compare runner uses:

- `CompareRunConfig` in `scripts/run_rag_compare_repro_20260420_133019.py`
- `build_smoke_compare_config()` for low-cost verification
- `build_repro_candidate_space()` for the two fixed RAG candidates

## Outputs

Compare runs write into `results/experiments_repro_20260420_133019/`.

The retained compare artifact for this worktree is:

- `results/experiments_repro_20260420_133019/20260425_125359_repro_gpt_3_5_turbo_20260420_compare/`

Single-RAG notebook runs write candidate-specific summary JSON files under the same results root.

## Notes

- This worktree no longer keeps the old iteration orchestration or corpus-governance docs/tooling.
- Verification should prefer low-cost smoke runs over full-budget runs.
