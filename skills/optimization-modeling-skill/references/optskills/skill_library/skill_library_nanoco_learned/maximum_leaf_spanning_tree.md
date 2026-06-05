---
name: Maximum Leaf Spanning Tree
description: |
  Models and solves the problem of finding a spanning tree that maximizes the number of leaf nodes, using either a CP-SAT or MILP solver.

---
# Workflow 1 (CP-SAT with Flow Connectivity)

## Modeling stage

### Strategy Overview
Model the problem using binary edge selection variables, integer degree variables, and binary leaf indicators. Enforce connectivity and acyclicity via a single-commodity flow formulation. Use CP-SAT's implication constraints for exact leaf detection.

### Step 1 - Define Edge Selection Variables
- Define a binary variable `x[e]` for each eligible edge `e` in the set `E`.
- `x[e]` is 1 if the edge is selected in the spanning tree, 0 otherwise.

### Step 2 - Enforce Spanning Tree Cardinality
- Add a constraint that exactly `n-1` edges are selected: `sum(x[e] for e in E) == n-1`, where `n` is the number of nodes.

### Step 3 - Compute Node Degrees
- For each node `i`, create an integer variable `deg[i]` with domain `[0, n-1]`.
- Precompute the list of incident edges for each node.
- Add constraints: `deg[i] == sum(x[e] for e incident to i)`.

### Step 4 - Model Leaf Node Indicators
- For each node `i`, create a binary variable `leaf[i]`.
- Use CP-SAT implication constraints to enforce logical equivalence `(deg[i] == 1) ⇔ (leaf[i] == 1)`:
  - `model.Add(deg[i] == 1).OnlyEnforceIf(leaf[i])`
  - `model.Add(deg[i] != 1).OnlyEnforceIf(leaf[i].Not())`

### Step 5 - Enforce Connectivity and Acyclicity via Flow
- Choose a root node `r` (e.g., node 0).
- For each undirected edge `(u,v)`, create two directed flow variables `f[(u,v)]` and `f[(v,u)]` with domain `[0, n-1]`.
- Link flow to edge selection: `f[(u,v)] <= (n-1) * x[e]` and `f[(v,u)] <= (n-1) * x[e]`.
- Flow conservation constraints:
  - For root `r`: `sum(f[(r,j)] for j in neighbors) - sum(f[(j,r)] for j in neighbors) == n-1`
  - For each other node `i`: `sum(f[(j,i)] for j in neighbors) - sum(f[(i,j)] for j in neighbors) == 1`

### Step 6 - Set Objective
- Maximize the total number of leaf nodes: `model.Maximize(sum(leaf[i] for i in nodes))`

### Formulation Template
```json
{
  "sets": {
    "N": "set of nodes, indexed 0..n-1",
    "E": "set of eligible undirected edges (u,v)"
  },
  "parameters": {
    "n": "number of nodes",
    "root": "chosen root node for flow (e.g., 0)"
  },
  "decision_variables": {
    "x[e]": "binary, 1 if edge e is selected",
    "deg[i]": "integer [0, n-1], degree of node i",
    "leaf[i]": "binary, 1 if node i is a leaf",
    "f[(u,v)]": "integer [0, n-1], flow on directed arc (u,v)"
  },
  "objective": {
    "sense": "max",
    "expression": "sum(leaf[i] for i in N)"
  },
  "constraints": [
    "sum(x[e] for e in E) == n-1",
    "deg[i] == sum(x[e] for e incident to i) for all i in N",
    "deg[i] == 1 => leaf[i] == 1 for all i in N",
    "deg[i] != 1 => leaf[i] == 0 for all i in N",
    "f[(u,v)] <= (n-1) * x[(u,v)] for all (u,v) in directed arcs",
    "f[(v,u)] <= (n-1) * x[(u,v)] for all (u,v) in directed arcs",
    "flow conservation at root: outflow - inflow == n-1",
    "flow conservation at non-root: inflow - outflow == 1"
  ]
}
```

