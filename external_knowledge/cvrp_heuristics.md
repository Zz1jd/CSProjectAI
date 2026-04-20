# CVRP Heuristics Playbook

This note summarizes practical heuristics for a CVRP priority function.

## Core objective

At each step, choose the nearest feasible node while still considering demand and remaining capacity.

Important runtime variables:
- current_node
- distance_data
- remaining_capacity
- node_demands

The score convention in this project is:
- Higher score means higher priority.
- If you start from distance values, return negative scores so nearer nodes become better.

## Stable baseline pattern

Start from a distance copy:

```python
scores = distance_data[current_node].copy()
```

Compute feasibility mask:

```python
feasible_mask = node_demands <= remaining_capacity
```

Reward feasible nodes by reducing distance-like score and penalize infeasible nodes.

## Practical score shaping terms

Use combinations of these terms:
- distance term: distance_data[current_node]
- demand term: node_demands
- capacity ratio: node_demands / max(remaining_capacity, 1)
- urgency term: np.power(node_demands, p)

Example formula style:

```python
distance_term = distance_data[current_node]
demand_term = np.sqrt(np.clip(node_demands, 0, None))
capacity_ratio = node_demands / max(remaining_capacity, 1)

scores = -(distance_term + 0.6 * capacity_ratio - 0.2 * demand_term)
```

## Feasibility first

Keep infeasible nodes unattractive:

```python
scores = np.where(feasible_mask, scores, scores - 1e3)
```

Alternative softer penalty:

```python
scores = np.where(feasible_mask, scores, scores - 10.0 * np.power(capacity_ratio, 2))
```

## Do and do not

Do:
- Keep nearest feasible node logic strong.
- Use vectorized numpy math.
- Use np.where, np.clip, np.power for controlled nonlinearity.

Do not:
- Let infeasible nodes beat feasible nodes.
- Overweight demand so distance is ignored.
- Use slow Python loops when vectorized operations are possible.

## Quick checklist

Before returning scores:
1. Feasible nodes are generally ranked above infeasible nodes.
2. Nearer feasible nodes usually rank higher than farther feasible nodes.
3. Return shape is compatible with node indexing.
4. Returned score direction matches argmax behavior.
