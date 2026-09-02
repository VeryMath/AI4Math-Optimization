---
name: Facility Location Problem Solver
description: |
  Models and solves uncapacitated facility location problems using binary decision variables for facility opening and customer assignment, with fixed opening costs and variable assignment costs.
---

# Workflow 1 (Pyomo with CBC Solver)

## Modeling stage

### Strategy Overview
Formulate the uncapacitated facility location problem (UFLP) as a mixed-integer linear program using Pyomo's ConcreteModel. Define binary variables for facility opening and customer assignment, enforce each customer is served exactly once and only by open facilities, and minimize the sum of fixed opening costs and variable assignment costs.

### Step 1 - Define Sets and Parameters
- Create Pyomo Set objects for customers (`model.I`) and facilities (`model.J`) using `pyo.Set(initialize=...)`.
- Define parameter dictionaries for fixed opening costs per facility (`fixed_cost[j]`) and variable assignment costs per customer-facility pair (`assign_cost[i,j]`). Use precomputed data (e.g., a cost matrix) directly.

### Step 2 - Declare Decision Variables
- Create binary variable `y[j]` for each facility indicating whether it is opened: `pyo.Var(model.J, domain=pyo.Binary)`.
- Create binary variable `x[i,j]` for each customer-facility pair indicating assignment: `pyo.Var(model.I, model.J, domain=pyo.Binary)`.

### Step 3 - Build Objective and Constraints
- Define objective as `sum(fixed_cost[j] * y[j] for j in model.J) + sum(assign_cost[i,j] * x[i,j] for i in model.I for j in model.J)` with `sense=pyo.minimize`.
- Add **assignment_coverage** constraint: each customer assigned to exactly one facility: `sum(x[i,j] for j in model.J) == 1` for each customer `i`.
- Add **facility_activation** constraint: assignments only to open facilities: `x[i,j] <= y[j]` for all customer-facility pairs `(i,j)`.

### Formulation Template
```json
{
  "sets": ["I: customers", "J: facilities"],
  "parameters": ["f_j: fixed cost for facility j", "c_ij: assignment cost for customer i to facility j"],
  "decision_variables": ["y_j: binary, 1 if facility j opened", "x_ij: binary, 1 if customer i assigned to facility j"],
  "objective": {
    "sense": "min",
    "expression": "sum_j f_j * y_j + sum_i sum_j c_ij * x_ij"
  },
  "constraints": [
    "sum_j x_ij == 1 for all i",
    "x_ij <= y_j for all i, j"
  ]
}
```

### Common Pitfalls
- Forgetting to set `domain=pyo.Binary` on both variable types, leading to continuous relaxation instead of MILP.
- Using mutable parameter objects when static dictionaries suffice, adding unnecessary complexity.

## Solving stage

### Strategy Overview
Solve the MILP using CBC solver via Pyomo's SolverFactory. Configure solver options for time limit and optimality gap, then parse results with proper status checks and threshold-based binary variable extraction.

### Step 1 - Configure and Solve
- Instantiate solver: `solver = pyo.SolverFactory("cbc")`.
- Set solver options: `solver.options["seconds"] = [TIME_LIMIT]` and `solver.options["ratio"] = 0.0` for exact optimal solution.
- Call solve: `results = solver.solve(model, tee=False)`.

### Step 2 - Parse Results
- Check solver status: `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Extract objective value: `float(pyo.value(model.obj))`.
- Retrieve open facilities: `[j for j in model.J if pyo.value(model.y[j]) > 0.5]`.
- Retrieve assignments: `{(i, j) for i in model.I for j in model.J if pyo.value(model.x[i, j]) > 0.5}`.
- **Calculate cost breakdown**: Compute fixed cost component (`sum(fixed_cost[j] for j in open_facilities)`) and assignment cost component (`obj_val - fixed_cost_sum`) for solution verification.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=customer_list)
model.J = pyo.Set(initialize=facility_list)

model.y = pyo.Var(model.J, domain=pyo.Binary)
model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

def obj_rule(m):
    return sum(fixed_cost[j] * m.y[j] for j in m.J) + sum(assign_cost[i,j] * m.x[i,j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def assign_rule(m, i):
    return sum(m.x[i,j] for j in m.J) == 1
model.assign_con = pyo.Constraint(model.I, rule=assign_rule)

def open_rule(m, i, j):
    return m.x[i,j] <= m.y[j]
model.open_con = pyo.Constraint(model.I, model.J, rule=open_rule)

# Solve
solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = [TIME_LIMIT]
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

# Parse results
if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = float(pyo.value(model.obj))
    open_facilities = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    assignments = {(i, j) for i in model.I for j in model.J if pyo.value(model.x[i, j]) > 0.5}
    # Cost breakdown for verification
    fixed_cost_sum = sum(fixed_cost[j] for j in open_facilities)
    assign_cost_sum = obj_val - fixed_cost_sum
    result_json = {"status": "optimal", "objective": obj_val, "open_facilities": open_facilities, "assignments": assignments, "fixed_cost": fixed_cost_sum, "assignment_cost": assign_cost_sum}
else:
    result_json = {"status": "infeasible"}
```

