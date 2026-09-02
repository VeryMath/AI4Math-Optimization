---
name: Minimum Unique Label Assignment via Graph Coloring
description: |
  Models a conflict graph where each vertex must be assigned a unique label (e.g., frequency) such that adjacent vertices receive different labels, and minimizes the total number of distinct labels used.

---
# Workflow 1 (MILP with Binary Assignment Variables)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using binary assignment variables for each vertex-label pair and binary usage variables for each label. The objective minimizes the sum of used labels, with constraints ensuring each vertex gets exactly one label and no adjacent vertices share a label.

### Step 1 - Define Sets and Parameters
- Define the set of vertices `V`.
- Define the set of edges `E` representing conflicts between vertex pairs.
- Define the set of possible labels `K` with cardinality equal to `|V|` (a safe upper bound).

### Step 2 - Create Decision Variables
- Create binary variable `x[i,k]` for each vertex `i` and label `k`, equal to 1 if vertex `i` is assigned label `k`.
- Create binary variable `y[k]` for each label `k`, equal to 1 if label `k` is used by any vertex.

### Step 3 - Enforce Assignment Completeness
- For each vertex `i`, add constraint: `sum_{k in K} x[i,k] == 1`.

### Step 4 - Enforce Neighbor Conflict Constraints
- For each edge `(i,j)` in `E` and each label `k` in `K`, add constraint: `x[i,k] + x[j,k] <= 1`.

### Step 5 - Link Usage Variables
- For each vertex `i` and label `k`, add constraint: `x[i,k] <= y[k]`.

### Step 6 - Set Objective
- Minimize the sum of `y[k]` over all labels `k`.

### Formulation Template
```json
{
  "sets": ["V: vertices", "E: edges (conflicts)", "K: labels (size = |V|)"],
  "parameters": [],
  "decision_variables": [
    "x[i,k] binary: 1 if vertex i assigned label k",
    "y[k] binary: 1 if label k is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{k in K} y[k]"
  },
  "constraints": [
    "sum_{k in K} x[i,k] == 1, for all i in V",
    "x[i,k] + x[j,k] <= 1, for all (i,j) in E, k in K",
    "x[i,k] <= y[k], for all i in V, k in K"
  ]
}
```

### Common Pitfalls
- Setting `|K|` too small, making the model infeasible when a feasible solution exists with more labels.
- Forgetting to link `x` and `y` variables, causing the solver to use labels without counting them in the objective.
- Using continuous variables instead of binary, which can lead to fractional assignments.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., Gurobi, CPLEX, or SCIP) with binary variables. Set a time limit and zero MIP gap for optimality. After solving, extract the objective value and decode the assignment for each vertex.

### Step 1 - Initialize Solver and Model
- Import the solver library (e.g., `gurobipy`, `pulp`, or `ortools`).
- Create a model instance and set parameters: time limit (e.g., `[TIME_LIMIT]` seconds), MIP gap (0), random seed.

### Step 2 - Build and Solve
- Add variables and constraints as defined in the modeling stage.
- Call the solve method.

### Step 3 - Check Status and Extract Results
- Verify solver status is `optimal` or `feasible`.
- Extract the objective value as the minimum number of unique labels.
- For each vertex `i`, find the label `k` where `x[i,k].X > 0.5`.

### Step 4 - Validate Solution
- Iterate over all edges `(i,j)` and confirm `label[i] != label[j]`.
- Confirm every vertex has exactly one label assigned.