### Common Pitfalls
- Forgetting to create both directed flow variables for each undirected edge.
- Using incorrect flow conservation signs (root sends out, others receive).
- Not linking flow variables to edge selection, allowing flow on unselected edges.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver to handle the binary and integer variables efficiently. Set a time limit and verify solution validity post-solve.

### Step 1 - Initialize Solver and Set Parameters
- Create a `cp_model.CpSolver` instance.
- Set a time limit: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`.
- Optionally enable logging: `solver.parameters.log_search_progress = True`.

### Step 2 - Solve the Model
- Call `status = solver.Solve(model)`.
- Check the status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.

### Step 3 - Extract and Verify Solution
- Extract objective value: `solver.ObjectiveValue()`.
- Extract selected edges: `[e for e in E if solver.Value(x[e]) > 0.5]`.
- **Verification checks**:
  - Verify exactly `n-1` edges are selected.
  - Verify connectivity using BFS/DFS from the root on selected edges.
  - Verify acyclicity (automatically satisfied if connected with `n-1` edges).
  - Compute degrees and confirm leaf nodes match `leaf` variables.
- If any check fails, treat the solution as invalid.

### Step 4 - Output Results
- Print a structured result (e.g., JSON) with status, objective value, leaf list, selected edges, and degrees.

### Code Usage
```python
from ortools.sat.python import cp_model

def build_and_solve_max_leaf_spanning_tree(nodes, eligible_edges, root=0, time_limit=60):
    model = cp_model.CpModel()
    n = len(nodes)
    edge_list = list(eligible_edges)
    
    # Decision variables
    x = {e: model.NewBoolVar(f'x_{e[0]}_{e[1]}') for e in edge_list}
    deg = {i: model.NewIntVar(0, n-1, f'deg_{i}') for i in nodes}
    leaf = {i: model.NewBoolVar(f'leaf_{i}') for i in nodes}
    
    # Flow variables
    f = {}
    for (u,v) in edge_list:
        f[(u,v)] = model.NewIntVar(0, n-1, f'f_{u}_{v}')
        f[(v,u)] = model.NewIntVar(0, n-1, f'f_{v}_{u}')
    
    # Spanning tree cardinality
    model.Add(sum(x[e] for e in edge_list) == n-1)
    
    # Degree constraints
    incident_edges = {i: [] for i in nodes}
    for e in edge_list:
        u, v = e
        incident_edges[u].append(x[e])
        incident_edges[v].append(x[e])
    for i in nodes:
        model.Add(deg[i] == sum(incident_edges[i]))
    
    # Leaf detection
    for i in nodes:
        model.Add(deg[i] == 1).OnlyEnforceIf(leaf[i])
        model.Add(deg[i] != 1).OnlyEnforceIf(leaf[i].Not())
    
    # Flow constraints
    for (u,v) in edge_list:
        model.Add(f[(u,v)] <= (n-1) * x[(u,v)])
        model.Add(f[(v,u)] <= (n-1) * x[(u,v)])
    
    # Flow conservation
    for i in nodes:
        outflow = sum(f[(i,j)] for (a,b) in edge_list for (i2,j) in [(a,b),(b,a)] if i2 == i)
        inflow = sum(f[(j,i)] for (a,b) in edge_list for (j,i2) in [(a,b),(b,a)] if i2 == i)
        if i == root:
            model.Add(outflow - inflow == n-1)
        else:
            model.Add(inflow - outflow == 1)
    
    # Objective
    model.Maximize(sum(leaf[i] for i in nodes))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    status = solver.Solve(model)
    
    # Result parsing
    result = {"status": solver.StatusName(status), "objective": None, "edges": [], "leaves": []}
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        result["objective"] = solver.ObjectiveValue()
        result["edges"] = [e for e in edge_list if solver.Value(x[e]) > 0.5]
        result["leaves"] = [i for i in nodes if solver.Value(leaf[i]) > 0.5]
    return result
