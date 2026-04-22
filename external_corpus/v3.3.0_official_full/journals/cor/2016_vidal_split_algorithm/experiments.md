---
title: Vidal 2016 experiments node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,benchmark,experiments
summary: Experiments node for the governed COR 2016 Split paper package.
source_type: journal_experiments
summary_level: leaf
journal: Computers & Operations Research
paper_type: research_article
section_ref: 4 Computational experiments
benchmark_family: tsplib_derived,world_tsp_derived,cvrp_randomized
metrics: split_runtime,speedup
authority_score: 0.94
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=7
---

The experiments isolate decoder cost rather than overall metaheuristic quality. The paper builds giant tours from TSPLIB and World-TSP coordinates, assigns random customer demands, and then tests Split under ten capacity scales ranging from very tight to very loose routes. Runtime is compared between the classical Bellman implementation and the linear algorithm on unlimited-fleet, limited-fleet, and soft-capacity settings. The reported evidence therefore speaks directly to how much search time a solver can recover when Split is called repeatedly.