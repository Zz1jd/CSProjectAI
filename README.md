# CS5491 — CVRP FunSearch Notebooks (Execution Records)

This repository contains the execution records of two Jupyter notebooks that run DeepMind-style FunSearch on the Capacitated Vehicle Routing Problem (CVRP). The goal is to evolve a priority-scoring function used inside a fixed greedy route-construction template, rather than building a full solver from scratch.

## Notebook ↔ Log Mapping

- `funsearch_cvrp_original.ipynb` → `INFOabsl_original.txt`
- `funsearch_cvrp_cot.ipynb` → `INFOabsl_cot.txt`

The `INFOabsl_*.txt` files are exported console logs from the corresponding notebook runs. They capture:
- per-island “best score” updates (multi-island evolution),
- the current evaluated `priority(...)` function body,
- the score reported by the evaluation function.

## What Each Notebook Does

### `funsearch_cvrp_original.ipynb`

- A baseline FunSearch workflow for CVRP.
- Implements an LLM interface, sandboxed execution, a CVRP greedy template, and an evaluation loop on CVRPLib instances (primarily setB).
- Produces absl-style logs during evolution (saved as `INFOabsl_original.txt`).

### `funsearch_cvrp_cot.ipynb`

- An enhanced version of the baseline notebook that strengthens prompt guidance (Chain-of-Thought style instructions), improves code extraction robustness, and encourages vectorized NumPy expressions (optionally with Numba acceleration).
- Produces absl-style logs during evolution (saved as `INFOabsl_cot.txt`).

## Data and Core Implementation

- CVRPLib instances and best-known solutions are under `cvrplib/setA` and `cvrplib/setB` (`.vrp` / `.sol`).
- The core FunSearch-style components live in `implementation/` (e.g., evolution loop, program database, evaluator, prompt engine).

## Reproducing the Runs (High-Level)

These notebooks were originally written to be run in a notebook environment (e.g., Google Colab). To reproduce:
- Open either notebook and run cells top-to-bottom.
- Install notebook dependencies when prompted (e.g., `vrplib`; some notebooks also use `pandas` / `matplotlib`).
- Configure the LLM API endpoint and credentials via environment variables or notebook secrets (do not hard-code or commit keys).
