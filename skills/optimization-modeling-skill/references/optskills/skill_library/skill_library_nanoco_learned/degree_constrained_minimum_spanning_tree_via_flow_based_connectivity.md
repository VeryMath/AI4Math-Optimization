---
name: Degree-Constrained Minimum Spanning Tree via Flow-Based Connectivity
description: |
  Build and solve a degree-constrained minimum spanning tree problem using binary edge selection, single-commodity flow for connectivity, and degree constraints, with two solver workflows: one using Pyomo with HiGHS and another using OR-Tools CP-SAT.

---
# Workflow 1 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Model the degree-constrained minimum spanning tree as a mixed-integer linear program using binary edge selection variables for undirected edges. Enforce tree structure via an exact edge count constraint and single-commodity flow for connectivity. Degree constraints limit incident edges per node.

### Step 1 - Define Sets and Parameters
- Define the set of nodes `N` and the set of undirected edges `E` as all unordered pairs `(i,j)` with `i < j`.
- Create a parameter `cost[i,j]` for each edge representing the edge weight.
- Define a parameter `max_degree[v]` for each node `v` in `N`.

### Step 2 - Declare Decision Variables
- Create binary variables `x[i,j]` for each edge `(i,j)` in `E`, indicating whether the edge is selected.
- Create continuous non-negative flow variables `f[i,j]` for each directed arc `(i,j)` with `i != j`. For each undirected edge `(i,j)` in `E`, define both `f[i,j]` and `f[j,i]`.

### Step 3 - Add Constraints
- **Tree cardinality**: `sum(x[i,j] for (i,j) in E) == |N| - 1`
- **Degree constraints**: For each node `v`, `sum(x[i,j] for (i,j) in E if i==v or j==v) <= max_degree[v]`
- **Flow capacity**: For each edge `(i,j)` in `E`, `f[i,j] <= (|N|-1) * x[i,j]` and `f[j,i] <= (|N|-1) * x[i,j]`
- **Flow conservation at root**: Choose an arbitrary root node `r` (e.g., node 0). `sum(f[r,j] for j != r) - sum(f[i,r] for i != r) == |N|-1`
- **Flow conservation at other nodes**: For each node `v != r`, `sum(f[i,v] for i != v) - sum(f[v,j] for j != v) == 1`

### Step 4 - Define Objective
- Minimize total edge cost: `sum(cost[i,j] * x[i,j] for (i,j) in E)`

### Formulation Template
```json
{
  "sets": ["N: nodes", "E: undirected edges (i,j) with i<j"],
  "parameters": ["cost[i,j] for (i,j) in E", "max_degree[v] for v in N"],
  "decision_variables": [
    "x[i,j] binary for (i,j) in E",
    "f[i,j] continuous >=0 for each directed arc (i,j) with i!=j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for (i,j) in E)"
  },
  "constraints": [
    "sum(x[i,j] for (i,j) in E) == |N|-1",
    "for each v in N: sum(x[i,j] for (i,j) in E if i==v or j==v) <= max_degree[v]",
    "for each (i,j) in E: f[i,j] <= (|N|-1) * x[i,j]",
    "for each (i,j) in E: f[j,i] <= (|N|-1) * x[i,j]",
    "root r: sum(f[r,j] for j != r) - sum(f[i,r] for i != r) == |N|-1",
    "for each v != r: sum(f[i,v] for i != v) - sum(f[v,j] for j != v) == 1"
  ]
}
```

### Common Pitfalls
- Forgetting to define flow variables for both directions of each undirected edge, leading to connectivity failures.
- Using `i<j` indexing for edge variables but then referencing `x[j,i]` in flow constraints, causing key errors.
- Setting flow capacity bound too low (must be at least `|N|-1` to allow feasible flow).

## Solving stage

### Strategy Overview
Use HiGHS via Pyomo's solver interface with explicit MILP settings. After solving, validate solver status and termination condition before extracting results. Verify solution feasibility by checking edge count, degrees, and connectivity.

### Step 1 - Configure Solver
- Instantiate solver: `solver = SolverFactory("highs")`
- Set options: `solver.options["time_limit"] = [TIME_LIMIT]`, `solver.options["mip_rel_gap"] = 0.0`, `solver.options["threads"] = [NUM_THREADS]`, `solver.options["presolve"] = "on"`

### Step 2 - Solve and Check Status
- Call `result = solver.solve(model, tee=True)`
- Check `result.solver.status == SolverStatus.ok` and `result.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)`

### Step 3 - Extract and Validate Solution
- Extract selected edges: `[(i,j) for (i,j) in E if pyo.value(model.x[i,j]) > 0.5]`
- Validate: compute `len(selected_edges) == |N|-1`, check each node's degree against `max_degree`, and run BFS/DFS from root to confirm all nodes are reachable.

