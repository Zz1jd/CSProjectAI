---
title: jsprit Ruin Strategy Family
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,operators
summary: jsprit implements a broad ruin family including random, radial, worst, cluster, kruskal-cluster, and string ruin, each as a named factory with its own removal logic.
source_type: ruin_reference
summary_level: leaf
authority_score: 0.84
url: https://github.com/graphhopper/jsprit
source_id: official_jsprit_repo
distilled_from: https://github.com/graphhopper/jsprit
---

The jsprit ruin layer is explicitly plural. Migration and factory documentation list random, radial, worst, cluster, kruskal-cluster, and string ruin as separate available strategies, with bounded-fraction variants for controlling removal share. This means destroy behavior is not a single generic "ruin" step but a configurable family of perturbation patterns.

String ruin is especially important because it removes contiguous sequences from routes rather than isolated jobs. Its implementation draws a seed job, explores neighborhood structure, chooses route-local string bounds, and removes the selected subsequence from affected routes. Worst ruin, by contrast, removes jobs with the highest removal benefit and can add noise. A governed corpus should keep these variants distinct because each one implies a different exploration bias during ruin-and-recreate search.