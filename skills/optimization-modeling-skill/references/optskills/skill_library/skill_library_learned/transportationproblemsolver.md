---
name: TransportationProblemSolver
description: |
  Model and solve balanced or capacitated transportation problems with linear costs using either direct LP solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct LP Solver API)

## Modeling stage

### Strategy Overview
Formulate the transportation problem directly within a solver's API (e.g., OR-Tools GLOP) by creating variables, constraints, and objective using procedural loops. This approach is efficient for standard problems and offers fine-grained control over variable bounds and constraint coefficients.

### Step 1 - Define Data Structures and Check Balance
- Organize problem data into lists or arrays for supply, demand, cost, and optional capacity.
- Use consistent indexing: `origins = range(num_origins)`, `destinations = range(num_destinations)`.
- **Prerequisite check**: Verify that total supply equals total demand for a balanced problem. If not, add a dummy origin or destination with zero cost to balance the problem before proceeding. For unbalanced problems, use inequality constraints (`<=` for supply, `>=` for demand) instead of equality constraints.

### Step 2 - Create Flow Variables with Bounds
- Instantiate non-negative continuous variables for each origin-destination pair.
- Use `solver.NumVar(lower_bound, upper_bound, name)`.
- For capacitated problems, set the upper bound directly to `capacity[i][j]`; otherwise, use `solver.infinity()`.

### Step 3 - Add Supply and Demand Constraints
- For each origin `i`, create an equality constraint: `sum(x[i][j] for all j) == supply[i]`.
- For each destination `j`, create an equality constraint: `sum(x[i][j] for all i) == demand[j]`.
- Use `solver.Constraint(value, value)` for equality or `solver.Constraint(lb, ub)` for inequalities.

