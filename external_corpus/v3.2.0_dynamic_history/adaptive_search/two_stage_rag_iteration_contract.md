---
title: Two-Stage RAG Iteration Contract
date: 2026-04-20
license: repository_source
topics: cvrp,adaptive_search,search_control
summary: Contract for query-alignment, density-refinement, source-variant search, and stage-gated promotion to stage 2.
source_type: orchestration_contract
summary_level: summary
source_scope: repository
source_paths: scripts/run_rag_iteration.py,scripts/experiments/rag_iteration_config.py,scripts/experiments/space.py,scripts/_runner.py,scripts/compare_rag.py
source_anchor: run_iteration,_run_candidate_batch,_execute_candidate_attempt,build_query_phase_candidates,build_density_phase_candidates,build_source_phase_candidates,evaluate_acceptance
source_id: repo_run_rag_iteration_py
distilled_from: scripts/run_rag_iteration.py,scripts/experiments/rag_iteration_config.py,scripts/experiments/space.py,scripts/_runner.py,scripts/compare_rag.py
---

`run_iteration` always writes fresh baseline stage-1 and stage-2 logs before evaluating any RAG candidate. The adaptive search then progresses in a fixed order: query-alignment candidates first, density refinement next if there is still no winner, and finally source-variant candidates if attempt budget remains. Stage 2 is never unconditional; it runs only when stage-1 acceptance passes the paired-run policy checks. This makes source variants a controlled last-phase swap over an already validated control strategy, not a free-for-all branch of the search.