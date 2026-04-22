---
title: HGS Population Diversity and Restart Policy
date: 2026-04-20
license: repository_license
topics: cvrp,solver_atoms,solver_code
summary: HGS-CVRP manages feasible and infeasible subpopulations separately, measures diversity with broken-pairs distance, and uses restart plus penalty adaptation as core population-control mechanisms.
source_type: population_management_note
summary_level: leaf
authority_score: 0.87
url: https://github.com/vidalt/HGS-CVRP
source_id: official_hgs_cvrp_repo
distilled_from: https://github.com/vidalt/HGS-CVRP
---

HGS-CVRP organizes its search around a population object that stores feasible and infeasible individuals in separate subpopulations. It tracks best solutions for the current restart and for the whole run, computes broken-pairs distance for diversity, updates biased fitness, and can remove the worst individual by biased fitness when survivor selection is triggered. This makes diversity maintenance a native population feature rather than a reporting afterthought.

Population generation and restart behavior reinforce the same design. The initial population builds about `4 * mu` randomized individuals, repairs a share of infeasible ones with stronger penalties, and can later restart by cleaning solutions and rebuilding the initial population. Penalty management is also explicit, so feasibility pressure is adjusted instead of being frozen. Retrieval should therefore treat HGS population control as a solver atom on its own, not just an implementation detail around crossover and local search.