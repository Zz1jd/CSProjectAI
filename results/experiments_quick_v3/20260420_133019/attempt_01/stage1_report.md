# Baseline vs RAG Comparison Report

## Run Setup
- Baseline log: `results/experiments_quick_v3/20260420_133019/baseline_stage1.log`
- RAG log: `results/experiments_quick_v3/20260420_133019/attempt_01/rag_stage1.log`
- Baseline seed: 42
- RAG seed: 42
- Baseline model: gpt-3.5-turbo
- RAG model: gpt-3.5-turbo
- Baseline budget: 2
- RAG budget: 2
- Seed match: Yes
- Model match: Yes

## Metrics
- Baseline best score: -1157.297130
- RAG best score: -1145.532921
- Delta (rag - baseline): 11.764209
- Relative change vs baseline: 1.016525%
- Improved vs baseline: Yes
- Baseline valid eval ratio: 1.000000
- RAG valid eval ratio: 1.000000
- Baseline evals per sample: 1.500000
- RAG evals per sample: 1.500000
- Baseline sample progress evidence: 2/2
- RAG sample progress evidence: 2/2

## Retrieval Diagnostics
- Baseline retrieval events: 0
- Baseline mean top score: NA
- Baseline mean top score gap: NA
- Baseline mean retrieval confidence: NA
- Baseline mean injected chars: NA
- Baseline mean unique sources: NA
- Baseline retrieval skip ratio: NA
- RAG retrieval events: 1
- RAG mean top score: 0.662263
- RAG mean top score gap: 0.065718
- RAG mean retrieval confidence: 0.391650
- RAG mean injected chars: 780.000000
- RAG mean unique sources: 2.000000
- RAG retrieval skip ratio: 0.00%

## Policy Compliance
- Policy compliant: Yes
- Run mode valid: Yes
- Same run mode: Yes
- Budgets match: Yes
- Budget cap (Not enforced) respected: Yes
- Sample evidence within budget: Yes

## Acceptance
- Acceptance passed: No
- Same seed required: Yes
- Same model required: Yes
- Same budget required: Yes
- Score beats baseline: Yes
- Relative gain guard (5.00%): No
- Valid eval ratio guard: Yes
- Completion guard: Yes
- Policy warnings: None
- Acceptance warnings:
  - Relative gain did not meet the minimum acceptance threshold.

## Notes
- Fresh baseline and RAG logs should be generated under matched budget and timeout for fair comparison.
- If seed/model do not match, treat the result as directional rather than controlled evidence.
