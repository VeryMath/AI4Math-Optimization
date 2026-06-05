---
name: Minimum Cost Flow with Route Constraints
description: |
  Model and solve a minimum cost flow problem with flow balance, minimum flow, and capacity constraints on routes using either Pyomo or OR-Tools.
---

# Workflow 1 (Pyomo LP Formulation)

## Modeling stage

### Strategy Overview
Define a linear programming model using Pyomo's ConcreteModel with continuous decision variables for flow on each route. Enforce flow balance at nodes, minimum flow, and capacity constraints using indexed parameters and constraint rules.

### Step 1 - Define Sets and Parameters
- Create a set `ROUTES` indexed by route identifiers.
- Create a set `NODES` for all warehouse locations.
- For each route, define parameters: `origin`, `destination`, `cost_per_unit`, `min_flow`, `max_flow` stored in dictionaries keyed by route ID.

### Step 2 - Create Decision Variables
- Declare a continuous non-negative variable `flow[r]` for each route `r` in `ROUTES` using `pyo.Var(ROUTES, domain=pyo.NonNegativeReals)`.

### Step 3 - Define Objective
- Minimize total cost: `sum(flow[r] * cost_per_unit[r] for r in ROUTES)`.

### Step 4 - Add Constraints
- **Flow balance**: For each node `n` in `NODES`, enforce `sum(flow[r] for r in ROUTES if destination[r] == n) == sum(flow[r] for r in ROUTES if origin[r] == n)`.
- **Minimum flow**: For each route `r`, `flow[r] >= min_flow[r]`.
- **Capacity**: For each route `r`, `flow[r] <= max_flow[r]`.

### Formulation Template
```json
{
  "sets": ["ROUTES", "NODES"],
  "parameters": ["origin[ROUTES]", "destination[ROUTES]", "cost_per_unit[ROUTES]", "min_flow[ROUTES]", "max_flow[ROUTES]"],
  "decision_variables": ["flow[ROUTES] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(flow[r] * cost_per_unit[r] for r in ROUTES)"
  },
  "constraints": [
    "flow_balance[n]: sum(flow[r] for r in ROUTES if destination[r]==n) == sum(flow[r] for r in ROUTES if origin[r]==n) for n in NODES",
    "min_flow[r]: flow[r] >= min_flow[r] for r in ROUTES",
    "capacity[r]: flow[r] <= max_flow[r] for r in ROUTES"
  ]
}
```

### Common Pitfalls
- Using integer variables unnecessarily when continuous flows are acceptable, increasing solve time.
- Forgetting to include all nodes in the flow balance set, leading to infeasibility.
- Mixing up origin and destination in flow balance constraints.

## Solving stage

### Strategy Overview
Use Pyomo's SolverFactory with an LP-capable solver (e.g., GLPK, HiGHS). Set time limits and check solver status before extracting results. Output structured JSON for downstream parsing.

### Step 1 - Instantiate Solver
- Create solver with `pyo.SolverFactory("glpk")` or `pyo.SolverFactory("highs")`.

### Step 2 - Configure Solver Options
- Set time limit: `solver.options["tmlim"] = 30` (seconds).
- Set MIP gap if using MIP: `solver.options["mipgap"] = 0.0`.
- Set threads: `solver.options["threads"] = 4`.

### Step 3 - Solve and Check Status
- Call `result = solver.solve(model, tee=False)`.
- Check `result.solver.status == pyo.SolverStatus.ok` and `result.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.

### Step 4 - Extract Results
- Get objective: `float(pyo.value(model.obj))`.
- Get variable values: `{r: float(pyo.value(model.flow[r])) for r in model.ROUTES}`.

### Code Usage
```python
import pyomo.environ as pyo

# Build model
model = pyo.ConcreteModel()
model.ROUTES = pyo.Set(initialize=route_ids)
model.NODES = pyo.Set(initialize=node_ids)

# Parameters (example dictionaries)
origin = {...}; dest = {...}; cost = {...}; min_f = {...}; max_f = {...}