### Code Usage
```python
import pyomo.environ as pyo

def build_dcmst_model(N, edges, cost, max_degree, root=0):
    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=N)
    model.E = pyo.Set(initialize=edges, dimen=2)
    
    model.cost = pyo.Param(model.E, initialize=cost)
    model.max_degree = pyo.Param(model.N, initialize=max_degree)
    
    model.x = pyo.Var(model.E, domain=pyo.Binary)
    # Flow variables for all directed arcs
    model.arcs = pyo.Set(initialize=[(i,j) for i in N for j in N if i != j], dimen=2)
    model.f = pyo.Var(model.arcs, domain=pyo.NonNegativeReals)
    
    # Tree cardinality
    model.cardinality = pyo.Constraint(expr=sum(model.x[i,j] for (i,j) in model.E) == len(N)-1)
    
    # Degree constraints
    def degree_rule(m, v):
        return sum(m.x[i,j] for (i,j) in m.E if i==v or j==v) <= m.max_degree[v]
    model.degree = pyo.Constraint(model.N, rule=degree_rule)
    
    # Flow capacity
    def flow_cap_rule(m, i, j):
        return m.f[i,j] <= (len(N)-1) * m.x[i,j]
    model.flow_cap = pyo.Constraint(model.E, rule=flow_cap_rule)
    
    def flow_cap_rev_rule(m, i, j):
        return m.f[j,i] <= (len(N)-1) * m.x[i,j]
    model.flow_cap_rev = pyo.Constraint(model.E, rule=flow_cap_rev_rule)
    
    # Flow conservation at root
    root_out = sum(model.f[root,j] for j in N if j != root)
    root_in = sum(model.f[i,root] for i in N if i != root)
    model.root_flow = pyo.Constraint(expr=root_out - root_in == len(N)-1)
    
    # Flow conservation at other nodes
    def flow_cons_rule(m, v):
        if v == root:
            return pyo.Constraint.Skip
        inflow = sum(m.f[i,v] for i in N if i != v)
        outflow = sum(m.f[v,j] for j in N if j != v)
        return inflow - outflow == 1
    model.flow_cons = pyo.Constraint(model.N, rule=flow_cons_rule)
    
    # Objective
    model.obj = pyo.Objective(expr=sum(model.cost[i,j] * model.x[i,j] for (i,j) in model.E), sense=pyo.minimize)
    
    return model

# Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = [TIME_LIMIT]
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = [NUM_THREADS]
solver.options["presolve"] = "on"
result = solver.solve(model, tee=True)

# Check status
if result.solver.status == pyo.SolverStatus.ok and result.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    selected = [(i,j) for (i,j) in model.E if pyo.value(model.x[i,j]) > 0.5]
    obj_val = pyo.value(model.obj)
    # Validate
    assert len(selected) == len(N)-1
    # BFS connectivity check
    adj = {v: [] for v in N}
    for i,j in selected:
        adj[i].append(j)
        adj[j].append(i)
    visited = set()
    stack = [root]
    while stack:
        v = stack.pop()
        if v not in visited:
            visited.add(v)
            stack.extend(adj[v])
    assert len(visited) == len(N)
else:
    print("Solver failed:", result.solver.status, result.solver.termination_condition)
```

### Common Pitfalls
- Not checking `termination_condition` for `feasible` in addition to `optimal`, which may discard valid solutions when time limit is hit.
- Using `tee=False` during development, making it hard to diagnose solver issues.
- Forgetting to convert `pyo.value()` for flow variables when validating connectivity.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Model the degree-constrained minimum spanning tree using OR-Tools CP-SAT with boolean variables for edge selection and integer flow variables. Leverage CP-SAT's native support for boolean variables and linear constraints. Use single-commodity flow for connectivity enforcement.

### Step 1 - Define Data Structures
- Create a list of nodes `range(n)` and a list of undirected edges as tuples `(i,j)` with `i<j`.
- Store edge costs in a dictionary `cost[(i,j)]`.
- Define `max_degree` per node.

### Step 2 - Declare Decision Variables
- For each undirected edge `(i,j)`, create a boolean variable: `x[(i,j)] = model.NewBoolVar(f"x_{i}_{j}")`
- For each directed arc `(i,j)` with `i != j`, create an integer variable: `f[(i,j)] = model.NewIntVar(0, n, f"f_{i}_{j}")`

### Step 3 - Add Constraints
- **Tree cardinality**: `model.Add(sum(x[(i,j)] for (i,j) in edges) == n-1)`
- **Degree constraints**: For each node `v`, `model.Add(sum(x[(i,j)] for (i,j) in edges if i==v or j==v) <= max_degree[v])`
- **Flow capacity**: For each undirected edge `(i,j)`, `model.Add(f[(i,j)] <= n * x[(i,j)])` and `model.Add(f[(j,i)] <= n * x[(i,j)])`
- **Flow conservation at root** (node 0): `model.Add(sum(f[(0,j)] for j in range(1,n)) - sum(f[(j,0)] for j in range(1,n)) == n-1)`
- **Flow conservation at other nodes**: For each node `v != 0`, `model.Add(sum(f[(i,v)] for i in range(n) if i!=v) - sum(f[(v,j)] for j in range(n) if j!=v) == 1)`

