---
name: Quadratic Assignment Problem Solver
description: |
  Models and solves one-to-one assignment problems with quadratic interaction costs using either MILP linearization or direct permutation enumeration.

---
# Workflow 1 (MILP Linearization with OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Transform the quadratic assignment objective into a linear form by introducing auxiliary binary variables for each product of assignment variables. This enables the use of MILP solvers like OR-Tools CP-SAT for small to medium instances.

### Step 1 - Define Sets and Parameters
- Create index sets for items (e.g., `items = range(N)`) and slots (e.g., `slots = range(N)`).
- Define flow matrix `flow[i][k]` and distance matrix `dist[j][l]` as dictionaries or 2D lists keyed by index pairs.
- **Verify problem symmetry**: Check if flow and distance matrices are symmetric (flow[i][k] = flow[k][i], dist[j][l] = dist[l][j]) to confirm the problem structure and potentially optimize computation.

### Step 2 - Declare Binary Assignment Variables
- Create binary variable `x[i][j]` for each item `i` and slot `j`, indicating assignment.
- Use `model.NewBoolVar(f'x_{i}_{j}')` in OR-Tools CP-SAT.

### Step 3 - Enforce One-to-One Constraints
- Add constraint: `sum(x[i][j] for j in slots) == 1` for each item `i`.
- Add constraint: `sum(x[i][j] for i in items) == 1` for each slot `j`.

### Step 4 - Linearize Quadratic Objective
- For each pair of items `(i, k)` with non-zero flow and each pair of slots `(j, l)` with non-zero distance, create auxiliary binary variable `z[i][k][j][l]` representing `x[i][j] * x[k][l]`.
- Add linearization constraints:
  - `z[i][k][j][l] <= x[i][j]`
  - `z[i][k][j][l] <= x[k][l]`
  - `z[i][k][j][l] >= x[i][j] + x[k][l] - 1`
- Only create `z` variables for quadruples where `flow[i][k] > 0` and `dist[j][l] > 0` to reduce model size.

### Step 5 - Build Objective
- Minimize `sum(flow[i][k] * dist[j][l] * z[i][k][j][l] for all relevant quadruples)`.
- **Scale to integers**: Convert floating-point flow/distance values to integers before passing to CP-SAT (requires integer coefficients).

### Formulation Template
```json
{
  "sets": ["I: items", "J: slots"],
  "parameters": ["flow[i][k]: interaction flow between items i and k", "dist[j][l]: distance between slots j and l"],
  "decision_variables": [
    "x[i][j] ∈ {0,1}: assignment of item i to slot j",
    "z[i][k][j][l] ∈ {0,1}: product x[i][j] * x[k][l] for non-zero flow/distance pairs"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,k} sum_{j,l} flow[i][k] * dist[j][l] * z[i][k][j][l]"
  },
  "constraints": [
    "sum_j x[i][j] == 1, ∀i ∈ I",
    "sum_i x[i][j] == 1, ∀j ∈ J",
    "z[i][k][j][l] <= x[i][j], ∀ relevant quadruples",
    "z[i][k][j][l] <= x[k][l], ∀ relevant quadruples",
    "z[i][k][j][l] >= x[i][j] + x[k][l] - 1, ∀ relevant quadruples"
  ]
}
```

### Common Pitfalls
- Creating `z` variables for all quadruples (O(N^4)) even when flow or distance is zero, causing unnecessary model bloat.
- Forgetting to enforce both directions of the one-to-one constraint (items-to-slots and slots-to-items).
- Using floating-point flow/distance values without scaling to integers for CP-SAT.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with parallel search and time limits. Extract results with proper status checking and output in structured JSON format.

### Step 1 - Configure Solver
- Create `CpSolver()` instance.
- Set parameters: `max_time_in_seconds=[TIME_LIMIT]`, `num_search_workers=8`, `random_seed=42`, `relative_gap_limit=0.0`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.

### Step 3 - Extract Results
- Retrieve objective value via `solver.ObjectiveValue()`.
- Extract assignment by iterating over `x` variables and checking `solver.Value(x[i][j]) == 1`.
- Build assignment dictionary mapping item index to slot index.

### Step 4 - Output and Validate
- Output JSON with keys: `status`, `objective_value`, `assignment`.
- **Include verification step**: Recompute cost for the best assignment using the original quadratic formula to ensure correctness.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_qap_cpsat(items, slots, flow, dist, time_limit=30.0):
    model = cp_model.CpModel()
    N = len(items)
    x = {}
    for i in items:
        for j in slots:
            x[i, j] = model.NewBoolVar(f'x_{i}_{j}')
    
    # One-to-one constraints
    for i in items:
        model.Add(sum(x[i, j] for j in slots) == 1)
    for j in slots:
        model.Add(sum(x[i, j] for i in items) == 1)
    
    # Linearization
    z = {}
    for i in items:
        for k in items:
            if flow[i][k] == 0:
                continue
            for j in slots:
                for l in slots:
                    if dist[j][l] == 0:
                        continue
                    z[i, k, j, l] = model.NewBoolVar(f'z_{i}_{k}_{j}_{l}')
                    model.Add(z[i, k, j, l] <= x[i, j])
                    model.Add(z[i, k, j, l] <= x[k, l])
                    model.Add(z[i, k, j, l] >= x[i, j] + x[k, l] - 1)
    
    # Objective
    obj_expr = sum(flow[i][k] * dist[j][l] * z[i, k, j, l]
                   for (i, k, j, l) in z)
    model.Minimize(obj_expr)
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignment = {i: next(j for j in slots if solver.Value(x[i, j]) == 1) for i in items}
        return {
            "status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
            "objective_value": solver.ObjectiveValue(),
            "assignment": assignment
        }
    else:
        return {"status": "FAILURE", "solver_status": status}