model.flow = pyo.Var(model.ROUTES, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return sum(m.flow[r] * cost[r] for r in m.ROUTES)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def flow_balance_rule(m, n):
    inflow = sum(m.flow[r] for r in m.ROUTES if dest[r] == n)
    outflow = sum(m.flow[r] for r in m.ROUTES if origin[r] == n)
    return inflow == outflow
model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

def min_flow_rule(m, r):
    return m.flow[r] >= min_f[r]
model.min_flow = pyo.Constraint(model.ROUTES, rule=min_flow_rule)

def cap_rule(m, r):
    return m.flow[r] <= max_f[r]
model.capacity = pyo.Constraint(model.ROUTES, rule=cap_rule)

# Solve
solver = pyo.SolverFactory("glpk")
solver.options["tmlim"] = 30
result = solver.solve(model, tee=False)

# Check and output
if result.solver.status == pyo.SolverStatus.ok and result.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    flows = {r: float(pyo.value(model.flow[r])) for r in model.ROUTES}
    print(f"RESULT_JSON:{{\"status\":\"success\",\"objective\":{obj_val},\"flows\":{flows}}}")
else:
    print(f"RESULT_JSON:{{\"status\":\"failed\",\"solver_status\":\"{result.solver.status}\",\"termination\":\"{result.solver.termination_condition}\"}}")
```

### Common Pitfalls
- Not checking termination condition, leading to reading results from infeasible models.
- Using `tee=True` in production, cluttering logs.
- Forgetting to convert Pyomo values to Python floats/ints for JSON serialization.

# Workflow 2 (OR-Tools Integer Flow)

## Modeling stage

### Strategy Overview
Use OR-Tools pywraplp with SCIP backend to model flows as integer variables. Encode minimum flow and capacity directly as variable bounds. Use additive constraints for flow balance and objective coefficients.

### Step 1 - Define Data Structures
- Create lists for route origins, destinations, costs, minimum flows, and maximum flows, indexed by route index.
- Create a set of unique node identifiers.

### Step 2 - Create Solver and Variables
- Instantiate solver: `pywraplp.Solver.CreateSolver("SCIP")`.
- For each route `i`, create an integer variable: `solver.IntVar(min_flow[i], max_flow[i], f"flow_{i}")`. This directly enforces both minimum flow and capacity constraints.

### Step 3 - Add Flow Balance Constraints
- For each node `n`, compute `outflow = sum(var[i] for i where origin[i]==n)` and `inflow = sum(var[i] for i where dest[i]==n)`.
- Add constraint: `solver.Add(outflow == inflow)`.

### Step 4 - Set Objective
- Create objective: `objective = solver.Objective()`.
- For each route `i`, set coefficient: `objective.SetCoefficient(var[i], cost[i])`.
- Set minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["routes indexed by i", "nodes"],
  "parameters": ["origin[i]", "destination[i]", "cost[i]", "min_flow[i]", "max_flow[i]"],
  "decision_variables": ["flow[i] integer in [min_flow[i], max_flow[i]]"],
  "objective": {
    "sense": "min",
    "expression": "sum(flow[i] * cost[i] for i in routes)"
  },
  "constraints": [
    "flow_balance[n]: sum(flow[i] for i where origin[i]==n) == sum(flow[i] for i where dest[i]==n) for n in nodes"
  ]
}
```

### Common Pitfalls
- Using `IntVar` when continuous flows are acceptable, unnecessarily restricting the solution space.
- Forgetting to include all nodes in flow balance, especially nodes that only appear as origin or destination.
- Not setting variable bounds correctly, leading to infeasibility.

## Solving stage

### Strategy Overview
Solve using OR-Tools SCIP solver with time limits and thread settings. Check solver status against OPTIMAL or FEASIBLE before extracting results. Output structured JSON.

### Step 1 - Configure Solver
- Set time limit: `solver.SetTimeLimit(30000)` (milliseconds).
- Set threads: `solver.SetNumThreads(4)`.

### Step 2 - Solve
- Call `status = solver.Solve()`.

### Step 3 - Check Status and Extract
- Check `if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):`.
- Get objective: `objective.Value()`.
- Get variable values: `var.solution_value()` for each route.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Data
origins = [...]  # list of origin nodes per route
dests = [...]    # list of destination nodes per route
costs = [...]    # list of costs per unit
min_flows = [...]  # list of minimum flows
max_flows = [...]  # list of maximum capacities
nodes = set(origins + dests)

# Create solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Variables with bounds
vars = []
for i in range(len(origins)):
    var = solver.IntVar(min_flows[i], max_flows[i], f"flow_{i}")
    vars.append(var)

# Flow balance constraints
for n in nodes:
    outflow = sum(vars[i] for i in range(len(origins)) if origins[i] == n)
    inflow = sum(vars[i] for i in range(len(origins)) if dests[i] == n)
    solver.Add(outflow == inflow)

# Objective
objective = solver.Objective()
for i in range(len(origins)):
    objective.SetCoefficient(vars[i], costs[i])
objective.SetMinimization()

# Solve
status = solver.Solve()

# Check and output
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    obj_val = objective.Value()
    flows = {f"route_{i}": int(var.solution_value()) for i, var in enumerate(vars)}
    print(f"RESULT_JSON:{{\"status\":\"success\",\"objective\":{obj_val},\"flows\":{flows}}}")
else:
    print(f"RESULT_JSON:{{\"status\":\"failed\",\"solver_status_code\":{status}}}")
```

### Common Pitfalls
- Not converting `solution_value()` to int for integer variables, causing JSON serialization issues.
- Using `solver.Solve()` without checking status, leading to crashes on infeasible models.
- Setting time limit too low for large instances, causing premature termination without feasible solution.