### Common Pitfalls
- Not checking termination condition for feasible solutions when optimal is not guaranteed, missing valid results.
- Using threshold too low (e.g., 0.1) for binary variable extraction, potentially including numerical noise.

# Workflow 2 (OR-Tools with SCIP Solver)

## Modeling stage

### Strategy Overview
Formulate the uncapacitated facility location problem using Google OR-Tools' pywraplp solver interface. Define binary variables explicitly, add constraints using solver methods, and set objective coefficients directly for efficient MILP construction.

### Step 1 - Initialize Solver and Variables
- Create solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Create binary variables for facilities: `y = [solver.BoolVar(f"y_{j}") for j in range(num_facilities)]`.
- Create binary variables for assignments: `x = [[solver.BoolVar(f"x_{i}_{j}") for j in range(num_facilities)] for i in range(num_customers)]`.

### Step 2 - Add Constraints
- Add **assignment_coverage** constraints: `solver.Add(sum(x[i][j] for j in range(num_facilities)) == 1)` for each customer `i`.
- Add **facility_activation** constraints: `solver.Add(x[i][j] <= y[j])` for all customer-facility pairs `(i, j)`.

### Step 3 - Build Objective
- Create objective: `objective = solver.Objective()`.
- Set coefficients: for each facility `j`, `objective.SetCoefficient(y[j], fixed_cost[j])`; for each pair `(i,j)`, `objective.SetCoefficient(x[i][j], assign_cost[i][j])`.
- Set minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I: customers (0..n-1)", "J: facilities (0..m-1)"],
  "parameters": ["f_j: fixed cost for facility j", "c_ij: assignment cost for customer i to facility j"],
  "decision_variables": ["y_j: BoolVar, 1 if facility j opened", "x_ij: BoolVar, 1 if customer i assigned to facility j"],
  "objective": {
    "sense": "min",
    "expression": "sum_j f_j * y_j + sum_i sum_j c_ij * x_ij"
  },
  "constraints": [
    "sum_j x_ij == 1 for all i",
    "x_ij <= y_j for all i, j"
  ]
}
```

### Common Pitfalls
- Using `IntVar(0, 1)` instead of `BoolVar()` for binary variables, which may cause solver inefficiency.
- Forgetting to call `objective.SetMinimization()` after setting coefficients, defaulting to maximization.

## Solving stage

### Strategy Overview
Solve the MILP using OR-Tools' SCIP backend with configurable time limit and parallelism. Check solver status against predefined constants and extract solution values using threshold-based filtering.

### Step 1 - Configure and Solve
- Set time limit: `solver.SetTimeLimit([TIME_LIMIT_MS])` (time in milliseconds).
- Set thread count: `solver.SetNumThreads([NUM_THREADS])`.
- Call solve: `status = solver.Solve()`.

### Step 2 - Parse Results
- Check status: `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`.
- Extract objective value: `solver.Objective().Value()`.
- Retrieve open facilities: `[j for j in range(num_facilities) if y[j].solution_value() > 0.5]`.
- Retrieve assignments: `[(i, j) for i in range(num_customers) for j in range(num_facilities) if x[i][j].solution_value() > 0.5]`.
- **Calculate cost breakdown**: Compute fixed cost component (`sum(fixed_cost[j] for j in open_facilities)`) and assignment cost component (`obj_val - fixed_cost_sum`) for solution verification.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model
solver = pywraplp.Solver.CreateSolver("SCIP")
num_customers = len(customer_list)
num_facilities = len(facility_list)

y = [solver.BoolVar(f"y_{j}") for j in range(num_facilities)]
x = [[solver.BoolVar(f"x_{i}_{j}") for j in range(num_facilities)] for i in range(num_customers)]

# Constraints
for i in range(num_customers):
    solver.Add(sum(x[i][j] for j in range(num_facilities)) == 1)
for i in range(num_customers):
    for j in range(num_facilities):
        solver.Add(x[i][j] <= y[j])

# Objective
objective = solver.Objective()
for j in range(num_facilities):
    objective.SetCoefficient(y[j], fixed_cost[j])
for i in range(num_customers):
    for j in range(num_facilities):
        objective.SetCoefficient(x[i][j], assign_cost[i][j])
objective.SetMinimization()

# Solve
solver.SetTimeLimit([TIME_LIMIT_MS])
solver.SetNumThreads([NUM_THREADS])
status = solver.Solve()

# Parse results
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    obj_val = solver.Objective().Value()
    open_facilities = [j for j in range(num_facilities) if y[j].solution_value() > 0.5]
    assignments = [(i, j) for i in range(num_customers) for j in range(num_facilities) if x[i][j].solution_value() > 0.5]
    # Cost breakdown for verification
    fixed_cost_sum = sum(fixed_cost[j] for j in open_facilities)
    assign_cost_sum = obj_val - fixed_cost_sum
    result_json = {"status": "optimal", "objective": obj_val, "open_facilities": open_facilities, "assignments": assignments, "fixed_cost": fixed_cost_sum, "assignment_cost": assign_cost_sum}
else:
    result_json = {"status": "infeasible"}
```

### Common Pitfalls
- Not converting time limit to milliseconds (OR-Tools expects milliseconds, not seconds).
- Assuming `solution_value()` returns exactly 0 or 1 for binary variables; always use a threshold for robustness.