```

### Common Pitfalls
- Not scaling floating-point parameters to integers before passing to CP-SAT (requires integer coefficients).
- Ignoring the `FEASIBLE` status when optimality is not guaranteed within time limit.
- Forgetting to set `random_seed` for reproducibility across runs.

# Workflow 2 (Direct Permutation Enumeration)

## Modeling stage

### Strategy Overview
For small instances (N ≤ 8), enumerate all possible assignments as permutations of slots. This avoids solver dependencies and provides exact optimal solutions through brute-force search.

### Step 1 - Define Sets and Parameters
- Create list of items `items = list(range(N))` and slots `slots = list(range(N))`.
- Define flow matrix `flow[i][k]` and distance matrix `dist[j][l]` as 2D lists or NumPy arrays.
- **Verify problem symmetry**: Check if flow and distance matrices are symmetric (flow[i][k] = flow[k][i], dist[j][l] = dist[l][j]) to confirm the problem structure and enable computational optimizations.
- **Note small problem size**: For N ≤ 8, complete enumeration is feasible (N! ≤ 40320 permutations). For N ≤ 10, enumeration may still be practical depending on hardware.

### Step 2 - Model as Permutation Problem
- Recognize that a one-to-one assignment is equivalent to a permutation `π` where item `i` is assigned to slot `π[i]`.
- The objective becomes: `sum_{i,k} flow[i][k] * dist[π[i]][π[k]]`.
- **Leverage symmetry for optimization**: Since matrices are symmetric, compute only upper triangle (i < k) and double the result.

### Step 3 - No Explicit Variables or Constraints
- The permutation structure inherently satisfies one-to-one constraints.
- No decision variables or constraints are needed; the search space is all permutations of `N` elements.

### Formulation Template
```json
{
  "sets": ["I: items (0..N-1)", "J: slots (0..N-1)"],
  "parameters": ["flow[i][k]: interaction flow between items i and k", "dist[j][l]: distance between slots j and l"],
  "decision_variables": ["π: permutation mapping item index to slot index"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,k} flow[i][k] * dist[π[i]][π[k]]"
  },
  "constraints": ["π is a bijection from I to J (implicitly satisfied by permutation structure)"]
}
```

### Common Pitfalls
- Assuming this approach scales beyond N=8 (factorial growth makes it infeasible).
- Forgetting to handle symmetric flow/distance matrices to avoid double-counting in objective computation.
- Not using early pruning or symmetry breaking for larger instances within the limit.

## Solving stage

### Strategy Overview
Use `itertools.permutations` to generate all possible assignments, compute the objective for each, and track the minimum. This provides a simple, exact solution for small instances.

### Step 1 - Generate Permutations
- Use `itertools.permutations(range(N))` to iterate over all slot assignments for items.

### Step 2 - Compute Objective for Each Permutation
- For each permutation `perm`, compute cost as `sum(flow[i][k] * dist[perm[i]][perm[k]] for i in range(N) for k in range(N))`.
- **Optimize computation**: If matrices are symmetric, compute only upper triangle (i < k) and double the result. Include diagonal terms (i=k) separately.

### Step 3 - Track Best Solution
- Initialize `best_cost = float('inf')` and `best_perm = None`.
- Update when a lower cost is found.

### Step 4 - Output Results
- Return JSON with status `"OPTIMAL"`, objective value, and assignment dictionary mapping item index to slot index.
- **Include verification step**: Recompute cost for the best assignment using the original quadratic formula to ensure correctness.
- **Confirm uniqueness (optional)**: After finding optimal cost, enumerate all permutations again to check if multiple optimal solutions exist.

### Code Usage
```python
import itertools
import json

def solve_qap_enumeration(items, slots, flow, dist):
    N = len(items)
    best_cost = float('inf')
    best_perm = None
    
    for perm in itertools.permutations(range(N)):
        cost = 0
        # Leverage symmetry: compute only upper triangle and double
        for i in range(N):
            for k in range(i, N):  # i <= k
                if i == k:
                    cost += flow[i][i] * dist[perm[i]][perm[i]]
                else:
                    cost += 2 * flow[i][k] * dist[perm[i]][perm[k]]
        if cost < best_cost:
            best_cost = cost
            best_perm = perm
    
    assignment = {i: best_perm[i] for i in range(N)}
    return {
        "status": "OPTIMAL",
        "objective_value": best_cost,
        "assignment": assignment
    }
```

### Common Pitfalls
- Using `itertools.permutations` for N > 8 (will cause memory/time explosion).
- Not exploiting symmetry (e.g., if flow or distance matrices are symmetric, compute only upper triangle and double).
- Forgetting to convert permutation indices to match slot indexing convention.

## Verification and Output (Both Workflows)
- After obtaining a solution, recompute the objective value using the assignment and the original quadratic formula to verify correctness.
- Present the final answer as a numeric value (e.g., `<answer>[OBJECTIVE_VALUE]</answer>`) for integration into automated pipelines.