### Step 4 - Set Linear Cost Objective
- Create an objective function: `minimize sum(cost[i][j] * x[i][j] for all i,j)`.
- Set coefficients via `objective.SetCoefficient(x[i][j], cost[i][j])` and call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply[origins]", "demand[destinations]", "cost[origins][destinations]", "capacity[origins][destinations] (optional)"],
  "decision_variables": ["flow[origins][destinations] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for all i,j)"
  },
  "constraints": [
    "sum(flow[i][j] for j in destinations) == supply[i] for each i",
    "sum(flow[i][j] for i in origins) == demand[j] for each j",
    "flow[i][j] <= capacity[i][j] for each i,j (optional)"
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver instance was created successfully (`solver` is not `None`).
- Using inequality constraints (`<=`, `>=`) when the problem is balanced and requires exact equality, leading to unexpected surplus or shortage.
- Not setting a time limit for large instances, risking excessive runtime.

## Solving stage

### Strategy Overview
Solve the constructed model using a dedicated LP solver (e.g., GLOP, CBC). Extract the solution, verify its correctness, and handle solver statuses robustly.

### Step 1 - Initialize Solver and Set Limits
- Create solver: `solver = pywraplp.Solver.CreateSolver("GLOP")`.
- Set a reasonable time limit: `solver.SetTimeLimit([TIME_LIMIT_MS])` (e.g., 30000 for 30 seconds).

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check if `status` is `OPTIMAL` or `FEASIBLE`. If not, handle the failure (e.g., output error JSON).

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `total_cost = objective.Value()`.
- Extract variable values: `flow_val = x[i][j].solution_value()`.
- **Post-solution verification**:
  1. For each origin `i`, compute `shipped = sum(x[i, j].solution_value() for j in destinations)` and verify `abs(shipped - supply[i]) < 1e-6`.
  2. For each destination `j`, compute `received = sum(x[i, j].solution_value() for i in origins)` and verify `abs(received - demand[j]) < 1e-6`.
  3. For capacitated problems, verify `x[i, j].solution_value() <= capacity[i][j] + 1e-6`.
  4. Recompute total cost from extracted flows to cross-check the solver's objective value.

### Step 4 - Output Results
- For successful solves, output the objective value in a parseable format (e.g., `RESULT:{total_cost}`).
- Optionally, output a structured JSON with non-zero flows (values > `1e-6`) and verification metrics.

### Code Usage
```python
# Example using OR-Tools GLOP
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    raise RuntimeError("Solver backend not available.")

# 2. Create variables
x = {}
for i in range(num_origins):
    for j in range(num_destinations):
        ub = capacity[i][j] if capacitated else solver.infinity()
        x[i, j] = solver.NumVar(0, ub, f"flow_{i}_{j}")

# 3. Add constraints
# Supply constraints
for i in range(num_origins):
    constraint = solver.Constraint(supply[i], supply[i])
    for j in range(num_destinations):
        constraint.SetCoefficient(x[i, j], 1)
# Demand constraints
for j in range(num_destinations):
    constraint = solver.Constraint(demand[j], demand[j])
    for i in range(num_origins):
        constraint.SetCoefficient(x[i, j], 1)

# 4. Set objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_destinations):
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# 5. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    # Verification
    for i in range(num_origins):
        shipped = sum(x[i, j].solution_value() for j in range(num_destinations))
        assert abs(shipped - supply[i]) < 1e-6
    for j in range(num_destinations):
        received = sum(x[i, j].solution_value() for i in range(num_origins))
        assert abs(received - demand[j]) < 1e-6
    print(f"RESULT:{total_cost}")
else:
    print(f'{{"status":"failed","solver_status":{status}}}')
```

### Common Pitfalls
- Not checking solver status before extracting values, leading to runtime errors on infeasible models.
- Ignoring numerical precision issues when comparing constraint satisfaction; always use a tolerance.
- Forgetting to set the objective sense to minimization.

# Workflow 2 (Algebraic Modeling with Pyomo)

## Modeling stage

### Strategy Overview
Use an algebraic modeling language (Pyomo) to declaratively define sets, parameters, variables, and constraints. This approach separates model logic from solver interaction, improving readability and maintainability for complex or large-scale problems.

### Step 1 - Define Abstract Sets and Parameters
- Create Pyomo `Set` objects for origins and destinations.
- Define `Param` objects for supply, demand, cost, and optional capacity, using dictionaries or rules for initialization.
- **Prerequisite check**: Verify that total supply equals total demand. If not, add a dummy origin or destination with zero cost to balance the problem before building constraints. For unbalanced problems, use inequality constraints (`<=` for supply, `>=` for demand) instead of equality constraints.

### Step 2 - Declare Decision Variables
- Create a non-negative continuous variable indexed over origin and destination sets: `model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)`.
- For capacitated problems, variable bounds can be set via a rule or a separate constraint.

### Step 3 - Construct Objective Function
- Define a linear objective to minimize total cost using a summation expression over the indexed sets.

### Step 4 - Implement Constraint Rules
- Create supply balance constraints: for each origin, sum of outgoing flows equals supply.
- Create demand balance constraints: for each destination, sum of incoming flows equals demand.
- For capacitated problems, add capacity constraints as inequalities.

### Formulation Template
```json
{
  "sets": ["I (origins)", "J (destinations)"],
  "parameters": ["supply[I]", "demand[J]", "cost[I,J]", "capacity[I,J] (optional)"],
  "decision_variables": ["x[I,J] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in I, j in J)"
  },
  "constraints": [
    "sum(x[i,j] for j in J) == supply[i] for each i in I",
    "sum(x[i,j] for i in I) == demand[j] for each j in J",
    "x[i,j] <= capacity[i,j] for each i in I, j in J (optional)"
  ]
}
```

### Common Pitfalls
- Incorrectly initializing parameters with mutable defaults; use `initialize` with a dictionary or function.
- Defining constraint rules that modify global state or have side effects.
- Not verifying that total supply equals total demand before solving, which can lead to infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external LP solver (e.g., HiGHS, CBC). Configure solver options, check termination status rigorously, and load the solution only after confirming success.

### Step 1 - Instantiate Solver and Set Options
- Create solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set options: `solver.options["time_limit"] = [TIME_LIMIT]`, `solver.options["threads"] = [NUM_THREADS]`.

### Step 2 - Solve with Status Control
- Call `results = solver.solve(model, tee=False, load_solutions=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `optimal` or `feasible`.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution: `model.solutions.load_from(results)`.
- Retrieve objective value: `total_cost = float(pyo.value(model.obj))`.
- Extract non-zero flows by iterating over variables with a tolerance (e.g., `val > 1e-6`).

### Step 4 - Validate Solution
- **Post-solution verification**:
  1. For each origin `i`, compute `shipped = sum(pyo.value(model.x[i, j]) for j in model.J)` and verify `abs(shipped - pyo.value(model.supply[i])) < 1e-6`.
  2. For each destination `j`, compute `received = sum(pyo.value(model.x[i, j]) for i in model.I)` and verify `abs(received - pyo.value(model.demand[j])) < 1e-6`.
  3. For capacitated problems, verify `pyo.value(model.x[i, j]) <= capacity_dict[i, j] + 1e-6`.
  4. Recompute total cost from extracted flows to cross-check the solver's objective value.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=range(num_origins))
model.J = pyo.Set(initialize=range(num_destinations))

model.supply = pyo.Param(model.I, initialize=supply_dict)
model.demand = pyo.Param(model.J, initialize=demand_dict)
model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)

model.x = pyo.Var(model.I, model.J, domain=pyo.NonNegativeReals)

def obj_rule(m):
    return sum(m.cost[i, j] * m.x[i, j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def supply_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == m.supply[i]
model.supply_con = pyo.Constraint(model.I, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.x[i, j] for i in m.I) == m.demand[j]
model.demand_con = pyo.Constraint(model.J, rule=demand_rule)

# Optional capacity constraints
if capacitated:
    def capacity_rule(m, i, j):
        return m.x[i, j] <= capacity_dict[i, j]
    model.cap_con = pyo.Constraint(model.I, model.J, rule=capacity_rule)

# 2. Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False, load_solutions=False)

# 3. Check status and extract
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    model.solutions.load_from(results)
    total_cost = float(pyo.value(model.obj))
    # Verification
    for i in model.I:
        shipped = sum(pyo.value(model.x[i, j]) for j in model.J)
        assert abs(shipped - pyo.value(model.supply[i])) < 1e-6
    for j in model.J:
        received = sum(pyo.value(model.x[i, j]) for i in model.I)
        assert abs(received - pyo.value(model.demand[j])) < 1e-6
    print(f"RESULT:{total_cost}")
else:
    print(f'{{"status":"failed","solver_status":"{status}","termination":"{term}"}}')
```

### Common Pitfalls
- Loading solutions without checking termination condition, which may raise `NoFeasibleSolutionError`.
- Using `tee=True` in production, which clutters output with solver logs.
- Not converting the objective value to a standard Python float, which can cause serialization issues.
