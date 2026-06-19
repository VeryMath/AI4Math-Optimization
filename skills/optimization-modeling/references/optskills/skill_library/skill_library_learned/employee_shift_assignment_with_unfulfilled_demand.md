---
name: Employee Shift Assignment with Unfulfilled Demand
description: |
  Models and solves a resource-to-demand assignment problem where unfulfilled demand is penalized, using either CP-SAT or MIP solvers with binary assignment variables and integer slack variables.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Model the assignment problem using boolean variables for each employee-location-shift combination and integer slack variables for unfulfilled demand. Enforce demand coverage with equality constraints, employee availability by fixing disallowed assignments to zero, and at-most-one-assignment per employee. Minimize a weighted sum of assignment costs and penalty costs for unmet demand.

### Step 1 - Define Assignment Variables
- Create a binary variable for each employee, location, and shift combination using `model.NewBoolVar()`.
- Name each variable with a descriptive string (e.g., `f"x_{e}_{r}_{s}"`) for debugging.

### Step 2 - Define Unfulfilled Demand Variables
- Create an integer variable for each location-shift pair using `model.NewIntVar(0, demand[r][s], name)`.
- Set the upper bound to the demand value for that pair to prevent unbounded solutions.

### Step 3 - Enforce Demand Coverage
- For each location-shift pair, add an equality constraint: sum of assignment variables for that pair plus the unfulfilled variable equals the required demand.
- Use `model.Add(sum(x[e, r, s] for e in employees) + u[r, s] == demand[r, s])`.

### Step 4 - Model Employee Availability
- For each unavailable employee, add a constraint fixing the sum of all their assignment variables to zero: `model.Add(sum(x[employee, ...]) == 0)`.
- For available employees, no constraint is needed.

### Step 5 - Limit Each Employee to One Assignment
- For each employee, add a constraint that the sum of all their assignment variables is less than or equal to 1: `model.Add(sum(x[e, ...]) <= 1)`.

### Step 6 - Construct Objective
- Minimize the sum of assignment costs (cost[e] * x[e, r, s]) plus penalty costs (penalty * u[r, s]).
- Use `model.Minimize()` with the weighted sum expression.

### Formulation Template
```json
{
  "sets": ["Employees", "Locations", "Shifts"],
  "parameters": ["demand[location, shift]", "cost[employee]", "penalty"],
  "decision_variables": [
    "x[employee, location, shift] ∈ {0, 1}",
    "u[location, shift] ∈ [0, demand[location, shift]]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[e] * x[e, r, s]) + sum(penalty * u[r, s])"
  },
  "constraints": [
    "sum(x[e, r, s] for e) + u[r, s] == demand[r, s]",
    "sum(x[e, r, s] for r, s) <= 1",
    "sum(x[unavailable_e, r, s] for r, s) == 0"
  ]
}
```

### Common Pitfalls
- Setting the penalty too low, causing the solver to leave demand unfulfilled even when employees are available.
- Forgetting to set an upper bound on unfulfilled demand variables, which can lead to unbounded solutions.
- Using `model.AddBoolOr()` or other logical constraints when simple linear constraints suffice.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with parallel search and a time limit. Check solver status for both optimal and feasible solutions before extracting results. Output objective value and variable assignments in a parseable format.

### Step 1 - Configure Solver
- Create a `CpSolver()` instance.
- Set `solver.parameters.max_time_in_seconds = [TIME_LIMIT]` for predictable runtime.
- Enable parallel search with `solver.parameters.num_search_workers = [NUM_WORKERS]`.
- Fix a random seed with `solver.parameters.random_seed = [SEED]` for reproducibility.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check if status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE` before reading results.
- If neither, output a failure message with the status code.

### Step 3 - Extract Results
- Read the objective value using `float(solver.ObjectiveValue())`.
- Iterate over all assignment variables and collect those with `solver.Value(var) == 1`.
- Iterate over unfulfilled demand variables and collect those with `solver.Value(var) > 0`.
- Print results in a parseable format (e.g., `RESULT:{obj}` or JSON).

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... build model ...

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42

status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    obj = float(solver.ObjectiveValue())
    assignments = [(e, r, s) for e, r, s in x if solver.Value(x[e, r, s]) == 1]
    unfulfilled = [(r, s) for r, s in u if solver.Value(u[r, s]) > 0]
    print(f"RESULT:{obj}")
else:
    print("FAILED")
```

### Common Pitfalls
- Not checking for `FEASIBLE` status, missing near-optimal solutions found within the time limit.
- Using `solver.Value()` on variables that were not solved (e.g., after infeasible status), causing runtime errors.
- Setting the time limit too short for large instances, resulting in no feasible solution found.

# Workflow 2 (MIP with Pyomo)

## Modeling stage

### Strategy Overview
Model the assignment problem using Pyomo with binary assignment variables and non-negative integer slack variables. Enforce demand coverage with equality constraints, employee availability by fixing disallowed assignments to zero, and at-most-one-assignment per employee. Minimize a weighted sum of assignment costs and penalty costs for unmet demand.