### Code Usage
```python
import pulp

# Define data
vertices = list(range(num_vertices))
edges = [(u, v) for u, v in conflict_pairs]
labels = list(range(num_vertices))  # upper bound

# Create model
model = pulp.LpProblem("MinLabels", pulp.LpMinimize)

# Variables
x = pulp.LpVariable.dicts("x", (vertices, labels), cat="Binary")
y = pulp.LpVariable.dicts("y", labels, cat="Binary")

# Objective
model += pulp.lpSum(y[k] for k in labels)

# Constraints
for i in vertices:
    model += pulp.lpSum(x[i][k] for k in labels) == 1

for (i, j) in edges:
    for k in labels:
        model += x[i][k] + x[j][k] <= 1

for i in vertices:
    for k in labels:
        model += x[i][k] <= y[k]

# Solve
model.solve(pulp.PULP_CBC_CMD(msg=False, timeLimit=[TIME_LIMIT]))

# Check status
if pulp.LpStatus[model.status] in ["Optimal", "Feasible"]:
    min_labels = int(pulp.value(model.objective))
    assignment = {}
    for i in vertices:
        for k in labels:
            if pulp.value(x[i][k]) > 0.5:
                assignment[i] = k
                break
    # Validate
    for (u, v) in edges:
        assert assignment[u] != assignment[v], f"Conflict at edge ({u},{v})"
else:
    raise RuntimeError(f"Solver failed with status: {pulp.LpStatus[model.status]}")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, causing runtime errors.
- Assuming the solver will always return an optimal solution; always handle infeasible or unbounded statuses.
- Using a time limit too short for large instances, resulting in suboptimal or no solution.

# Workflow 2 (Constraint Programming with CP-SAT)

## Modeling stage

### Strategy Overview
Formulate as a Constraint Satisfaction/Optimization Problem (CSP/COP) using integer variables for each vertex's label assignment. Use pairwise inequality constraints on edges. Minimize the number of distinct labels by introducing auxiliary boolean variables to track label usage and an objective variable for the count.

### Step 1 - Define Sets and Parameters
- Define the set of vertices `V`.
- Define the set of edges `E`.
- Define an upper bound `K_max` equal to `|V|`.

### Step 2 - Create Decision Variables
- Create integer variable `label[i]` for each vertex `i`, with domain `[0, K_max-1]`.
- Create boolean variable `used[k]` for each possible label `k`, indicating if any vertex uses that label.
- Create integer variable `num_labels` representing the count of distinct labels used.

### Step 3 - Enforce Neighbor Conflict Constraints
- For each edge `(i,j)` in `E`, add constraint: `label[i] != label[j]`.

### Step 4 - Link Used Variables to Labels
- For each vertex `i` and label `k`, create an intermediate boolean variable `is_equal[i][k]`.
- Add constraints: `label[i] == k` implies `is_equal[i][k] == true`, and `label[i] != k` implies `is_equal[i][k] == false`.
- For each label `k`, enforce `used[k] >= is_equal[i][k]` for all vertices `i`. This ensures `used[k]` is true if any vertex uses label `k`.
- Set `num_labels` equal to the sum of `used[k]`.

### Step 5 - Set Objective
- Minimize `num_labels`.

### Formulation Template
```json
{
  "sets": ["V: vertices", "E: edges (conflicts)"],
  "parameters": ["K_max: upper bound on labels (|V|)"],
  "decision_variables": [
    "label[i] integer in [0, K_max-1]: assigned label for vertex i",
    "is_equal[i][k] boolean: true if label[i] == k",
    "used[k] boolean: true if label k is used",
    "num_labels integer: total distinct labels used"
  ],
  "objective": {
    "sense": "min",
    "expression": "num_labels"
  },
  "constraints": [
    "label[i] != label[j], for all (i,j) in E",
    "label[i] == k => is_equal[i][k] == true, for all i in V, k in [0, K_max-1]",
    "label[i] != k => is_equal[i][k] == false, for all i in V, k in [0, K_max-1]",
    "used[k] >= is_equal[i][k], for all i in V, k in [0, K_max-1]",
    "num_labels == sum_{k} used[k]"
  ]
}
```

### Common Pitfalls
- Using a domain for `label[i]` that is too small, causing infeasibility.
- Not linking `used[k]` to `label[i]` properly, leading to an incorrect count of distinct labels.
- Forgetting that CP-SAT requires integer variables; using boolean variables for `used[k]` and `is_equal[i][k]` is fine.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver, which is well-suited for combinatorial optimization with integer variables. Set a time limit and enable solution logging if needed. After solving, extract the objective value and decode the assignment.

### Step 1 - Initialize Solver and Model
- Import `ortools.sat.python.cp_model`.
- Create a `CpModel()` instance.

### Step 2 - Build and Solve
- Add variables and constraints as defined.
- Add the objective to minimize `num_labels`.
- Create a `CpSolver()` and set parameters: time limit (`[TIME_LIMIT]` seconds), number of search workers.

### Step 3 - Check Status and Extract Results
- Check solver status: `OPTIMAL` or `FEASIBLE`.
- Extract `num_labels` value and `label[i]` for each vertex.

### Step 4 - Validate Solution
- Verify all edge constraints are satisfied.
- Confirm the number of distinct labels matches the objective value.

### Step 5 - Prove Optimality via Feasibility Check (Optional)
- After finding a solution with `K` colors, to prove optimality, attempt to solve the problem with `K-1` colors (by adding a constraint `num_labels <= K-1`). If the solver returns `INFEASIBLE`, then `K` is optimal.

### Code Usage
```python
from ortools.sat.python import cp_model

# Define data
vertices = list(range(num_vertices))
edges = [(u, v) for u, v in conflict_pairs]
K_max = num_vertices

# Create model
model = cp_model.CpModel()

# Variables
label = [model.NewIntVar(0, K_max - 1, f"label_{i}") for i in vertices]
used = [model.NewBoolVar(f"used_{k}") for k in range(K_max)]
num_labels = model.NewIntVar(0, K_max, "num_labels")

# Conflict constraints
for (u, v) in edges:
    model.Add(label[u] != label[v])

# Link used to labels
for k in range(K_max):
    vertex_uses_k = []
    for i in vertices:
        is_equal = model.NewBoolVar(f"eq_{i}_{k}")
        model.Add(label[i] == k).OnlyEnforceIf(is_equal)
        model.Add(label[i] != k).OnlyEnforceIf(is_equal.Not())
        vertex_uses_k.append(is_equal)
    for i in vertices:
        model.Add(used[k] >= vertex_uses_k[i])

model.Add(num_labels == sum(used))
model.Minimize(num_labels)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

# Check status
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    min_labels = solver.Value(num_labels)
    assignment = {i: solver.Value(label[i]) for i in vertices}
    # Validate
    for (u, v) in edges:
        assert assignment[u] != assignment[v], f"Conflict at edge ({u},{v})"
else:
    raise RuntimeError(f"Solver failed with status: {solver.StatusName(status)}")
```

### Common Pitfalls
- Not setting a time limit, causing the solver to run indefinitely on hard instances.
- Using `OnlyEnforceIf` incorrectly with boolean variables; ensure the implication direction is correct.
- Forgetting to check for `FEASIBLE` status in addition to `OPTIMAL` when a time limit is used.
