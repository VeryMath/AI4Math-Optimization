---
name: Multi-Commodity Flow Min-Max Utilization
description: |
  Models and solves a multi-commodity flow problem where the objective is to minimize the maximum arc utilization across the network, using either direct LP solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct LP Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., Google OR-Tools) to build the optimization model programmatically. The min-max objective is linearized by introducing an auxiliary variable `z` representing the maximum utilization ratio across all arcs, then constraining each arc's total flow to be at most its capacity times `z`.

### Step 1 - Define Sets and Parameters
- Define the set of directed arcs `(i,j)` with associated capacity `capacity[i,j]`.
- Define the set of commodities `k`, each with a source node `source[k]`, sink node `sink[k]`, and demand `demand[k]`.
- Represent undirected edges as two directed arcs with identical capacity.

### Step 2 - Create Decision Variables
- For each directed arc `(i,j)` and each commodity `k`, create a continuous non-negative variable `flow_on_arc[i,j,k]`.
- Create a single continuous non-negative auxiliary variable `z` representing the maximum utilization ratio.

### Step 3 - Formulate Flow Conservation Constraints
- For each commodity `k` and each node `n`:
  - Compute outflow: sum of `flow_on_arc[i,j,k]` for arcs where `i == n`.
  - Compute inflow: sum of `flow_on_arc[i,j,k]` for arcs where `j == n`.
  - Enforce `outflow - inflow == demand[k]` if `n == source[k]`.
  - Enforce `outflow - inflow == -demand[k]` if `n == sink[k]`.
  - Enforce `outflow - inflow == 0` for all other nodes.

### Step 4 - Formulate Capacity Constraints with Utilization
- For each directed arc `(i,j)`, constrain the total flow across all commodities to be at most `capacity[i,j] * z`.
- Use `solver.Add(sum_k flow_on_arc[i,j,k] <= capacity[i,j] * z)`.

### Step 5 - Set Objective
- Set the objective to minimize `z` using `solver.Objective().SetCoefficient(z, 1)` and `solver.Objective().SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["ARCS: directed arcs (i,j)", "COMMODITIES: commodities k"],
  "parameters": ["capacity[i,j]: capacity of arc (i,j)", "source[k]: source node for commodity k", "sink[k]: sink node for commodity k", "demand[k]: demand for commodity k"],
  "decision_variables": ["flow_on_arc[i,j,k] >= 0: flow of commodity k on arc (i,j)", "z >= 0: maximum utilization ratio"],
  "objective": {
    "sense": "min",
    "expression": "z"
  },
  "constraints": [
    "flow_conservation: for each k, n: outflow - inflow == demand[k] if n==source[k], -demand[k] if n==sink[k], 0 otherwise",
    "capacity_utilization: for each (i,j): sum_k flow_on_arc[i,j,k] <= capacity[i,j] * z"
  ]
}
```

### Common Pitfalls
- Forgetting to represent undirected edges as two directed arcs, leading to missing flow directions.
- Using integer variables for flow when continuous variables are sufficient, unnecessarily increasing solve time.
- Misplacing the sign of demand in flow conservation (positive at source, negative at sink).

## Solving stage

### Strategy Overview
The model is solved using a linear programming solver (e.g., GLOP from OR-Tools) since all variables are continuous. The solver status is checked before extracting results, and arc utilization is computed post-solve for verification.

### Step 1 - Select and Configure Solver
- Use `pywraplp.Solver.CreateSolver("GLOP")` for pure linear programming problems.
- Optionally set a time limit using `solver.SetTimeLimit([TIME_LIMIT_MS])` (milliseconds).

### Step 2 - Solve the Model
- Call `status = solver.Solve()` to execute the optimization.
- Check the status: `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE` before accessing results.

### Step 3 - Extract and Validate Results
- Retrieve the optimal objective value using `z.solution_value()` and print with a clear prefix: `print(f"RESULT:{z.solution_value()}")`.
- For each arc, compute utilization as `sum_k flow_on_arc[i,j,k].solution_value() / capacity[i,j]` and verify it does not exceed the optimal `z` value.
- Identify bottleneck arcs where utilization equals the optimal `z` value (within a small tolerance).
- Validate flow conservation at source and sink nodes to ensure demands are met.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Data definition (use placeholders)
arcs = [(0,1), (1,2), (0,2)]  # list of (i,j)
capacity = {(0,1): [CAPACITY], (1,2): [CAPACITY], (0,2): [CAPACITY]}
commodities = [0, 1]
source = {0: 0, 1: 1}
sink = {0: 2, 1: 2}
demand = {0: [DEMAND], 1: [DEMAND]}
nodes = set([i for i,j in arcs] + [j for i,j in arcs])

# Create solver
solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    raise Exception("Solver not created")

