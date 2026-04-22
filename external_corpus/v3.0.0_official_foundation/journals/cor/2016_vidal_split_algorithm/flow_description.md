---
title: Vidal 2016 flow description node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,split,algorithm_flow
summary: Flow-description node for the governed COR 2016 Split paper package.
source_type: journal_flow_description
summary_level: leaf
journal: Computers & Operations Research
paper_type: research_article
section_ref: 2 Methodology flow
authority_score: 0.93
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=4
---

Linear Split can be read as a streaming pass over tour positions. First compute prefix sums for demand and distance so every candidate arc cost from predecessor `i` to breakpoint `j` is available in constant time. Then maintain a queue of candidate predecessors ordered so the front is always the best currently feasible break position, dropping front elements that violate capacity and back elements that become dominated for every future `j`. Each new tour position contributes one query to read the best predecessor and one insertion that preserves the dominance ordering.