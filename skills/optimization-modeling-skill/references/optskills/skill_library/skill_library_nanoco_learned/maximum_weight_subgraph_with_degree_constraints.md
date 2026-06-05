---
name: Maximum Weight Subgraph with Degree Constraints
description: |
  Model and solve a maximum weight subgraph selection problem where each node has a capacity limit on the number of incident selected edges.

---
# Workflow 1 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Formulate the problem as a maximum-weight b-matching integer program using OR-Tools CP-SAT. Use binary variables for edge selection, enforce degree constraints per node via precomputed incident lists, and maximize total selected edge weight.

### Step 1 - Define Decision Variables
- Create a `BoolVar` for each edge in the edge list using `model.NewBoolVar(f'x_{i}')`.
- Store variables in a list indexed by edge index for easy access.

### Step 2 - Precompute Incident Edge Lists
- For each node, initialize an empty list.
- For each edge index `i` and its endpoints `(u, v)`, append `i` to the incident lists for `u` and `v`.
- This ensures O(|E|) constraint building.

### Step 3 - Enforce Degree Constraints
- For each node `v` with capacity `c[v]`, add a linear constraint:
  `model.Add(sum(x[idx] for idx in incident[v]) <= c[v])`.
- Isolated nodes (no incident edges) require no constraint.

### Step 4 - Define Objective
- Compute total weight as `sum(edge_weight[i] * x[i] for i in range(num_edges))`.
- Set objective with `model.Maximize(total_weight)`.

### Formulation Template
```json
{
  "sets": ["E: edges", "V: nodes"],
  "parameters": ["w[e]: weight of edge e", "c[v]: capacity of node v", "incident[v]: list of edge indices incident to node v"],
  "decision_variables": ["x[e] ∈ {0,1}: 1 if edge e selected"],
  "objective": {
    "sense": "max",
    "expression": "sum(w[e] * x[e] for e in E)"
  },
  "constraints": ["sum(x[e] for e in incident[v]) <= c[v] for all v in V"]
}
```

### Common Pitfalls
- Forgetting to precompute incident edge lists, leading to O(|V|*|E|) constraint building.
- Using `model.AddBoolOr` or `model.AddBoolAnd` instead of linear sum constraints for degree limits.
- Not handling isolated nodes gracefully; they require no constraint.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with parameters for exact optimality, solve, and parse results with explicit status checking and feasibility verification.

### Step 1 - Configure Solver
- Create `cp_model.CpSolver()` instance.
- Set parameters:
  - `max_time_in_seconds` (e.g., `[TIME_LIMIT]`),
  - `num_search_workers` (e.g., 8),
  - `random_seed` (e.g., 42),
  - `relative_gap_limit = 0.0` to ensure exact optimum.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check status against `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.
- If status is `cp_model.INFEASIBLE`, output failure JSON.

### Step 3 - Extract and Verify Results
- For each edge, check `solver.Value(x[i]) == 1` to identify selected edges.
- Compute objective value as `float(solver.ObjectiveValue())`.
- **Verification:** Recalculate node usage from selected edges to ensure all degree constraints are satisfied.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_max_weight_subgraph(edges, node_capacities):
    """
    edges: list of (u, v, weight)
    node_capacities: dict {node: capacity}
    """
    model = cp_model.CpModel()
    num_edges = len(edges)
    x = [model.NewBoolVar(f'x_{i}') for i in range(num_edges)]
    
    # Build incident edge lists
    incident = {node: [] for node in node_capacities}
    for idx, (u, v, w) in enumerate(edges):
        incident[u].append(idx)
        incident[v].append(idx)
    
    # Degree constraints
    for node, cap in node_capacities.items():
        if incident[node]:
            model.Add(sum(x[idx] for idx in incident[node]) <= cap)
    
    # Objective
    model.Maximize(sum(w * x[i] for i, (_, _, w) in enumerate(edges)))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0
    
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        selected = [(u, v, w) for i, (u, v, w) in enumerate(edges) if solver.Value(x[i]) == 1]
        objective = float(solver.ObjectiveValue())
        # Verification
        node_usage = {node: 0 for node in node_capacities}
        for u, v, _ in selected:
            node_usage[u] += 1
            node_usage[v] += 1
        feasible = all(node_usage[node] <= node_capacities[node] for node in node_capacities)
        return {"status": "success", "objective": objective, "selected_edges": selected, "feasible": feasible}
    else:
        return {"status": "failed", "reason": "no_feasible_solution", "solver_status": status}
```

### Common Pitfalls
- Not setting `relative_gap_limit` to 0.0 when exact optimality is required.
- Forgetting to convert `solver.ObjectiveValue()` to float for JSON serialization.
- Assuming `solver.Value()` returns integer for BoolVar (it returns 0 or 1 as int).

# Workflow 2 (Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Use Pyomo's algebraic modeling language with HiGHS solver. Define sets for edges and nodes, binary variables for edge selection, and linear constraints for degree limits using precomputed incident lists.