### Step 1 - Define Sets and Parameters
- Create Pyomo sets for employees, locations, and shifts using `pyo.Set(initialize=...)`.
- Define parameters for demand, cost, and penalty using `pyo.Param()`.

### Step 2 - Define Assignment Variables
- Create binary variables for each employee-location-shift combination using `pyo.Var(domain=pyo.Binary)`.
- Use a multi-index set (e.g., `model.employee_set * model.location_set * model.shift_set`) for the indexing domain.

### Step 3 - Define Unfulfilled Demand Variables
- Create non-negative integer variables for each location-shift pair using `pyo.Var(domain=pyo.NonNegativeIntegers)`.
- Optionally set an upper bound equal to the demand value.

### Step 4 - Enforce Demand Coverage
- For each location-shift pair, add a constraint: sum of assignment variables plus unfulfilled variable equals demand.
- Use `model.Add(expr=sum(x[e, r, s] for e in employees) + u[r, s] == demand[r, s])`.

### Step 5 - Model Employee Availability
- For each unavailable employee, add a constraint fixing the sum of all their assignment variables to zero.
- Use `pyo.Constraint.Skip` for available employees to avoid unnecessary constraints.

### Step 6 - Limit Each Employee to One Assignment
- For each employee, add a constraint that the sum of all their assignment variables is less than or equal to 1.

### Step 7 - Construct Objective
- Minimize the sum of assignment costs plus penalty costs for unfulfilled demand.
- Use `pyo.Objective(expr=..., sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["Employees", "Locations", "Shifts"],
  "parameters": ["demand[location, shift]", "cost[employee]", "penalty"],
  "decision_variables": [
    "x[employee, location, shift] ∈ {0, 1}",
    "u[location, shift] ∈ ℤ⁺"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[e] * x[e, r, s]) + sum(penalty * u[r, s])"
  },
  "constraints": [
    "sum(x[e, r, s] for e) + u[r, s] == demand[r, s]",
    "sum(x[e, r, s] for r, s) <= 1",
    "sum(x[unavailable_e, r, s] for r, s) == 0"
  ]
}
```

### Common Pitfalls
- Using `pyo.NonNegativeReals` instead of `pyo.NonNegativeIntegers` for unfulfilled demand, which can lead to fractional shortages.
- Forgetting to use `pyo.Constraint.Skip` for available employees, creating unnecessary constraints that slow down the solver.
- Setting the penalty too low, causing the solver to leave demand unfulfilled even when employees are available.

## Solving stage

### Strategy Overview
Use a standard MIP solver (CBC or GLPK) with a time limit and optimality gap. Check solver status and termination condition before extracting results. Handle floating-point rounding for binary variables with a threshold check.

### Step 1 - Configure Solver
- Create a solver instance with `pyo.SolverFactory("cbc")` or `pyo.SolverFactory("glpk")`.
- Set time limit: `solver.options["seconds"] = [TIME_LIMIT]` (CBC) or `solver.options["tmlim"] = [TIME_LIMIT]` (GLPK).
- Set optimality gap: `solver.options["ratio"] = [GAP]` (CBC) or `solver.options["mipgap"] = [GAP]` (GLPK).
- Enable parallelism: `solver.options["threads"] = [NUM_WORKERS]` (CBC).

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If not, output a failure JSON payload with status and termination condition strings.

### Step 3 - Extract Results
- Read the objective value using `pyo.value(model.objective)`.
- Iterate over assignment variables and collect those with `pyo.value(var) > 0.5` (threshold for binary variables).
- Iterate over unfulfilled demand variables and collect those with `pyo.value(var) > 0`.
- Package results in a JSON payload with keys: `status`, `objective`, `assignments`, and `unfulfilled`.
- Print the JSON with a `RESULT_JSON:` prefix for easy parsing.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

model = pyo.ConcreteModel()
# ... build model ...

solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = 30
solver.options["ratio"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                              TerminationCondition.feasible)):
    obj = pyo.value(model.objective)
    assignments = [(e, r, s) for e, r, s in model.x if pyo.value(model.x[e, r, s]) > 0.5]
    unfulfilled = [(r, s) for r, s in model.u if pyo.value(model.u[r, s]) > 0]
    payload = {"status": "success", "objective": obj,
               "assignments": assignments, "unfulfilled": unfulfilled}
    print(f"RESULT_JSON:{json.dumps(payload)}")
else:
    payload = {"status": "failed",
               "solver_status": str(results.solver.status),
               "termination": str(results.solver.termination_condition)}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Using `pyo.value()` on variables before checking solver status, causing runtime errors on failed solves.
- Using a threshold of `0.0` for binary variables, which can pick up floating-point noise near zero.
- Not setting a time limit, causing the solver to run indefinitely on large instances.