```

### Common Pitfalls
- Not checking solver status before reading variable values, leading to runtime errors.
- Using too large a flow domain (`n-1` is sufficient; larger values slow the solver).
- Forgetting that CP-SAT requires explicit `OnlyEnforceIf` for implications.

# Workflow 2 (MILP with Linear Leaf Detection)

## Modeling stage

### Strategy Overview
Formulate as a Mixed Integer Linear Program (MILP) using binary edge and leaf variables. Enforce connectivity and acyclicity via single-commodity flow. Use linear constraints to link degree to leaf status, relying on the objective to enforce correctness.

### Step 1 - Define Edge Selection Variables
- Define a binary variable `x[e]` for each eligible edge `e` in the set `E`.
- `x[e]` is 1 if the edge is selected, 0 otherwise.

### Step 2 - Enforce Spanning Tree Cardinality
- Add constraint: `sum(x[e] for e in E) == n-1`.

### Step 3 - Compute Node Degrees
- For each node `i`, define `deg[i]` as the sum of incident selected edges: `deg[i] = sum(x[e] for e incident to i)`.

### Step 4 - Model Leaf Node Indicators with Linear Constraints
- For each node `i`, define a binary variable `y[i]` indicating if it is a leaf.
- Add constraints:
  - `y[i] <= deg[i]` (leaf implies degree >= 1).
  - `deg[i] <= 1 + (n-1) * (1 - y[i])` (if leaf, degree <= 1; otherwise, no restriction).
- Since the objective maximizes leaf count, the solver will set `y[i]=1` exactly when `deg[i]==1`.

### Step 5 - Enforce Connectivity and Acyclicity via Flow
- Choose a root node `r`.
- For each undirected edge `(u,v)`, create two directed flow variables `f[(u,v)]` and `f[(v,u)]` with domain `[0, n-1]`.
- Link flow to edge selection: `f[(u,v)] <= (n-1) * x[e]` and `f[(v,u)] <= (n-1) * x[e]`.
- Flow conservation:
  - Root: `outflow - inflow == n-1`.
  - Non-root: `inflow - outflow == 1`.

### Step 6 - Set Objective
- Maximize the sum of leaf indicators: `maximize sum(y[i] for i in nodes)`.

### Formulation Template
```json
{
  "sets": {
    "N": "set of nodes, indexed 0..n-1",
    "E": "set of eligible undirected edges (u,v)"
  },
  "parameters": {
    "n": "number of nodes",
    "root": "chosen root node for flow (e.g., 0)"
  },
  "decision_variables": {
    "x[e]": "binary, 1 if edge e is selected",
    "y[i]": "binary, 1 if node i is a leaf",
    "f[(u,v)]": "continuous [0, n-1], flow on directed arc (u,v)"
  },
  "objective": {
    "sense": "max",
    "expression": "sum(y[i] for i in N)"
  },
  "constraints": [
    "sum(x[e] for e in E) == n-1",
    "deg[i] = sum(x[e] for e incident to i) for all i in N",
    "y[i] <= deg[i] for all i in N",
    "deg[i] <= 1 + (n-1) * (1 - y[i]) for all i in N",
    "f[(u,v)] <= (n-1) * x[(u,v)] for all (u,v) in directed arcs",
    "f[(v,u)] <= (n-1) * x[(u,v)] for all (u,v) in directed arcs",
    "flow conservation at root: outflow - inflow == n-1",
    "flow conservation at non-root: inflow - outflow == 1"
  ]
}
```

### Common Pitfalls
- Using `deg[i] <= 1 + M * (1 - y[i])` with too large `M` (use `n-1` for tightness).
- Confusing flow conservation signs between root and non-root nodes.
- Not ensuring flow variables are bounded by edge selection, allowing cycles.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., CBC via `mip` library or `pulp`). Set a time limit and optimality gap. Verify solution validity post-solve.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `mip.CBC` or `pulp.PULP_CBC_CMD`).
- Set a time limit: `solver.seconds = [TIME_LIMIT]`.
- Set optimality gap: `solver.emphasis = 0` (optimal) or `solver.max_mip_gap = 0.0`.

### Step 2 - Solve the Model
- Call `status = model.optimize()`.
- Check status: `status == mip.OptimizationStatus.OPTIMAL` or `status == mip.OptimizationStatus.FEASIBLE`.

### Step 3 - Extract and Verify Solution
- Extract objective value: `model.objective_value`.
- Extract selected edges: `[e for e in E if x[e].x > 0.5]`.
- **Verification checks**:
  - Verify exactly `n-1` edges are selected.
  - Verify connectivity using BFS/DFS from the root.
  - Verify acyclicity (automatically satisfied if connected with `n-1` edges).
  - Compute degrees and confirm leaf nodes match `y` variables.
- If any check fails, treat the solution as invalid.

### Step 4 - Output Results
- Print a structured result (e.g., JSON) with status, objective value, leaf list, selected edges, and degrees.

### Code Usage
```python
import mip

