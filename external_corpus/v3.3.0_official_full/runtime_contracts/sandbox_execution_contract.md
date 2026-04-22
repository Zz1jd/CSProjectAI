---
title: Sandbox Execution Contract
date: 2026-04-20
license: repository_source
topics: cvrp,api_contracts,sandbox
summary: Contract for per-instance sandbox execution, timeout handling, and numeric result validation.
source_type: runtime_contract
summary_level: summary
source_scope: repository
source_paths: sandbox.py,implementation/evaluator.py
source_anchor: Sandbox.run,Sandbox._compile_and_run_function,Evaluator.analyse
source_id: repo_sandbox_py
distilled_from: sandbox.py,implementation/evaluator.py
---

The runtime does not execute the evolved program inline inside the evaluator loop. `Sandbox.run` extracts one dataset slice from `inputs[test_input]`, launches a separate process, and joins it with the configured timeout. If the worker times out, crashes, leaves the queue empty, or returns a non-numeric value, the sandbox reports `(None, False)` and that test instance does not count as a valid evaluation. A governed document therefore has to preserve three facts together: execution is per-instance, timeouts are hard failures, and only scalar `int` or `float` outputs are accepted.