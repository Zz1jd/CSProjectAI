---
title: PyVRP Cost Evaluator Delta Proposals
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,delta_eval
summary: PyVRP computes move quality through route proposals passed to CostEvaluator, which can shortcut losing moves but must be exact for any move that is actually applied.
source_type: delta_eval_note
summary_level: leaf
authority_score: 0.88
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/CostEvaluator.h
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/cpp/CostEvaluator.h
---

PyVRP's `CostEvaluator` exposes `deltaCost()` over one or more route proposals instead of forcing each operator to recompute complete route costs manually. The documentation states that delta evaluation may shortcut once it can prove the move will not improve the solution, but that any move an operator decides to apply must have an exact delta value. This is the key contract between move generation and move acceptance.

The local-search implementation makes that contract explicit by asserting `costAfter == costBefore + deltaCost` whenever an improving unary or binary move is applied. The delta evaluator also subtracts the old route's distance, load, duration, and penalty contributions before evaluating the proposals. In retrieval terms, this note explains why PyVRP can support many move classes without duplicating full cost recomputation logic in every operator.