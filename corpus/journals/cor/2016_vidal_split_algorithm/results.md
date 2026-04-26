---
title: Vidal 2016 results node
paper_title: Technical Note: Split algorithm in O(n) for the capacitated vehicle routing problem
url: https://doi.org/10.1016/j.cor.2015.11.012
doi: 10.1016/j.cor.2015.11.012
manuscript_url: https://arxiv.org/pdf/1508.02759.pdf
date: 2016-04-01
year: 2016
license: CC-BY-NC-ND 4.0 manuscript
topics: cvrp,benchmark,results
summary: Results node for the governed COR 2016 Split paper package.
source_type: journal_results
summary_level: leaf
journal: Computers & Operations Research
paper_type: research_article
section_ref: 4 Computational experiments results
benchmark_family: tsplib_derived,world_tsp_derived,cvrp_randomized
metrics: split_runtime,speedup
authority_score: 0.95
source_id: cor_vidal_2016_split_journal
distilled_from: https://arxiv.org/pdf/1508.02759.pdf#page=8
---

Across the benchmark grid, the linear decoder is consistently faster and the speedup grows with route size and with the complexity of the variant. For standard unlimited-fleet Split, gains become pronounced once average routes exceed only a few customers and reach two to three orders of magnitude on large instances. Limited-fleet cases still benefit, but soft-capacity instances show the strongest contrast because the Bellman alternative grows much faster with the penalty budget. The practical conclusion is that Split no longer needs to be treated as a negligible background routine when designing CVRP metaheuristics.