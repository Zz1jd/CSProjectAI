---
title: Vidal 2016 methodology node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,split,methodology
summary: Methodology node for the governed COR 2016 Split paper package.
source_type: journal_methodology
summary_level: leaf
journal: Computers & Operations Research
paper_type: research_article
section_ref: 2 Methodology
authority_score: 0.96
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=3
---

The method rewrites Split as shortest-path optimisation over prefix positions of the giant tour. By tracking cumulative load and travel cost, the cost of opening a route from predecessor `i` to successor `j` can be evaluated from prefix sums instead of reconstructing the whole subsequence. The key structural result is a dominance rule over predecessor states: once candidate predecessors are kept in the right order, a queue can discard states that will never again be optimal for later breakpoints. This yields an `O(n)` decoder for the standard hard-capacity case and closely related procedures for bounded-fleet and soft-capacity variants.