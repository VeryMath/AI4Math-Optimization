---
name: Minimum Group Assignment with Conflict Separation
description: |
  Models and solves the problem of assigning items to the minimum number of groups such that conflicting pairs are never placed in the same group, using either binary assignment variables with group usage indicators or integer assignment variables with reified constraints.
---

# Workflow 1 (Binary Assignment with Group Indicators)

## Modeling stage

### Strategy Overview
Use a binary assignment variable for each item-group pair, a binary group usage indicator, and linear constraints to enforce each item is assigned exactly once, conflicting items are separated, and group usage is correctly linked. The objective minimizes the sum of group usage indicators.

### Step 1 - Define Sets and Parameters
- Define the set of items `I` and an upper bound on groups `K` (e.g., `|I|`).
- Define the set of conflict pairs `C` as tuples `(u, v)` where items cannot share a group.

### Step 2 - Create Decision Variables
- Create binary variable `x[i, k]` for each item `i` in `I` and each group `k` in `K`, indicating assignment.
- Create binary variable `y[k]` for each group `k` in `K`, indicating if the group is used.

### Step 3 - Add Assignment Constraints
- For each item `i`, enforce `sum(x[i, k] for k in K) == 1` to ensure exactly one group per item.

### Step 4 - Add Conflict Separation Constraints
- For each conflict pair `(u, v)` in `C` and each group `k` in `K`, enforce `x[u, k] + x[v, k] <= 1`.

### Step 5 - Link Group Usage
- For each item `i` and group `k`, enforce `x[i, k] <= y[k]` to activate `y[k]` when any item is assigned to group `k`.

### Step 6 - Set Objective
- Minimize `sum(y[k] for k in K)` to minimize the number of used groups.

### Formulation Template
```json
{
  "sets": ["I: items", "K: groups (0..|I|-1)", "C: conflict pairs (u,v)"],
  "parameters": [],
  "decision_variables": [
    "x[i,k] binary: item i assigned to group k",
    "y[k] binary: group k is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[k] for k in K)"
  },
  "constraints": [
    "sum(x[i,k] for k in K) == 1 for all i in I",
    "x[u,k] + x[v,k] <= 1 for all (u,v) in C, k in K",
    "x[i,k] <= y[k] for all i in I, k in K"
  ]
}
```

### Common Pitfalls
- Setting the upper bound on groups too low, causing infeasibility; always use `|I|` as a safe upper bound.
- Forgetting to add conflict constraints for both orderings `(u,v)` and `(v,u)` if the conflict list is not symmetric.
- Omitting the `x[i,k] <= y[k]` constraint, which allows the solver to use a group without counting it in the objective.

## Solving stage

### Strategy Overview
Use a constraint programming solver (OR-Tools CP-SAT) that efficiently handles binary variables and linear constraints. Configure time limits and parallelism for practical performance.

### Step 1 - Initialize Solver and Model
- Import `cp_model` from `ortools.sat.python`.
- Create a `CpModel()` instance.

### Step 2 - Build Variables and Constraints
- Use `model.NewBoolVar(name)` for each `x[i,k]` and `y[k]`.
- Add constraints using `model.Add(expression)`.

### Step 3 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to a reasonable limit (e.g., 30.0).
- Set `solver.parameters.num_search_workers` to 8 for parallel search.
- Optionally set `solver.parameters.random_seed` for reproducibility.

### Step 4 - Solve and Extract Solution
- Call `status = solver.Solve(model)`.
- Check if `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.
- Extract assignment: for each item `i`, find the group `k` where `solver.Value(x[i,k]) > 0`.
- Count used groups: `sum(1 for k in K if solver.Value(y[k]) > 0)`.

### Step 5 - Validate and Output
- Verify no conflict pair shares the same group by checking the extracted assignment.
- Output a JSON payload with `status`, `objective` (as float), and the assignment dictionary.

### Code Usage
```python
from ortools.sat.python import cp_model

# Problem data
items = list(range(num_items))
conflict_pairs = [(u, v), ...]  # list of tuples
max_groups = len(items)
groups = list(range(max_groups))

model = cp_model.CpModel()

# Variables
x = {}
for i in items:
    for k in groups:
        x[i, k] = model.NewBoolVar(f'x_{i}_{k}')
y = {}
for k in groups:
    y[k] = model.NewBoolVar(f'y_{k}')

# Constraints
for i in items:
    model.Add(sum(x[i, k] for k in groups) == 1)

for u, v in conflict_pairs:
    for k in groups:
        model.Add(x[u, k] + x[v, k] <= 1)

for i in items:
    for k in groups:
        model.Add(x[i, k] <= y[k])

# Objective
model.Minimize(sum(y[k] for k in groups))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    obj_val = float(sum(1 for k in groups if solver.Value(y[k]) > 0))
    assignment = {}
    for i in items:
        for k in groups:
            if solver.Value(x[i, k]) > 0:
                assignment[i] = k
                break
    # Verify no conflicts
    for u, v in conflict_pairs:
        assert assignment[u] != assignment[v], f"Conflict violation: {u}, {v}"
    print(f"RESULT:{obj_val}")
else:
    print('{"status": "failed", "reason": "infeasible_or_timeout"}')
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, which may discard valid solutions found within the time limit.
- Using `solver.Value()` on variables that were not part of the solution (e.g., after infeasibility), causing runtime errors.
- Forgetting to set a time limit, causing the solver to run indefinitely on large instances.

# Workflow 2 (Integer Assignment with Reified Constraints)

## Modeling stage

### Strategy Overview
Use an integer variable for each item representing its group assignment, with reified Boolean variables to track group usage. This reduces the number of decision variables compared to the binary approach, but requires more complex linking constraints.

