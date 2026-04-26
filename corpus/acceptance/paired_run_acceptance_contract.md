---
title: Paired Run Acceptance Contract
date: 2026-04-20
license: repository_source
topics: cvrp,acceptance,paired_eval
summary: Contract for paired-run acceptance based on score win, relative gain, valid-ratio guard, completion guard, and policy compliance.
source_type: acceptance_contract
summary_level: leaf
source_scope: repository
source_paths: scripts/compare_rag.py
source_anchor: evaluate_compare_policy,evaluate_acceptance,build_pair_markdown,evaluate_stage_pair
source_id: repo_compare_rag_py
distilled_from: scripts/compare_rag.py
---

This repository does not accept a RAG candidate only because it once found a better score. `evaluate_acceptance` requires the paired-run policy to be compliant and then checks a stack of guards: same model and budget, optional same-seed enforcement, a real score win, minimum relative gain, valid-eval ratio protection, and sample-completion protection. `run_rag_iteration.py` uses that acceptance object to decide whether a stage-1 candidate may advance to stage 2 and whether a stage-2 result becomes the winner. In practice, acceptance is a runtime contract over matched evidence, not a loose leaderboard rule.