# Decision variables
flow_on_arc = {}
for (i,j) in arcs:
    for k in commodities:
        flow_on_arc[(i,j,k)] = solver.NumVar(0, solver.infinity(), f'flow_{i}_{j}_{k}')
z = solver.NumVar(0, solver.infinity(), 'z')

# Flow conservation constraints
for k in commodities:
    for n in nodes:
        outflow = sum(flow_on_arc[(i,j,k)] for (i,j) in arcs if i == n)
        inflow = sum(flow_on_arc[(i,j,k)] for (i,j) in arcs if j == n)
        if n == source[k]:
            solver.Add(outflow - inflow == demand[k])
        elif n == sink[k]:
            solver.Add(outflow - inflow == -demand[k])
        else:
            solver.Add(outflow - inflow == 0)

# Capacity constraints with utilization
for (i,j) in arcs:
    solver.Add(sum(flow_on_arc[(i,j,k)] for k in commodities) <= capacity[(i,j)] * z)

# Objective
solver.Minimize(z)

# Solve
status = solver.Solve()
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    print(f"RESULT:{z.solution_value()}")
    # Optional: print arc utilizations and identify bottlenecks
    for (i,j) in arcs:
        total_flow = sum(flow_on_arc[(i,j,k)].solution_value() for k in commodities)
        util = total_flow / capacity[(i,j)]
        print(f"Arc ({i},{j}): utilization = {util:.3f}")
else:
    print("No feasible solution found")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, leading to runtime errors.
- Using an MIP solver (e.g., CBC) when the problem is purely linear, causing unnecessary overhead.
- Forgetting to set a time limit for large instances, causing indefinite solve times.

# Workflow 2 (Algebraic Modeling Framework)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling framework (e.g., Pyomo) to declare the optimization model declaratively. The min-max objective is linearized identically to Workflow 1, but the model is built using symbolic set indexing and constraint expressions, which improves readability and maintainability for larger problems.

### Step 1 - Define Sets and Parameters
- Create Pyomo `Set` objects for directed arcs, commodities, and nodes.
- Create Pyomo `Param` objects for arc capacities, commodity source/sink nodes, and demand values.
- Represent undirected edges as two directed arcs in the arcs set.

### Step 2 - Create Decision Variables
- Define a continuous non-negative variable `flow_on_arc` indexed by arcs and commodities using `pyomo.Var(arcs, commodities, domain=pyomo.NonNegativeReals)`.
- Define a continuous non-negative auxiliary variable `z` using `pyomo.Var(domain=pyomo.NonNegativeReals)`.

### Step 3 - Formulate Flow Conservation Constraints
- For each commodity `k` and each node `n`, create a constraint using `pyomo.Constraint` that enforces: outflow minus inflow equals demand at the source, negative demand at the sink, and zero otherwise.
- Use conditional logic within the constraint rule to determine the right-hand side based on node type.

### Step 4 - Formulate Capacity Constraints with Utilization
- For each directed arc `(i,j)`, create a constraint: sum of flows of all commodities on that arc is less than or equal to `capacity[i,j] * z`.
- Use `pyomo.Constraint(arcs, rule=lambda model, i, j: sum(model.flow_on_arc[i,j,k] for k in model.commodities) <= model.capacity[i,j] * model.z)`.

### Step 5 - Set Objective
- Set the objective to minimize `z` using `pyomo.Objective(expr=model.z, sense=pyomo.minimize)`.

### Formulation Template
```json
{
  "sets": ["ARCS: directed arcs (i,j)", "COMMODITIES: commodities k", "NODES: all network nodes"],
  "parameters": ["capacity[i,j]: capacity of arc (i,j)", "source[k]: source node for commodity k", "sink[k]: sink node for commodity k", "demand[k]: demand for commodity k"],
  "decision_variables": ["flow_on_arc[i,j,k] >= 0: flow of commodity k on arc (i,j)", "z >= 0: maximum utilization ratio"],
  "objective": {
    "sense": "min",
    "expression": "z"
  },
  "constraints": [
    "flow_conservation: for each k, n: outflow - inflow == demand[k] if n==source[k], -demand[k] if n==sink[k], 0 otherwise",
    "capacity_utilization: for each (i,j): sum_k flow_on_arc[i,j,k] <= capacity[i,j] * z"
  ]
}
```

### Common Pitfalls
- Using mutable parameters inside constraint rules without proper Pyomo `value()` calls, causing expression errors.
- Forgetting to declare all sets before using them in variable or constraint indexing.
- Using Python loops inside constraint rules that inadvertently create multiple constraints instead of a single indexed constraint.

## Solving stage

### Strategy Overview
The model is solved using an LP solver (e.g., HiGHS or GLPK) via Pyomo's solver interface. Solver status and termination condition are checked before extracting results, and a time limit is set to prevent indefinite solves.

