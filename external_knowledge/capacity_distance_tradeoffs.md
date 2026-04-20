# Capacity and Distance Trade-offs

This note focuses on balancing distance_data, node_demands, and remaining_capacity in CVRP scoring.

## Why trade-offs matter

Greedy nearest-node choice can fail when it consumes capacity too early.
Demand-heavy choice can also fail when route distance explodes.

The priority score should balance:
- short travel from current_node
- demand fit with remaining_capacity
- future flexibility for the rest of the route

## Useful normalized terms

```python
d = distance_data[current_node]
d_norm = d / (np.max(d) + 1e-9)

q = node_demands
q_norm = q / (np.max(q) + 1e-9)

cap_ratio = q / max(remaining_capacity, 1)
```

## Weighted blend template

```python
feasible = q <= remaining_capacity
scores = -(0.70 * d_norm + 0.25 * cap_ratio - 0.15 * q_norm)
scores = np.where(feasible, scores, scores - 1000.0)
```

Interpretation:
- 0.70 keeps distance dominant.
- cap_ratio prevents overfilling.
- q_norm gives mild preference to meaningful demand.

## Nonlinear penalty ideas

Infeasible demand should become rapidly worse:

```python
overflow = np.clip(cap_ratio - 1.0, 0.0, None)
penalty = np.power(overflow, 2)
scores = scores - 20.0 * penalty
```

This gives smooth but strong rejection of over-capacity nodes.

## Remaining-capacity regimes

When remaining_capacity is high:
- Be more distance-driven.

When remaining_capacity is tight:
- Increase cap_ratio penalty.
- Prioritize small-demand feasible nodes near current_node.

Simple adaptive weight example:

```python
cap_tight = 1.0 - min(remaining_capacity / (np.max(node_demands) + 1e-9), 1.0)
w_cap = 0.2 + 0.5 * cap_tight
w_dist = 0.8 - 0.3 * cap_tight
scores = -(w_dist * d_norm + w_cap * cap_ratio)
```

## Failure signs

If routes become very long:
- demand term is too strong relative to distance.

If many infeasible nodes are selected early:
- feasibility penalties are too weak.

If vehicle returns too early with spare room:
- small-demand preference is too strong.
