# Legacy V2 Corpus Audit

- Legacy versions scanned: v2.*
- Documents scanned: 24
- Flagged documents: 24

## Reason Counts
- design_doc_distillation: 11
- internal_synthesis_license: 20
- missing_source_locator: 24

## Flagged Documents
| Path | Reasons | License | Distilled From |
| --- | --- | --- | --- |
| v2.0.0_foundation/api_contracts/priority_function_contract.md | missing_source_locator | Internal reference | specification.py, sandbox.py |
| v2.0.0_foundation/instance_features/matrix_state_features.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, specification.py |
| v2.0.0_foundation/theory/classic_heuristic_playbook.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/cvrp_heuristics.md |
| v2.1.0_solver_atoms/api_contracts/sandbox_runtime_checklist.md | missing_source_locator | Internal reference | sandbox.py, specification.py |
| v2.1.0_solver_atoms/delta_eval/fast_delta_rules.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md |
| v2.1.0_solver_atoms/instance_features/feasible_frontier_features.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, specification.py |
| v2.1.0_solver_atoms/operators/atomic_move_catalog.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/local_search_moves.md |
| v2.1.0_solver_atoms/solver_code/vectorized_priority_patterns.md | internal_synthesis_license, missing_source_locator | Internal synthesis | specification.py, external_knowledge/numpy_routing_patterns.md |
| v2.1.0_solver_atoms/theory/constructive_to_improvement_bridge.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/local_search_moves.md |
| v2.2.0_dynamic_history/api_contracts/strict_array_api.md | missing_source_locator | Internal reference | specification.py, sandbox.py, dataset.py |
| v2.2.0_dynamic_history/delta_eval/incremental_reasoning_without_simulation.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md |
| v2.2.0_dynamic_history/instance_features/residual_capacity_landscape.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/capacity_distance_tradeoffs.md |
| v2.2.0_dynamic_history/internal_history/funsearch_evolution_memory.md | internal_synthesis_license, missing_source_locator | Internal synthesis | results/, specification.py |
| v2.2.0_dynamic_history/operators/operator_bias_signals.md | internal_synthesis_license, missing_source_locator | Internal synthesis | external_knowledge/local_search_moves.md |
| v2.2.0_dynamic_history/solver_code/stable_numpy_scoring.md | internal_synthesis_license, missing_source_locator | Internal synthesis | specification.py, sandbox.py |
| v2.2.0_dynamic_history/theory/adaptive_search_map.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/capacity_distance_tradeoffs.md |
| v2.3.0_full_corpus/api_contracts/sandbox_guardrails.md | missing_source_locator | Internal reference | specification.py, sandbox.py, dataset.py |
| v2.3.0_full_corpus/delta_eval/fast_fitness_patterns.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md |
| v2.3.0_full_corpus/instance_features/matrix_frontier_state.md | internal_synthesis_license, missing_source_locator | Internal synthesis | specification.py, external_knowledge/capacity_distance_tradeoffs.md |
| v2.3.0_full_corpus/internal_history/evolution_feedback_patterns.md | internal_synthesis_license, missing_source_locator | Internal synthesis | results/, specification.py |
| v2.3.0_full_corpus/internal_history/failure_mode_catalog.md | internal_synthesis_license, missing_source_locator | Internal synthesis | results/, sandbox.py, specification.py |
| v2.3.0_full_corpus/operators/operator_selection_rules.md | internal_synthesis_license, missing_source_locator | Internal synthesis | external_knowledge/local_search_moves.md |
| v2.3.0_full_corpus/solver_code/solver_pattern_signals.md | internal_synthesis_license, missing_source_locator | Internal synthesis | specification.py, external_knowledge/numpy_routing_patterns.md |
| v2.3.0_full_corpus/theory/search_stack_summary.md | internal_synthesis_license, missing_source_locator, design_doc_distillation | Internal synthesis | Corpus Design.md, external_knowledge/cvrp_heuristics.md, external_knowledge/local_search_moves.md |
