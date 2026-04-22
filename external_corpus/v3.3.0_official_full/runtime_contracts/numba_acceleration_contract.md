---
title: Numba Acceleration Contract
date: 2026-04-20
license: repository_source
topics: cvrp,api_contracts,numba_acceleration
summary: Contract for how the runtime injects numba.jit and what that implies for evolved priority code.
source_type: runtime_contract
summary_level: leaf
source_scope: repository
source_paths: sandbox.py,implementation/evaluator_accelerate.py
source_anchor: add_numba_decorator,Sandbox._compile_and_run_function
source_id: repo_evaluator_accelerate_py
distilled_from: sandbox.py,implementation/evaluator_accelerate.py
---

When sandbox acceleration is enabled, the runtime rewrites the generated program before execution: it inserts `import numba` if needed and appends `@numba.jit(nopython=True)` to the evolved function. This means candidate code is judged under a stricter execution model than plain Python, especially for NumPy features that numba does not support. The practical contract is not “always use numba syntax”; it is “avoid constructs that break `nopython=True`, because the sandbox may decorate the evolved function automatically before calling `evaluate`.”