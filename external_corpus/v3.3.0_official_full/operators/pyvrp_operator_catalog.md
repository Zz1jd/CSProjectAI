---
title: PyVRP Operator Catalog
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: PyVRP exposes an explicit catalogue of node and route operators rather than treating neighbourhood choice as an unnamed implementation detail.
source_type: operator_reference
summary_level: leaf
authority_score: 0.85
url: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
source_id: official_pyvrp_repo
distilled_from: https://github.com/PyVRP/PyVRP/tree/main/pyvrp/search
---

PyVRP exposes a concrete exported operator family rather than a vague neighbourhood label. The move classes include exchanges of different segment sizes, `SwapTails` for inter-route tail exchange, depot-adjacent clean-up moves, and optional-customer insertion or replacement operators. Because operators are typed as node or route operators, the catalogue separates what can be evaluated locally from what needs route-level context. A governed operator document should preserve that explicit operator inventory so retrieval can suggest move families instead of only saying "do local search".