---
name: Multi-Item Allocation with Capacity Constraints
description: |
  Model and solve integer linear programs for allocating items under individual demand limits and multiple linear capacity constraints to maximize linear revenue.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
Use a procedural, solver-centric API (e.g., OR-Tools) to directly construct the model. This approach provides fine-grained control over variable bounds and constraint addition, which is efficient for problems with a straightforward structure.

### Step 1 - Define Sets and Parameters
- Declare the set of item types `ITEMS` and the set of capacity constraints `CONSTRAINTS`.
- Define parameters:
  - `revenue[i]`: revenue per unit of item `i`.
  - `demand_limit[i]`: maximum allowable units for item `i`.
  - `capacity_limit[c]`: total capacity for constraint `c`.
  - `coeff_matrix[c][i]`: binary coefficient (1 if item `i` consumes capacity `c`, 0 otherwise).

### Step 2 - Create Decision Variables
- Instantiate non-negative integer variables `x[i]` for each item `i`.
- Directly incorporate individual upper bounds by setting the variable's upper bound to its demand limit during creation: `solver.IntVar(0, demand_limit[i], f'x_{i}')`. This is more efficient than adding separate constraints.

### Step 3 - Formulate Capacity Constraints
- For each capacity constraint `c`, create a linear inequality: `sum(coeff_matrix[c][i] * x[i] for i in ITEMS) <= capacity_limit[c]`.
- Add the constraint to the solver: `solver.Add(sum_expr <= capacity_limit[c])`.

### Step 4 - Define the Objective
- Create a linear expression for total revenue: `sum(revenue[i] * x[i] for i in ITEMS)`.
- Set the objective to maximize this expression: `solver.Maximize(revenue_sum)`.

### Formulation Template
```json
{
  "sets": ["ITEMS", "CONSTRAINTS"],
  "parameters": [
    {"name": "revenue", "type": "float", "index": "ITEMS"},
    {"name": "demand_limit", "type": "int", "index": "ITEMS"},
    {"name": "capacity_limit", "type": "float", "index": "CONSTRAINTS"},
    {"name": "coeff_matrix", "type": "int", "index": ["CONSTRAINTS", "ITEMS"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "integer_nonnegative", "index": "ITEMS", "bounds": [0, "demand_limit[i]"]}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in ITEMS)"
  },
  "constraints": [
    {"name": "capacity", "expression": "sum(coeff_matrix[c][i] * x[i] for i in ITEMS) <= capacity_limit[c]", "index": "CONSTRAINTS"}
  ]
}
```

### Common Pitfalls
- Forgetting to set variable upper bounds, leading to unbounded or unrealistic solutions.
- Incorrectly populating the coefficient matrix, which can silently create wrong constraints.
- Using floating-point numbers for capacity limits when integer limits are more appropriate, potentially causing precision issues.

## Solving stage

### Strategy Overview
Solve the model using a dedicated MIP solver (e.g., SCIP, CBC) via the OR-Tools wrapper. Configure the solver for performance, robustly check the solution status, and extract and verify the results.

### Step 1 - Initialize and Configure Solver
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: `solver.SetTimeLimit([TIME_LIMIT])` (in milliseconds) and `solver.SetNumThreads([NUM_THREADS])`.
- Optionally set a relative optimality gap: `solver.SetRelativeGapTolerance(0.0)` for exact solutions.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Check the result status against `solver.OPTIMAL` and `solver.FEASIBLE`. Handle `solver.INFEASIBLE` or `solver.UNBOUNDED` appropriately.

### Step 3 - Extract and Verify Solution
- If the status is acceptable, retrieve the objective value: `obj_val = solver.Objective().Value()`.
- Extract variable values: `sol = {i: x[i].solution_value() for i in ITEMS}`.
- Programmatically verify that all capacity constraints and demand bounds are satisfied. Check integrality for integer variables.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver not available.")

# 2. Configure solver (optional)
solver.SetTimeLimit([TIME_LIMIT])
solver.SetNumThreads([NUM_THREADS])

# 3. Build model (following Modeling stage steps)
# ... (Define variables, constraints, objective)

# 4. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # 5. Extract solution
    objective_value = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in ITEMS}
    # 6. Optional verification and analysis
    for c in CONSTRAINTS:
        lhs = sum(coeff_matrix[c][i] * solution[i] for i in ITEMS)
        assert lhs <= capacity_limit[c] + 1e-6, f"Constraint {c} violated."
    # Report key insights: non-zero allocations, binding constraints, total units
    print(f"RESULT:{objective_value}")
