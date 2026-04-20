# CS5491
CS5491 artificial intelligence group project

## External Knowledge RAG

This project can inject external CVRP knowledge into the FunSearch prompt.
The active governed corpus now lives under `external_corpus/v3.0.0_official_foundation/` by default. The `v2.*` families stay on disk only as audited migration references.

The corpus governance version is configured from `RAGConfig.corpus_version` in `implementation/config.py`.

Governance artifacts:
- `external_corpus/v3.0.0_official_foundation/manifest.json`
- `external_corpus/v3.0.0_official_foundation/dedup_report.json`

Build or refresh the governance artifacts:

```bash
python scripts/build_corpus_manifest.py
```

Legacy notes under `external_knowledge/` are still available for compatibility and Round 1 ablations.
Legacy V2 audit red-list is written to `results/corpus_audit/legacy_v2_audit.md`.

Starter governed corpus variants:
- `external_corpus/v3.0.0_official_foundation/`

Adaptive source-variant search is intentionally paused until additional governed `v3.*` families are authored.

When enabled in `implementation/config.py`, the sampler retrieves the top-ranked snippets for each prompt and appends them before the base heuristic code, so the LLM can condition on both the current prompt and the external reference notes.

## API Configuration

Model calls are unified through `implementation/llm_client.py`.

`llm_api.py` is kept as a legacy notebook-compatibility entry and is outside the core runtime path.

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
- `CompareScriptConfig` (single-pair compare log/report paths)
- `MultiRoundScriptConfig` (multi-round seeds, rounds, and log/report paths)
- `CompareReportConfig` (fresh baseline-vs-RAG report inputs/outputs)
- `HistoricalReportConfig` (RAG-vs-historical report inputs/outputs)

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

### Single-Pair Compare (baseline once + RAG once)

Use the dedicated one-shot compare script:

```bash
python scripts/run_compare_once.py
```

This workflow is policy-enforced for lightweight A/B checks:
- Exactly one baseline run and one RAG run are executed.
- Compare mode sample budget is capped at 10.
- Fresh logs and a markdown report are written to `results/`.

Generated files include:
- `results/compare_baseline_<timestamp>.log`
- `results/compare_rag_<timestamp>.log`
- `results/RAG_vs_baseline_compare_<timestamp>.md`

To compare two existing logs directly:

```bash
python scripts/compare_rag.py
```

By default this script reads `CompareReportConfig` in `implementation/config.py`.

## Three-Round Multi-Seed Ablation

Script: `scripts/run_multi_seed_compare.py`

Behavior:
- Fixed seeds: `41, 42, 43`
- Round 1: vector retrieval with legacy corpus path and no intent-query upgrade
- Round 2: vector retrieval with the active governed V3 foundation corpus + intent query + threshold/diagnostics
- Round 3: hybrid retrieval + model-upgrade track over the same governed V3 foundation corpus (only if Round 2 did not satisfy aggregate win criteria)
- Early stop: any round meeting aggregate win criteria stops later rounds

Before running, fill `MultiRoundScriptConfig.rounds` in `implementation/config.py` if you want Round 3 upgrade-model execution.

API/embedding credentials for this script are also sourced from `implementation/config.py`.

Run the orchestration:

```bash
python scripts/run_multi_seed_compare.py
```

Generate final consolidated markdown from the latest summary JSON:

```bash
python scripts/aggregate_multi_round_report.py
```
