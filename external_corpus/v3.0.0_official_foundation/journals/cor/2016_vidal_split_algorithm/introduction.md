---
title: Vidal 2016 introduction node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,split,introduction
summary: Introduction node for the governed COR 2016 Split paper package.
source_type: journal_introduction
summary_level: summary
journal: Computers & Operations Research
paper_type: research_article
section_ref: 1 Introduction
authority_score: 0.94
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=2
---

Split is a core decoder in route-first, cluster-second CVRP methods because many metaheuristics evolve a giant TSP-like tour and rely on Split to insert depot breaks afterwards. Earlier work already made the decoder practical, but its dynamic-programming form still contributes noticeable overhead when it is called repeatedly inside population search or repeated local search. The introduction argues that this cost becomes unnecessary once one exploits the structural regularity induced by cumulative distance and demand along the giant tour. The goal is therefore narrow but important: remove decoder overhead without changing the decoded objective.