def build_and_solve_max_leaf_spanning_tree_milp(nodes, eligible_edges, root=0, time_limit=60):
    n = len(nodes)
    edge_list = list(eligible_edges)
    
    model = mip.Model("MaxLeafSpanningTree")
    
    # Decision variables
    x = {e: model.add_var(var_type=mip.BINARY, name=f'x_{e[0]}_{e[1]}') for e in edge_list}
    y = {i: model.add_var(var_type=mip.BINARY, name=f'y_{i}') for i in nodes}
    f = {}
    for (u,v) in edge_list:
        f[(u,v)] = model.add_var(lb=0, ub=n-1, name=f'f_{u}_{v}')
        f[(v,u)] = model.add_var(lb=0, ub=n-1, name=f'f_{v}_{u}')
    
    # Spanning tree cardinality
    model += mip.xsum(x[e] for e in edge_list) == n-1
    
    # Degree and leaf constraints
    incident_edges = {i: [] for i in nodes}
    for e in edge_list:
        u, v = e
        incident_edges[u].append(x[e])
        incident_edges[v].append(x[e])
    for i in nodes:
        deg = mip.xsum(incident_edges[i])
        model += y[i] <= deg
        model += deg <= 1 + (n-1) * (1 - y[i])
    
    # Flow constraints
    for (u,v) in edge_list:
        model += f[(u,v)] <= (n-1) * x[(u,v)]
        model += f[(v,u)] <= (n-1) * x[(u,v)]
    
    # Flow conservation
    for i in nodes:
        outflow = mip.xsum(f[(i,j)] for (a,b) in edge_list for (i2,j) in [(a,b),(b,a)] if i2 == i)
        inflow = mip.xsum(f[(j,i)] for (a,b) in edge_list for (j,i2) in [(a,b),(b,a)] if i2 == i)
        if i == root:
            model += outflow - inflow == n-1
        else:
            model += inflow - outflow == 1
    
    # Objective
    model.objective = mip.maximize(mip.xsum(y[i] for i in nodes))
    
    # Solve
    model.optimize(max_seconds=time_limit)
    
    # Result parsing
    result = {"status": str(model.status), "objective": None, "edges": [], "leaves": []}
    if model.status in (mip.OptimizationStatus.OPTIMAL, mip.OptimizationStatus.FEASIBLE):
        result["objective"] = model.objective_value
        result["edges"] = [e for e in edge_list if x[e].x > 0.5]
        result["leaves"] = [i for i in nodes if y[i].x > 0.5]
    return result
```

### Common Pitfalls
- Not checking solver status before accessing `.x` values, causing attribute errors.
- Using `mip.xsum` incorrectly with generator expressions (wrap in list if needed).
- Forgetting to set a time limit, causing indefinite solve on large instances.