### Step 1 - Select and Configure Solver
- Use `pyomo.SolverFactory("highs")` or `pyomo.SolverFactory("glpk")` for LP problems.
- Set solver options such as time limit: `solver.options["time_limit"] = [TIME_LIMIT_SEC]` (seconds for HiGHS) or `solver.options["tmlim"] = [TIME_LIMIT_SEC]` (for GLPK).

### Step 2 - Solve the Model
- Call `result = solver.solve(model, tee=False)` to execute the optimization.
- Check the solver status: `result.solver.status == pyomo.SolverStatus.ok` and `result.solver.termination_condition == pyomo.TerminationCondition.optimal` (or `feasible`).

### Step 3 - Extract and Validate Results
- Retrieve the optimal objective value using `pyomo.value(model.z)` and print with a clear prefix: `print(f"RESULT:{pyomo.value(model.z)}")`.
- For each arc, compute utilization as `sum_k pyomo.value(model.flow_on_arc[i,j,k]) / pyomo.value(model.capacity[i,j])` and verify it does not exceed the optimal `z` value.
- Identify bottleneck arcs where utilization equals the optimal `z` value (within a small tolerance).
- If the solver fails, output a structured error message with solver status and termination condition.

### Code Usage
```python
import pyomo.environ as pyomo

# Data definition (use placeholders)
arcs_list = [(0,1), (1,2), (0,2)]
capacity_data = {(0,1): [CAPACITY], (1,2): [CAPACITY], (0,2): [CAPACITY]}
commodities_list = [0, 1]
source_data = {0: 0, 1: 1}
sink_data = {0: 2, 1: 2}
demand_data = {0: [DEMAND], 1: [DEMAND]}
nodes_list = list(set([i for i,j in arcs_list] + [j for i,j in arcs_list]))

# Create model
model = pyomo.ConcreteModel()

# Sets
model.ARCS = pyomo.Set(initialize=arcs_list, dimen=2)
model.COMMODITIES = pyomo.Set(initialize=commodities_list)
model.NODES = pyomo.Set(initialize=nodes_list)

# Parameters
model.capacity = pyomo.Param(model.ARCS, initialize=capacity_data)
model.source = pyomo.Param(model.COMMODITIES, initialize=source_data)
model.sink = pyomo.Param(model.COMMODITIES, initialize=sink_data)
model.demand = pyomo.Param(model.COMMODITIES, initialize=demand_data)

# Decision variables
model.flow_on_arc = pyomo.Var(model.ARCS, model.COMMODITIES, domain=pyomo.NonNegativeReals)
model.z = pyomo.Var(domain=pyomo.NonNegativeReals)

# Flow conservation constraints
def flow_conservation_rule(model, k, n):
    outflow = sum(model.flow_on_arc[i,j,k] for (i,j) in model.ARCS if i == n)
    inflow = sum(model.flow_on_arc[i,j,k] for (i,j) in model.ARCS if j == n)
    if n == model.source[k]:
        return outflow - inflow == model.demand[k]
    elif n == model.sink[k]:
        return outflow - inflow == -model.demand[k]
    else:
        return outflow - inflow == 0
model.flow_conservation = pyomo.Constraint(model.COMMODITIES, model.NODES, rule=flow_conservation_rule)

# Capacity constraints with utilization
def capacity_utilization_rule(model, i, j):
    return sum(model.flow_on_arc[i,j,k] for k in model.COMMODITIES) <= model.capacity[i,j] * model.z
model.capacity_utilization = pyomo.Constraint(model.ARCS, rule=capacity_utilization_rule)

# Objective
model.obj = pyomo.Objective(expr=model.z, sense=pyomo.minimize)

# Solve
solver = pyomo.SolverFactory("highs")
solver.options["time_limit"] = [TIME_LIMIT_SEC]
result = solver.solve(model, tee=False)

# Check status
if (result.solver.status == pyomo.SolverStatus.ok and 
    result.solver.termination_condition in [pyomo.TerminationCondition.optimal, pyomo.TerminationCondition.feasible]):
    print(f"RESULT:{pyomo.value(model.z)}")
    # Optional: print arc utilizations and identify bottlenecks
    for (i,j) in model.ARCS:
        total_flow = sum(pyomo.value(model.flow_on_arc[i,j,k]) for k in model.COMMODITIES)
        util = total_flow / pyomo.value(model.capacity[i,j])
        print(f"Arc ({i},{j}): utilization = {util:.3f}")
else:
    print(f"Solver failed: status={result.solver.status}, termination={result.solver.termination_condition}")
```

### Common Pitfalls
- Not converting Pyomo parameter values to floats when computing utilization (use `pyomo.value()`).
- Using `tee=True` in production code, which floods output with solver logs.
- Forgetting to handle the case where the solver returns feasible but not optimal (e.g., due to time limit), which may still provide a usable solution.
