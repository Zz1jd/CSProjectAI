---
title: Evaluate Entrypoint Contract
date: 2026-04-20
license: repository_source
topics: cvrp,api_contracts,evaluation
summary: Contract for the evaluate entrypoint, sandbox execution, and numeric scoring requirement.
source_type: runtime_contract
summary_level: summary
source_scope: repository
source_paths: specification.py,sandbox.py,implementation/evaluator.py
source_anchor: evaluate,Sandbox.run,Evaluator.analyse
source_id: repo_evaluator_py
distilled_from: specification.py,sandbox.py,implementation/evaluator.py
---

The runtime expects an `evaluate(test_instances: dict) -> float` entrypoint. The sandbox compiles the generated program, executes `evaluate` on one dataset slice at a time, and accepts only numeric scalar results; non-numeric outputs are treated as failed evaluations. The evaluator aggregates per-test results into a valid-evaluation ratio, so a candidate can lose acceptance even if one run returns a good score. This document therefore captures the execution boundary that the generated program must satisfy before any heuristic quality is even considered.
