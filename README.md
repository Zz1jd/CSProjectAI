# CS5491 RAG Notebook Repro

This worktree is a notebook-driven repro for running one fixed RAG configuration against the CVRP FunSearch pipeline.

## Primary Entrypoints

- `funsearch_cvrp_cot_plus_rag.ipynb` runs the Colab workflow.
- `scripts.run_rag_eval.run_rag_eval()` is the Python helper imported by the notebook.

## Runtime Configuration

Edit `implementation/config.py` or use the supported environment variables for API credentials, model settings, retrieval settings, dataset path, and runtime defaults.

The RAG runner uses:

- `ExperimentRunConfig` in `scripts/run_rag_eval.py`
- `ModelSpec` in `scripts/run_rag_eval.py`
- `RuntimeDefaults.dataset_path`, including `FUNSEARCH_DATASET_PATH` overrides, through `main.RUNTIME_DEFAULTS`

## Outputs

Notebook runs write `rag.txt` and `rag_summary.json` under `results/experiments/<timestamp>_<label>_rag/`.

## Notes

- This branch no longer keeps the old staged iteration or two-candidate compare runner.
- Verification should prefer mocked unit tests or low-cost smoke runs over full-budget experiment runs.
