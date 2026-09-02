---
name: Maximum Weight Assignment with Capacity Constraints
description: |
  Models and solves a maximum weight assignment problem where each resource has a capacity limit on the number of incident assignments it can participate in, using either CP-SAT or MILP solvers.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Model the problem as a binary assignment problem with per-node degree constraints. Use Google OR-Tools CP-SAT solver, which is well-suited for combinatorial optimization with binary variables and linear constraints.

### Step 1 - Define Decision Variables
- For each potential assignment (edge/link), create a binary variable `x_e` indicating whether that assignment is selected.
- Use `model.NewBoolVar(name)` for each variable, with a descriptive name like `"x_{i}_{j}"`.

### Step 2 - Define Capacity Constraints
- For each resource (node/cell) with a finite capacity, sum the binary variables of all incident assignments.
- Enforce `sum(x_e for e incident to i) <= capacity[i]` using `model.Add()`.
- This models the constraint that each resource can be involved in at most a given number of assignments.

### Step 3 - Define Objective Function
- Maximize the total weighted sum of selected assignments.
- Use `model.Maximize(sum(weight[e] * x_e for e in edges))` to directly encode the goal of maximizing total value.

### Formulation Template
```json
{
  "sets": ["E: set of edges/assignments", "N: set of nodes/resources"],
  "parameters": ["weight[e]: weight of edge e", "capacity[n]: capacity of node n", "incident_edges[n]: list of edges incident to node n"],
  "decision_variables": ["x[e]: binary variable indicating if edge e is selected"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[e] * x[e] for e in E)"
  },
  "constraints": ["sum(x[e] for e in incident_edges[n]) <= capacity[n] for all n in N"]
}
```

### Common Pitfalls
- Forgetting to convert node indices to integers when using them in variable names or constraint indexing.
- Using `model.Add(sum(...))` without wrapping in parentheses for multi-line expressions.
- Not storing incident edges per node in a precomputed list, leading to O(n*m) constraint generation.

## Solving stage

### Strategy Overview
Use CP-SAT solver with parallel search and time limits. Extract solution by checking variable values and validate capacity constraints manually.

### Step 1 - Configure Solver
- Create `CpSolver()` instance.
- Set `max_time_in_seconds` to a reasonable limit (e.g., 30 seconds) to avoid indefinite runtime.
- Enable `num_search_workers = 8` for parallel search.
- Set `random_seed = 42` for reproducibility.
- Use `relative_gap_limit = 0.0` to require optimality proof.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if `status` is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.
- For infeasible/unbounded cases, print a JSON with `status: "failed"` and a descriptive reason.

### Step 3 - Extract Solution
- Iterate over all variables and collect those with `solver.Value(x_e) == 1` to get the selected assignments.
- Compute the objective value via `solver.ObjectiveValue()`.
- Build structured output (e.g., JSON) containing status, objective value, and list of selected edges.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# Data preparation
edges = [(i, j, weight) for ...]  # list of tuples
capacities = {node: cap for node, cap in ...}
incident_edges = {node: [] for node in capacities}
for idx, (i, j, w) in enumerate(edges):
    incident_edges[i].append(idx)
    incident_edges[j].append(idx)

# Build model
model = cp_model.CpModel()
x = {}
for idx, (i, j, w) in enumerate(edges):
    x[idx] = model.NewBoolVar(f"x_{i}_{j}")

# Capacity constraints
for node, cap in capacities.items():
    model.Add(sum(x[idx] for idx in incident_edges[node]) <= cap)

# Objective
model.Maximize(sum(w * x[idx] for idx, (_, _, w) in enumerate(edges)))

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