### Step 1 - Define Sets and Parameters
- Create `pyomo.Set` for nodes and edges.
- Store edge weights in a dictionary keyed by edge index.
- Store node capacities in a dictionary.

### Step 2 - Precompute Incident Edge Lists
- For each node, initialize an empty list.
- For each edge index and its endpoints `(u, v)`, append the edge index to the incident lists for `u` and `v`.

### Step 3 - Create Decision Variables
- Declare `pyomo.Var(model.E, domain=pyomo.Binary)` for edge selection.

### Step 4 - Write Degree Constraints
- For each node, create a constraint rule that sums binary variables of incident edges.
- Use `pyomo.Constraint(model.V, rule=degree_rule)` where `degree_rule` accesses the precomputed incident list.

### Step 5 - Define Objective
- Use `pyomo.Objective(expr=sum(weight[e] * x[e] for e in model.E), sense=pyomo.maximize)`.

### Formulation Template
```json
{
  "sets": ["E: edges", "V: nodes"],
  "parameters": ["w[e]: weight of edge e", "c[v]: capacity of node v", "incident[v]: list of edges incident to node v"],
  "decision_variables": ["x[e] ∈ {0,1}: 1 if edge e selected"],
  "objective": {
    "sense": "max",
    "expression": "sum(w[e] * x[e] for e in E)"
  },
  "constraints": ["sum(x[e] for e in incident[v]) <= c[v] for all v in V"]
}
```

### Common Pitfalls
- Using `pyomo.Set(initialize=...)` with mutable objects that cause indexing errors.
- Not precomputing incident edge lists inside the constraint rule, causing repeated computation.
- Forgetting to handle isolated nodes (they require no constraint).

## Solving stage

### Strategy Overview
Configure HiGHS solver with time limit and zero MIP gap tolerance, solve, and parse results with proper status checking and feasibility verification.

### Step 1 - Configure Solver
- Use `pyomo.SolverFactory("highs")` to create solver instance.
- Set options:
  - `"time_limit"` (e.g., `[TIME_LIMIT]`),
  - `"mip_rel_gap" = 0.0` for exact optimum,
  - `"threads"` (e.g., 4).

### Step 2 - Solve and Check Status
- Call `result = solver.solve(model, tee=False)`.
- Check `result.solver.status == SolverStatus.ok` and `termination_condition` in `{TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Verify Results
- For each edge, check `pyo.value(x[e]) > 0.5` to identify selected edges.
- Compute objective value as `float(pyo.value(model.obj))`.
- **Verification:** Recalculate node usage from selected edges to ensure all degree constraints are satisfied.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_max_weight_subgraph_pyomo(edges, node_capacities):
    """
    edges: list of (u, v, weight)
    node_capacities: dict {node: capacity}
    """
    model = pyo.ConcreteModel()
    
    # Sets
    edge_indices = list(range(len(edges)))
    node_set = list(node_capacities.keys())
    model.E = pyo.Set(initialize=edge_indices)
    model.V = pyo.Set(initialize=node_set)
    
    # Parameters
    weight = {i: w for i, (_, _, w) in enumerate(edges)}
    model.w = pyo.Param(model.E, initialize=weight)
    
    # Incident edges per node
    incident = {node: [] for node in node_set}
    for idx, (u, v, _) in enumerate(edges):
        incident[u].append(idx)
        incident[v].append(idx)
    
    # Variables
    model.x = pyo.Var(model.E, domain=pyo.Binary)
    
    # Constraints
    def degree_rule(model, node):
        if not incident[node]:
            return pyo.Constraint.Skip
        return sum(model.x[e] for e in incident[node]) <= node_capacities[node]
    model.degree_con = pyo.Constraint(model.V, rule=degree_rule)
    
    # Objective
    model.obj = pyo.Objective(expr=sum(model.w[e] * model.x[e] for e in model.E), sense=pyo.maximize)
    
    # Solve
    solver = pyo.SolverFactory("highs")
    solver.options["time_limit"] = 30
    solver.options["mip_rel_gap"] = 0.0
    solver.options["threads"] = 4
    
    result = solver.solve(model, tee=False)
    
    if (result.solver.status == SolverStatus.ok and
        result.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
        selected = [(u, v, w) for i, (u, v, w) in enumerate(edges) if pyo.value(model.x[i]) > 0.5]
        objective = float(pyo.value(model.obj))
        # Verification
        node_usage = {node: 0 for node in node_capacities}
        for u, v, _ in selected:
            node_usage[u] += 1
            node_usage[v] += 1
        feasible = all(node_usage[node] <= node_capacities[node] for node in node_capacities)
        return {"status": "success", "objective": objective, "selected_edges": selected, "feasible": feasible}
    else:
        return {
            "status": "failed",
            "reason": "solver_error",
            "solver_status": str(result.solver.status),
            "termination_condition": str(result.solver.termination_condition)
        }
```

### Common Pitfalls
- Not checking `termination_condition` in addition to `solver.status` for feasible solutions.
- Using `tee=True` in production code, which floods output with solver logs.
- Forgetting to convert `pyo.value()` results to native Python types for JSON serialization.
