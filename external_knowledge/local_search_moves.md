# Local Search Moves for CVRP

This note summarizes local search ideas that can inspire better priority scoring.

## Goal

Use route-improvement intuition to shape node priority at construction time.

Even when the policy only outputs a score vector, it can still reflect local search logic.

## Useful move concepts

1. Relocate
- Move one customer to a better position.
- Scoring implication: favor nodes that are close to current_node and likely to connect well to neighbors.

2. Swap
- Exchange two customers between route positions.
- Scoring implication: avoid extreme demand jumps that create bad future swaps.

3. 2-opt
- Reverse a route segment to reduce crossing edges.
- Scoring implication: avoid long jumps from current_node if near alternatives exist.

4. Cross-exchange
- Exchange short segments between routes.
- Scoring implication: avoid filling capacity with a pattern that blocks easy exchanges.

## Construction-time proxies

You can proxy local-search quality with simple terms:
- edge smoothness proxy: prefer node i when distance_data[current_node, i] is small
- capacity slack proxy: prefer i when remaining_capacity - node_demands[i] stays positive and not too close to zero
- neighborhood density proxy: prefer i if node i has many nearby nodes

Neighborhood density approximation:

```python
row = distance_data
near_count = np.sum(row < np.percentile(row, 25), axis=1)
```

Use near_count as a mild bonus term.

## Example composite idea

```python
d = distance_data[current_node]
q = node_demands
feasible = q <= remaining_capacity

smooth = d / (np.max(d) + 1e-9)
slack = np.clip((remaining_capacity - q) / max(remaining_capacity, 1), -1.0, 1.0)

scores = -(0.75 * smooth - 0.15 * slack)
scores = np.where(feasible, scores, scores - 1000.0)
```

## Do and do not

Do:
- Keep proxy terms weak unless validated by score improvements.
- Keep feasibility as a hard preference.

Do not:
- Add many complex terms at once.
- Overfit to one dataset with unstable heuristics.

## Evaluation reminder

A good local-search-inspired score should:
- reduce long detours
- keep routes feasible
- improve average objective over multiple instances, not just one instance
