# Numpy Routing Patterns

This note gives numpy-first patterns for CVRP priority functions.

## Project constraints recap

Current prompt expects:
- start from scores = distance_data[current_node].copy()
- return a full score vector
- use numpy operations such as np.where, np.clip, np.power
- avoid slow Python loops when possible

## Common vectorized building blocks

### 1) Feasibility mask

```python
feasible = node_demands <= remaining_capacity
```

### 2) Safe ratio operations

```python
cap = max(remaining_capacity, 1)
ratio = node_demands / cap
ratio = np.clip(ratio, 0.0, 10.0)
```

### 3) Piecewise penalties with np.where

```python
penalty = np.where(feasible, 0.0, np.power(ratio - 1.0, 2))
```

### 4) Smooth nonlinear terms

```python
demand_term = np.sqrt(np.clip(node_demands, 0, None))
distance_term = distance_data[current_node]
curve_term = np.power(np.clip(ratio, 0.0, 1.0), 1.5)
```

## Template snippets

Distance-dominant template:

```python
scores = distance_data[current_node].copy()
ratio = node_demands / max(remaining_capacity, 1)
scores = -(scores + 0.4 * ratio)
```

Feasible-first template:

```python
scores = -distance_data[current_node].copy()
scores = np.where(feasible, scores, scores - 1000.0)
```

Demand-aware template:

```python
scores = -distance_data[current_node].copy()
scores = scores + 0.2 * np.sqrt(np.clip(node_demands, 0, None))
```

## Numerical stability tips

- Guard division with max(remaining_capacity, 1) or small epsilon.
- Use np.clip before np.power for safer exponentiation.
- Keep score magnitudes reasonable; very large constants can dominate all terms.

## Quick validation checks

1. Output shape equals number of nodes.
2. Feasible nodes usually outrank infeasible nodes.
3. Nearest feasible node can still win when demand terms are present.
4. Score direction is consistent with argmax selection.
