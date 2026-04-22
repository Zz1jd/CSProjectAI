# CS5491
CS5491 artificial intelligence group project

## External Knowledge RAG

This project can inject external CVRP knowledge into the FunSearch prompt.
The active governed corpus now lives under `external_corpus/v3.0.0_official_foundation/` by default.

The corpus governance version is configured from `RAGConfig.corpus_version` in `implementation/config.py`.

Governance artifacts:
- `external_corpus/v3.0.0_official_foundation/manifest.json`
- `external_corpus/v3.0.0_official_foundation/dedup_report.json`

Build or refresh the governance artifacts:

```bash
python scripts/build_corpus_manifest.py
```

Starter governed corpus variants:
- `external_corpus/v3.0.0_official_foundation/`
- `external_corpus/v3.1.0_official_solver_atoms/`
- `external_corpus/v3.2.0_official_plus_history/`
- `external_corpus/v3.3.0_official_full/`

Source-variant retrieval now queries `v3.2.0_official_plus_history` and `v3.3.0_official_full` with the raw prompt rather than the priority-only intent query, because these two families store higher-level runtime, history, and integration contracts.

When enabled in `implementation/config.py`, the sampler retrieves the top-ranked snippets for each prompt and appends them before the base heuristic code, so the LLM can condition on both the current prompt and the external reference notes.

## API Configuration

Model calls are unified through `implementation/llm_client.py`.

Only one configuration method is supported now: edit `implementation/config.py`.

Set credentials/endpoints in:
- `APIConfig.base_url`
- `APIConfig.api_key`
- `RAGConfig.embedding_base_url`
- `RAGConfig.embedding_api_key`

`APIConfig.base_url` and `RAGConfig.embedding_base_url` should preferably be OpenAI-compatible base URLs such as `https://host/v1`. The runtime now also normalizes legacy endpoint-style values such as `https://host/v1/chat/completions` and `https://host/v1/embeddings`.

Set runtime behavior in the same file:
- `Config` (model, run_mode, sampling/retrieval controls)
- `RuntimeDefaults` (`dataset_path`, `log_dir`, `max_sample_nums`, compare budget cap)
- `CompareReportConfig` (fresh baseline-vs-RAG report inputs/outputs)

If a field is not set in that file, its dataclass default is used.
No CLI/environment-variable fallback path is used for API/embedding credentials.

Typical run command:

```bash
python main.py
```

To change retrieval mode, model track, RAG switches, or budgets, edit the corresponding dataclass fields in `implementation/config.py`.

## Runtime Modes

### Full Experiment (default)

Run the standard experiment workflow:

```bash
python main.py
```

To compare two existing logs directly:

```bash
python scripts/compare_rag.py
```

By default this script reads `CompareReportConfig` in `implementation/config.py`.

## Two-Stage RAG Iteration

Script: `scripts/run_rag_iteration.py`

This workflow keeps the orchestration in `scripts/` and searches deterministic RAG candidates in two phases:
- query alignment on the control corpus
- density and context refinement on the best control candidate

Experiment-only behavior stays outside `implementation/`: `scripts/_runtime_patches.py` enables generator thinking and interprets `max_context_chars = 0` as "do not truncate retrieved context" for this orchestration.

Current fixed search-space settings are:
- generator thinking enabled
- corpus fixed to `v3.3.0_official_full`
- `hybrid` retrieval, which includes the built-in `_hybrid_rerank` re-scoring step
- no explicit `max_tokens` cap for generation
- `max_context_chars = 0`, which the script layer maps to unlimited retrieval-context injection

Current defaults are defined in `scripts/experiments/rag_iteration_config.py`:
- seed `42`
- stage 1 budget `20`
- stage 2 budget `100`
- relative gain threshold `10%`
- maximum attempts `10`

The candidate space in `scripts/experiments/space.py` now varies query strategy plus density/chunking settings, including `top_k` values `3`, `5`, and `10`, `score_threshold`, `chunk_size`, and `chunk_overlap`.

Run the orchestration:

```bash
python scripts/run_rag_iteration.py
```

Outputs are written under `results/experiments/<timestamp>/`:
- `baseline_stage1.log` and `baseline_stage2.log`
- `attempt_01.json`, `attempt_02.json`, ...
- `attempt_01/stage1_report.md`, `attempt_01/stage2_report.md`, ...
- `summary.json`
- `final_report.md`

The script caches stage-1 and stage-2 baseline logs under `results/experiments/_baseline_cache/` per model and budget, reuses them across repeated runs, records per-attempt progress to stdout, and writes failed attempt details into the attempt JSON instead of silently dropping them.
