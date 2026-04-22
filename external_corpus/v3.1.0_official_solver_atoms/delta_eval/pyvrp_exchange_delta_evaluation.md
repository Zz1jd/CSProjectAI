---
title: PyVRP Exchange Delta Evaluation
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,delta_evaluation
summary: PyVRP treats delta cost as an exact local contract for exchange moves, not as a heuristic proxy.
source_type: delta_evaluation_reference
summary_level: leaf
authority_score: 0.87
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
---

PyVRP does not estimate move quality with heuristic proxies once a candidate move reaches evaluation. Exchange operators build the local route change, ask the cost evaluator for a delta cost, and apply the move only when that exact delta is improving. The search code even checks that cost-after equals cost-before plus the reported delta, which turns delta evaluation into a contract rather than an optimisation hint. For retrieval, this is the key atom: fast search still depends on exact local cost accounting.