---
title: Vidal 2016 pseudocode node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,split,pseudocode
summary: Pseudocode node for the governed COR 2016 Split paper package.
source_type: journal_pseudocode
summary_level: leaf
journal: Computers & Operations Research
paper_type: research_article
section_ref: 2 Methodology pseudocode
authority_score: 0.93
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=4
---

1. Build prefix arrays for cumulative demand and cumulative travel along the giant tour.
2. Initialise a candidate queue with predecessor `0` and decoder cost `0`.
3. For each breakpoint `j` from `1` to `n`, pop queue fronts that cannot start a feasible route ending at `j`.
4. Use the current front to set the best predecessor and route cost for `j`.
5. Form the state associated with predecessor `j` and compare it with queue back elements using the paper's dominance test.
6. Remove dominated back elements, append `j`, and continue until all breakpoints are processed.
7. Recover routes by backtracking predecessor pointers from `n`.