---
title: Sampler Prompt Enrichment And Dispatch Contract
date: 2026-04-20
license: repository_source
topics: cvrp,orchestration,retrieval,sampling
summary: Contract for how Sampler clamps batch budget, enriches prompts with retrieval context, emits diagnostics, and dispatches samples to evaluators.
source_type: orchestration_contract
summary_level: leaf
source_scope: repository
source_paths: implementation/sampler.py
source_anchor: Sampler.__init__,Sampler.sample
source_id: repo_sampler_py
distilled_from: implementation/sampler.py
---

`Sampler` is the runtime bridge between governed retrieval and the evaluator pool. In `__init__`, it fixes the retrieval knobs that matter at run time: retriever handle, `rag_top_k`, retrieval mode, score threshold, maximum injected context, diagnostics switch, and whether to use the intent query. In `sample`, it first asks `ProgramsDatabase` for a prompt, then clamps the current batch to the remaining global sample budget so one loop iteration cannot overshoot the declared run budget.

Prompt enrichment happens before any LLM call. `Sampler.sample` creates a diagnostics dictionary when retrieval diagnostics are enabled, passes the database prompt through `retrieval.build_enhanced_prompt`, and prints `RETRIEVAL_DIAGNOSTICS` as a JSON line after enrichment. Within the boundary of `implementation/sampler.py`, the governed guarantee is the emission step itself: sampler-side execution preserves whatever enrichment diagnostics were produced for that prompt and writes them into the run log before sampling begins.

After prompt enrichment, `Sampler` draws one LLM continuation per clamped slot, records the per-sample average generation time, increments the shared global sample counter for every emitted sample, and sends each sample to a randomly chosen evaluator together with the originating island id, generated version id, `global_sample_nums`, and `sample_time`. The contract is therefore local but complete: sampler-side retrieval affects the prompt, sampler-side logging preserves that enrichment event, and evaluator dispatch consumes the enriched sample stream under the same budget boundary.