else:
    print(f"No feasible solution found. Status: {status}")
```

### Common Pitfalls
- Not checking solver availability, which can cause runtime errors.
- Misinterpreting the solver status (e.g., treating `FEASIBLE` as `OPTIMAL` without noting potential sub-optimality).
- Extracting variable values without first confirming a feasible status, leading to errors.

# Workflow 2 (Algebraic Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
Use a declarative Algebraic Modeling Language (AML) like Pyomo. The model is defined abstractly using sets, parameters, variables, and rules, which promotes clarity, maintainability, and is ideal for problems with complex indexing or those that are part of larger systems.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for items (`model.I`) and constraints (`model.C`).
- Define `Param` objects for `revenue`, `demand_limit`, `capacity_limit`, and the constraint coefficient matrix `coeff`. Initialize them from data dictionaries.

### Step 2 - Define Decision Variables
- Declare a `Var` `model.x[i]` for each item with domain `pyo.NonNegativeIntegers`.
- Implement individual upper bounds as variable bounds `bounds=(0, demand_limit[i])` for efficiency and clarity.

### Step 3 - Construct Capacity Constraints via Rules
- Define a constraint rule indexed by the constraint set `model.C`.
- The rule should return the expression `sum(coeff[c, i] * model.x[i] for i in model.I) <= capacity_limit[c]`.

### Step 4 - Formulate the Objective
- Define an `Objective` with the expression `sum(revenue[i] * model.x[i] for i in model.I)` and sense `pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["I (items)", "C (constraints)"],
  "parameters": [
    {"name": "revenue", "type": "float", "index": "I"},
    {"name": "demand_limit", "type": "int", "index": "I"},
    {"name": "capacity_limit", "type": "float", "index": "C"},
    {"name": "coeff", "type": "int", "index": ["C", "I"]}
  ],
  "decision_variables": [
    {"name": "x", "type": "NonNegativeIntegers", "index": "I"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "Capacity", "expression": "sum(coeff[c,i] * x[i] for i in I) <= capacity_limit[c]", "index": "C"}
  ]
}
```

### Common Pitfalls
- Confusing 1-based and 0-based indexing when initializing parameters from data.
- Defining constraint rules incorrectly so they reference model attributes that don't exist yet.
- Using mutable default arguments (like lists) in Pyomo rule functions.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MILP solver (e.g., HiGHS, CBC). Emphasize proper solver configuration, robust handling of solution loading, and post-solution analysis to verify feasibility and understand constraint utilization.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("[SOLVER_NAME]")`.
- Configure options: set time limit (`time_limit`), optimality gap (`mip_rel_gap`), number of threads (`threads`), and enable presolve.

### Step 2 - Solve with Solution Loading Control
- Solve the model with `load_solutions=False` to first check termination status without loading potentially invalid results.
- Capture the results object: `results = solver.solve(model, load_solutions=False, tee=False)`.

### Step 3 - Check Termination Status
- Verify the solver status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:`.

### Step 4 - Load and Extract Solution
- If termination is acceptable, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Extract variable values, converting to appropriate types (e.g., `int` for quantities).

### Step 5 - Perform Post-Solution Analysis
- Compute the utilization of each capacity constraint and the usage of each demand limit.
- Identify binding constraints (where usage equals limit) for insight.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model (following Modeling stage steps)
model = pyo.ConcreteModel()
# ... (Define sets, params, variables, constraints, objective)

# 2. Instantiate and configure solver
solver = pyo.SolverFactory("[SOLVER_NAME]")
solver.options["time_limit"] = [TIME_LIMIT]
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = [NUM_THREADS]

# 3. Solve with controlled solution loading
results = solver.solve(model, load_solutions=False, tee=False)

# 4. Check solver status and termination condition
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    # 5. Load solution
    model.solutions.load_from(results)
    # 6. Extract results
    objective_value = pyo.value(model.obj)
    solution = {i: int(pyo.value(model.x[i])) for i in model.I}
    # 7. Optional analysis
    for c in model.C:
        usage = sum(pyo.value(model.coeff[c, i]) * solution[i] for i in model.I)
        print(f"Constraint {c} usage: {usage} / {pyo.value(model.capacity_limit[c])}")
    print(f"RESULT:{objective_value}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Loading solutions automatically without checking termination condition, which can raise exceptions for infeasible models.
- Forgetting to convert Pyomo variable values (which are floats) to integers for integer variables.
- Not setting the `domain` of variables correctly, leading to continuous instead of integer solutions.