### Step 4 - Define Objective
- `model.Minimize(sum(cost[(i,j)] * x[(i,j)] for (i,j) in edges))`

### Formulation Template
```json
{
  "sets": ["nodes: range(n)", "edges: undirected pairs (i,j) with i<j"],
  "parameters": ["cost[(i,j)] for each edge", "max_degree[v] for each node v"],
  "decision_variables": [
    "x[(i,j)] boolean for each undirected edge",
    "f[(i,j)] integer in [0, n] for each directed arc"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[(i,j)] * x[(i,j)] for (i,j) in edges)"
  },
  "constraints": [
    "sum(x[(i,j)] for (i,j) in edges) == n-1",
    "for each v: sum(x[(i,j)] for (i,j) in edges if i==v or j==v) <= max_degree[v]",
    "for each (i,j) in edges: f[(i,j)] <= n * x[(i,j)]",
    "for each (i,j) in edges: f[(j,i)] <= n * x[(i,j)]",
    "root 0: sum(f[(0,j)] for j!=0) - sum(f[(j,0)] for j!=0) == n-1",
    "for each v!=0: sum(f[(i,v)] for i!=v) - sum(f[(v,j)] for j!=v) == 1"
  ]
}
```

### Common Pitfalls
- Using `x[(i,j)]` for undirected edges but then referencing `x[(j,i)]` in flow constraints, which doesn't exist.
- Setting flow variable upper bound too low (must be at least `n` to allow feasible flow from root).
- Forgetting that CP-SAT requires all variables to have explicit bounds.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with parallel search and optimality gap control. After solving, check status for OPTIMAL or FEASIBLE. Extract selected edges and validate solution properties.

### Step 1 - Configure Solver
- Instantiate: `solver = cp_model.CpSolver()`
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = [NUM_WORKERS]`, `solver.parameters.random_seed = 42`, `solver.parameters.relative_gap_limit = 0.0`

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`
- Check `status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`

### Step 3 - Extract and Validate Solution
- Extract selected edges: `[(i,j) for (i,j) in edges if solver.Value(x[(i,j)]) == 1]`
- Validate: check edge count equals `n-1`, compute degrees, and run BFS/DFS from root to confirm connectivity.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_dcmst_cpsat(n, edges, cost, max_degree, root=0, time_limit=60):
    model = cp_model.CpModel()
    
    # Variables
    x = {}
    for (i,j) in edges:
        x[(i,j)] = model.NewBoolVar(f"x_{i}_{j}")
    
    f = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                f[(i,j)] = model.NewIntVar(0, n, f"f_{i}_{j}")
    
    # Tree cardinality
    model.Add(sum(x[(i,j)] for (i,j) in edges) == n-1)
    
    # Degree constraints
    for v in range(n):
        incident = [x[(i,j)] for (i,j) in edges if i==v or j==v]
        model.Add(sum(incident) <= max_degree[v])
    
    # Flow capacity
    for (i,j) in edges:
        model.Add(f[(i,j)] <= n * x[(i,j)])
        model.Add(f[(j,i)] <= n * x[(i,j)])
    
    # Flow conservation at root
    root_out = sum(f[(root,j)] for j in range(n) if j != root)
    root_in = sum(f[(j,root)] for j in range(n) if j != root)
    model.Add(root_out - root_in == n-1)
    
    # Flow conservation at other nodes
    for v in range(n):
        if v == root:
            continue
        inflow = sum(f[(i,v)] for i in range(n) if i != v)
        outflow = sum(f[(v,j)] for j in range(n) if j != v)
        model.Add(inflow - outflow == 1)
    
    # Objective
    model.Minimize(sum(cost[(i,j)] * x[(i,j)] for (i,j) in edges))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = [NUM_WORKERS]
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        selected = [(i,j) for (i,j) in edges if solver.Value(x[(i,j)]) == 1]
        obj_val = solver.ObjectiveValue()
        
        # Validate
        assert len(selected) == n-1
        adj = {v: [] for v in range(n)}
        for i,j in selected:
            adj[i].append(j)
            adj[j].append(i)
        visited = set()
        stack = [root]
        while stack:
            v = stack.pop()
            if v not in visited:
                visited.add(v)
                stack.extend(adj[v])
        assert len(visited) == n
        
        return {"status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                "objective": obj_val,
                "edges": selected}
    else:
        return {"status": "INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN"}
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0` when exact optimality is required, as CP-SAT may stop early with a feasible solution.
- Using `solver.Value()` on variables that were not part of the model, causing runtime errors.
- Forgetting that CP-SAT's `NewIntVar` requires explicit bounds; using `n` as upper bound for flow variables is safe but may be tightened to `n-1` for efficiency.
