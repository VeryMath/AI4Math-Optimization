---
name: Maximum Cardinality Matching via Binary Edge Assignment
description: |
  Models and solves the maximum cardinality matching problem on a general graph using binary edge assignment variables, degree constraints, and edge set restrictions, with two distinct solver backends (CP-SAT and MILP).
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the maximum cardinality matching as a constraint satisfaction problem using binary variables for each allowed edge, node-degree constraints, and a maximization objective. This approach is suitable for graphs up to moderate size (thousands of edges) and guarantees exact optimality.

### Step 1 - Define Edge Variables
- For each edge `(u, v)` in the allowed edge set `E`, create a binary variable `x[(u,v)]` using `model.NewBoolVar()`.
- Use a dictionary keyed by the edge tuple to store variables for easy access during constraint building.

### Step 2 - Enforce Node Degree Constraints
- For each node in the graph, collect all variables corresponding to edges incident to that node.
- Add a constraint `sum(incident_vars) <= 1` for each node using `model.Add()`.

### Step 3 - Set Objective
- Maximize the total number of selected edges by calling `model.Maximize(sum(x.values()))`.

### Formulation Template
```json
{
  "sets": ["E: allowed edges (list of tuples)"],
  "parameters": ["N: set of nodes derived from edges"],
  "decision_variables": [
    "x_e ∈ {0,1} for each e ∈ E"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{e ∈ E} x_e"
  },
  "constraints": [
    "For each v ∈ N: sum_{e incident to v} x_e ≤ 1"
  ]
}
```

### Common Pitfalls
- Do not create variables for edges not in the allowed set; this would violate the edge set restriction.
- Do not forget to collect all incident edges for each node, including both endpoints of each edge.

## Solving stage

### Strategy Overview
Use OR-Tools' CP-SAT solver with appropriate parameters for performance. Parse the solver status and extract selected edges only on successful termination.

### Step 1 - Configure Solver
- Instantiate `cp_model.CpSolver()`.
- Set parameters: `max_time_in_seconds` (e.g., `[TIME_LIMIT]`), `num_search_workers` (e.g., 8), `random_seed` (e.g., 42), and `relative_gap_limit` (e.g., 0.0 for exact optimality).

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. If not, report failure with the solver status code.

### Step 3 - Extract and Verify Solution
- For each variable, use `solver.Value(x_e)` to check if it is 1.
- Build a list of selected edges.
- Verify that no node appears in more than one selected edge to confirm the matching property.

### Step 4 - Verify Optimality (Optional)
- To confirm optimality, add a constraint `sum(x.values()) >= k+1` where `k` is the objective value found, and check for infeasibility. This proves no larger matching exists.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# edges: list of tuples, e.g., [(0,1), (0,4), ...]
edges = [...]

model = cp_model.CpModel()
x = {}
for (u, v) in edges:
    x[(u, v)] = model.NewBoolVar(f'x_{u}_{v}')

# Node degree constraints
nodes = set()
for u, v in edges:
    nodes.add(u)
    nodes.add(v)
for v in nodes:
    incident = [x[e] for e in edges if v in e]
    if incident:
        model.Add(sum(incident) <= 1)

# Objective
model.Maximize(sum(x.values()))

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    selected = [e for e in edges if solver.Value(x[e]) > 0.5]
    payload = {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "objective": int(solver.ObjectiveValue()),
        "selected_edges": selected,
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
else:
    payload = {
        "status": "failed",
        "reason": "solver_error",
        "solver_status": str(status),
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Do not trust non-zero return codes or infeasible/unknown statuses; always check the status enum.
- Do not output pseudo-numeric answers when execution fails; always use the structured JSON output.

# Workflow 2 (MILP with Pyomo and CBC)

## Modeling stage

### Strategy Overview
Formulate the maximum cardinality matching as a mixed-integer linear program using Pyomo's `ConcreteModel`. This approach is suitable for larger graphs and provides access to advanced MILP solver features like warm starts and cut generation.

### Step 1 - Define Sets and Variables
- Create a Pyomo `Set` `m.E` indexed by edge indices (0 to len(edges)-1).
- Define binary variables `m.x[e]` for each edge index using `domain=pyo.Binary`.

### Step 2 - Build Node Degree Constraints
- Extract all unique nodes from the edge list.
- For each node, find incident edge indices and add a constraint `sum(m.x[e] for e in incident) <= 1` using `m.degree_con.add()`.

### Step 3 - Set Objective
- Maximize the sum of all edge variables: `m.obj = pyo.Objective(expr=sum(m.x[e] for e in m.E), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["E: set of edge indices"],
  "parameters": ["edges: list of tuples mapping index to (u,v)"],
  "decision_variables": [
    "x_e ∈ {0,1} for each e ∈ E"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{e ∈ E} x_e"
  },
  "constraints": [
    "For each v ∈ N: sum_{e incident to v} x_e ≤ 1"
  ]
}
```

### Common Pitfalls
- Do not use Pyomo's `Set` with tuples directly for indexing; use integer indices and maintain a separate mapping list.
- Do not forget to handle nodes with no incident edges (isolated nodes) gracefully.

## Solving stage

### Strategy Overview
Use the CBC solver via Pyomo's `SolverFactory`. Configure solver options for time limits and optimality gap. Parse results with explicit status and termination condition checks.

### Step 1 - Configure Solver
- Instantiate `pyo.SolverFactory("cbc")`.
- Set options: `seconds` for time limit (e.g., `[TIME_LIMIT]`) and `ratio` for MIP gap (e.g., 0.0 for optimality).

### Step 2 - Solve and Check Status
- Call `solver.solve(m, tee=False)`.
- Check `results.solver.status` equals `SolverStatus.ok` and `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Extract and Output Solution
- Iterate over edge indices, check `pyo.value(m.x[e]) > 0.5` to identify selected edges.
- Build a JSON payload with status, objective (cast to int), and selected edges list.
- On failure, output a JSON payload with failure reason and solver details.

### Code Usage
```python
import json
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# edges: list of tuples, e.g., [(0,1), (0,4), ...]
edges = [...]

m = pyo.ConcreteModel()
m.E = pyo.Set(initialize=range(len(edges)))
m.x = pyo.Var(m.E, domain=pyo.Binary)

m.obj = pyo.Objective(expr=sum(m.x[e] for e in m.E), sense=pyo.maximize)

nodes = list(set([v for e in edges for v in e]))
m.degree_con = pyo.ConstraintList()
for v in nodes:
    incident = [e for e, (u, w) in enumerate(edges) if u == v or w == v]
    if incident:
        m.degree_con.add(expr=sum(m.x[e] for e in incident) <= 1)

solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = [TIME_LIMIT]
solver.options["ratio"] = 0.0
results = solver.solve(m, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    selected = []
    for e in m.E:
        if pyo.value(m.x[e]) > 0.5:
            selected.append(edges[e])
    payload = {
        "status": "optimal" if term == TerminationCondition.optimal else "feasible",
        "objective": int(pyo.value(m.obj)),
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
- Do not skip validation of the matching solution; always verify that no node appears in more than one selected edge.
- Do not attempt to formulate a general graph matching as a max-flow problem without node-splitting constraints that enforce each original node appears at most once. This only works for bipartite graphs.
