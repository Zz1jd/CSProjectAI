---
title: PyVRP Benchmark Gap and Diagnostics
date: 2026-04-20
license: official_site_terms
topics: cvrp,instance_features,benchmarking
summary: PyVRP's basic CVRP example treats benchmark evaluation as more than an objective number by explicitly loading best-known solutions, computing percentage gaps, and exposing search diagnostics.
source_type: benchmark_workflow_note
summary_level: leaf
authority_score: 0.84
url: https://pyvrp.readthedocs.io/en/stable/examples/basic_vrps.html
source_id: official_pyvrp_docs
distilled_from: https://pyvrp.readthedocs.io/en/stable/examples/basic_vrps.html
---

The PyVRP basic CVRP example reads the `X-n439-k37` instance together with its best-known solution, solves the instance for 2000 iterations, and then reports the percentage gap rather than only the raw objective. In the documented run, the solver returns cost 37428 versus a best known 36391, which corresponds to a 2.8 percent gap. This makes benchmark comparability an explicit part of the workflow.

The same example also surfaces optimization diagnostics through the `Result` object and plotting utilities. Objective traces, iteration runtimes, and final-solution visualisation are presented as standard outputs, not optional debugging extras. For corpus design, that means benchmark notes should capture both how to read the instance and how to normalize and inspect outcomes, since retrieval may need to provide evaluation conventions and not just file-format details.