# Extract results
if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    selected = []
    for idx, (i, j, w) in enumerate(edges):
        if solver.Value(x[idx]) == 1:
            selected.append({"edge": idx, "nodes": (i, j), "weight": w})
    payload = {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "objective": solver.ObjectiveValue(),
        "selected_edges": selected
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
else:
    payload = {"status": "failed", "reason": "infeasible_or_error"}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking for `cp_model.FEASIBLE` in addition to `cp_model.OPTIMAL`, missing valid solutions when optimality is not proven.
- Forgetting to convert `solver.ObjectiveValue()` to float for JSON serialization.
- Not precomputing incident edges per node, causing O(n*m) runtime in solution extraction.

# Workflow 2 (MILP Solver)

## Modeling stage

### Strategy Overview
Model the problem as a mixed-integer linear program (MILP) using Pyomo. Use binary decision variables for each assignment and linear capacity constraints. This approach allows using high-performance MILP solvers like HiGHS or CBC.

### Step 1 - Define Sets and Parameters
- Create a Pyomo Set for edges/links: `m.E = pyo.Set(initialize=range(len(edges_data)))`.
- Create a Pyomo Set for nodes/resources: `m.N = pyo.Set(initialize=nodes)`.
- Store weights in a dictionary keyed by edge index.
- Store edge-node relationships in a dictionary keyed by edge index.

### Step 2 - Define Decision Variables
- Define binary variables for each edge: `m.x = pyo.Var(m.E, domain=pyo.Binary)`.
- Use descriptive variable names for debugging.

### Step 3 - Define Objective Function
- Maximize total weighted sum: `m.obj = pyo.Objective(expr=sum(weights[e] * m.x[e] for e in m.E), sense=pyo.maximize)`.

### Step 4 - Define Capacity Constraints
- For each node, create a constraint rule that sums binary variables of incident edges.
- Use `pyo.Constraint(m.N, rule=capacity_rule)` where `capacity_rule` checks if node is in edge's node tuple.

### Formulation Template
```json
{
  "sets": ["E: set of edges/assignments", "N: set of nodes/resources"],
  "parameters": ["weight[e]: weight of edge e", "capacity[n]: capacity of node n", "edge_nodes[e]: tuple of (node1, node2) for edge e"],
  "decision_variables": ["x[e]: binary variable indicating if edge e is selected"],
  "objective": {
    "sense": "max",
    "expression": "sum(weight[e] * x[e] for e in E)"
  },
  "constraints": ["sum(x[e] for e in E if n in edge_nodes[e]) <= capacity[n] for all n in N"]
}
```

### Common Pitfalls
- Using `pyo.Set(initialize=edges_data)` directly instead of initializing with indices, causing indexing issues.
- Not converting node indices to integers when checking membership in edge tuples.
- Forgetting to use `pyo.value()` when extracting variable values after solving.

## Solving stage

### Strategy Overview
Use a high-performance MILP solver (HiGHS or CBC) with time limits and MIP gap tolerance. Extract solution by checking variable values and validate capacity constraints manually.

### Step 1 - Configure Solver
- Use `pyo.SolverFactory("highs")` for high-performance MILP solving, or `pyo.SolverFactory("cbc")` for open-source alternative.
- Set key options: `time_limit=30`, `mip_rel_gap=0.0`, `threads=4`.
- For CBC, use `solver.options["seconds"] = 30` and `solver.options["ratio"] = 0.0`.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == SolverStatus.ok` and `term in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- For infeasible/unbounded cases, print a JSON with `status: "failed"` and descriptive reason.

### Step 3 - Extract Solution
- Retrieve selected variables with `[e for e in m.E if pyo.value(m.x[e]) > 0.5]`.
- Convert to native Python types (e.g., `int(a), int(b)`) for JSON serialization.
- Build structured output (e.g., JSON) containing status, objective value, and list of selected edges.

### Code Usage
```python
import json
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data preparation
nodes = list(range(num_nodes))
capacities = {node: cap_value for node in nodes}
edges_data = [(i, j, weight) for ...]  # list of tuples

# Build model
m = pyo.ConcreteModel()
m.E = pyo.Set(initialize=range(len(edges_data)))
m.N = pyo.Set(initialize=nodes)

weights = {e: edges_data[e][2] for e in m.E}
edge_nodes = {e: (edges_data[e][0], edges_data[e][1]) for e in m.E}

m.x = pyo.Var(m.E, domain=pyo.Binary)
m.obj = pyo.Objective(expr=sum(weights[e] * m.x[e] for e in m.E), sense=pyo.maximize)

def capacity_rule(model, n):
    return sum(model.x[e] for e in model.E if n in edge_nodes[e]) <= capacities[n]

m.capacity = pyo.Constraint(m.N, rule=capacity_rule)

# Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4
results = solver.solve(m, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    selected = []
    for e in m.E:
        if pyo.value(m.x[e]) > 0.5:
            selected.append({"edge": e, "nodes": edge_nodes[e], "weight": weights[e]})
    payload = {
        "status": "optimal" if term == TerminationCondition.optimal else "feasible",
        "objective": float(pyo.value(m.obj)),
        "selected_edges": selected,
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
else:
    payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status),
        "termination_condition": str(term),
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking both `SolverStatus.ok` and `TerminationCondition.feasible`, missing valid solutions when optimality is not proven.
- Using `pyo.value()` on the entire variable object instead of individual variable values.
- Forgetting to convert objective value to float for JSON serialization.
- Not handling the case where solver returns `TerminationCondition.unbounded` separately from infeasible.