### Step 1 - Define Sets and Parameters
- Define the set of items `I` and an upper bound on groups `K` (e.g., `|I|`).
- Define the set of conflict pairs `C` as tuples `(u, v)`.

### Step 2 - Create Decision Variables
- Create integer variable `color[i]` for each item `i` in `I` with domain `[0, max_groups-1]`.
- Create Boolean variable `used[k]` for each group `k` in `K` to indicate if the group is used.

### Step 3 - Add Conflict Separation Constraints
- For each conflict pair `(u, v)` in `C`, enforce `color[u] != color[v]`.

### Step 4 - Link Group Usage with Reified Constraints
- For each item `i` and group `k`, create a Boolean variable `eq[i][k]` that is true iff `color[i] == k`.
- Use `model.Add(color[i] == k).OnlyEnforceIf(eq[i][k])` and `model.Add(color[i] != k).OnlyEnforceIf(eq[i][k].Not())` to enforce the equivalence.
- For each item `i` and group `k`, enforce `model.Add(used[k] == 1).OnlyEnforceIf(eq[i][k])` to activate `used[k]` when any item is assigned to group `k`.

### Step 5 - Set Objective
- Minimize `sum(used[k] for k in K)` to minimize the number of used groups.

### Formulation Template
```json
{
  "sets": ["I: items", "K: groups (0..|I|-1)", "C: conflict pairs (u,v)"],
  "parameters": [],
  "decision_variables": [
    "color[i] integer in [0, |I|-1]: group assignment for item i",
    "used[k] binary: group k is used",
    "eq[i,k] binary: indicator that color[i] == k"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[k] for k in K)"
  },
  "constraints": [
    "color[u] != color[v] for all (u,v) in C",
    "color[i] == k iff eq[i,k] == 1 for all i in I, k in K",
    "used[k] == 1 if eq[i,k] == 1 for all i in I, k in K"
  ]
}
```

### Common Pitfalls
- Creating too many `eq[i,k]` variables (O(|I|^2)) which can blow up memory; only create them for items and groups that are relevant.
- Forgetting the `OnlyEnforceIf` for the negative case (`color[i] != k`), which can leave the equivalence unconstrained.
- Using `model.Add(color[i] == k)` directly without reification, which forces a specific assignment rather than allowing the solver to choose.

## Solving stage

### Strategy Overview
Use a constraint programming solver (OR-Tools CP-SAT) that supports reified constraints via `OnlyEnforceIf`. This approach is well-suited for problems with integer variables and logical implications.

### Step 1 - Initialize Solver and Model
- Import `cp_model` from `ortools.sat.python`.
- Create a `CpModel()` instance.

### Step 2 - Build Variables and Constraints
- Use `model.NewIntVar(0, max_groups-1, name)` for each `color[i]`.
- Use `model.NewBoolVar(name)` for each `used[k]` and `eq[i,k]`.
- Add constraints using `model.Add(expression).OnlyEnforceIf(condition)`.

### Step 3 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to a reasonable limit (e.g., 30.0).
- Set `solver.parameters.num_search_workers` to 8 for parallel search.
- Optionally set `solver.parameters.random_seed` for reproducibility.

### Step 4 - Solve and Extract Solution
- Call `status = solver.Solve(model)`.
- Check if `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.
- Extract assignment: for each item `i`, get `solver.Value(color[i])`.
- Count used groups: `sum(1 for k in K if solver.Value(used[k]) > 0)`.

### Step 5 - Validate and Output
- Verify no conflict pair shares the same group by checking the extracted assignment.
- Output a JSON payload with `status`, `objective` (as float), and the assignment dictionary.

### Code Usage
```python
from ortools.sat.python import cp_model

# Problem data
items = list(range(num_items))
conflict_pairs = [(u, v), ...]  # list of tuples
max_groups = len(items)
groups = list(range(max_groups))

model = cp_model.CpModel()

# Variables
color = {}
for i in items:
    color[i] = model.NewIntVar(0, max_groups - 1, f'color_{i}')
used = {}
for k in groups:
    used[k] = model.NewBoolVar(f'used_{k}')
eq = {}
for i in items:
    for k in groups:
        eq[i, k] = model.NewBoolVar(f'eq_{i}_{k}')

# Constraints
for u, v in conflict_pairs:
    model.Add(color[u] != color[v])

for i in items:
    for k in groups:
        model.Add(color[i] == k).OnlyEnforceIf(eq[i, k])
        model.Add(color[i] != k).OnlyEnforceIf(eq[i, k].Not())
        model.Add(used[k] == 1).OnlyEnforceIf(eq[i, k])

# Objective
model.Minimize(sum(used[k] for k in groups))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    obj_val = float(sum(1 for k in groups if solver.Value(used[k]) > 0))
    assignment = {i: solver.Value(color[i]) for i in items}
    # Verify no conflicts
    for u, v in conflict_pairs:
        assert assignment[u] != assignment[v], f"Conflict violation: {u}, {v}"
    print(f"RESULT:{obj_val}")
else:
    print('{"status": "failed", "reason": "infeasible_or_timeout"}')
```

### Common Pitfalls
- Using `model.Add(color[i] == k)` without `OnlyEnforceIf`, which forces the solver to assign item `i` to group `k` unconditionally.
- Not creating the `eq[i,k]` variables for all `(i,k)` pairs, which can lead to missing constraints that link group usage.
- Forgetting to set `OnlyEnforceIf(eq[i,k].Not())` for the negative case, which can cause the solver to incorrectly infer `color[i] == k` when `eq[i,k]` is false.
