---
name: Multi-Item Allocation with Capacity Constraints
description: |
  Model and solve integer linear programs for allocating items under individual demand limits and multiple linear capacity constraints to maximize linear revenue.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a procedural, solver-centric API (e.g., OR-Tools) to directly construct the model. Variables and constraints are added imperatively, which is efficient for problems with a straightforward structure and allows for fine-grained control over variable bounds.

### Step 1 - Define Sets and Parameters
- Declare the set of item types and the set of capacity constraints.
- Define parameters: revenue per item, individual demand limit per item, capacity limit per constraint, and a binary coefficient matrix indicating which items belong to which constraint.
- Use placeholders like `ITEMS`, `CONSTRAINTS`, `revenue`, `demand_limit`, `capacity_limit`, and `coeff_matrix`.

### Step 2 - Create Decision Variables
- Instantiate non-negative integer variables for each item type.
- Directly incorporate individual upper bounds by setting the variable's upper bound to its demand limit during creation, which is more efficient than adding separate constraints.
- Use `solver.IntVar(lower, upper, name)`.

### Step 3 - Formulate Capacity Constraints
- For each capacity constraint, create a linear inequality by summing the relevant variables.
- Use the binary coefficient matrix to determine which variables participate in each sum.
- Add the constraint to the solver: `solver.Add(sum(coeff[c][i] * x[i] for i in ITEMS) <= capacity_limit[c])`.

### Step 4 - Define the Objective
- Create a linear expression for total revenue: sum of `revenue[i] * x[i]` for all items.
- Set the objective to maximize this expression using `solver.Maximize()`.

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
Solve the model using a dedicated MIP solver (e.g., SCIP, CBC) via the OR-Tools wrapper. The focus is on configuring the solver for performance, robustly checking the solution status, and extracting and verifying the results.

### Step 1 - Initialize and Configure Solver
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Set practical limits: `solver.SetTimeLimit(30000)` (in milliseconds) and `solver.SetNumThreads(4)`.
- Optionally set a relative optimality gap: `solver.SetRelativeGapTolerance(0.0)` for exact solutions.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Check the result status against `solver.OPTIMAL` and `solver.FEASIBLE`. Handle `solver.INFEASIBLE` or `solver.UNBOUNDED` appropriately.

### Step 3 - Extract and Verify Solution
- If the status is acceptable, retrieve the objective value: `obj_val = solver.Objective().Value()`.
- Extract variable values: `sol = {i: x[i].solution_value() for i in ITEMS}`.
- Programmatically verify that all capacity constraints and demand bounds are satisfied.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver not available.")

# 2. Configure solver (optional)
solver.SetTimeLimit(30000)  # 30 seconds in milliseconds
solver.SetNumThreads(4)

# 3. Build model (following Modeling stage steps)
# ... (Define variables, constraints, objective)

# 4. Solve and check status
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # 5. Extract solution
    objective_value = solver.Objective().Value()
    solution = {i: x[i].solution_value() for i in ITEMS}
    # 6. Optional verification
    for c in CONSTRAINTS:
        lhs = sum(coeff_matrix[c][i] * solution[i] for i in ITEMS)
        assert lhs <= capacity_limit[c] + 1e-6, f"Constraint {c} violated."
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
This workflow uses a declarative Algebraic Modeling Language (AML) like Pyomo. The model is defined abstractly using sets, parameters, variables, and rules, which promotes clarity, maintainability, and is ideal for problems with complex indexing or those that are part of larger systems.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for items and constraints.
- Define `Param` objects for revenue, demand limits, capacity limits, and the constraint coefficient matrix. Initialize them from data dictionaries.

### Step 2 - Define Decision Variables
- Declare a `Var` for each item with domain `pyo.NonNegativeIntegers`.
- Implement individual upper bounds either as variable bounds `bounds=(0, demand_limit[i])` or as separate constraints for clarity.

### Step 3 - Construct Capacity Constraints via Rules
- Define a function (rule) for each capacity constraint or a single rule indexed by the constraint set.
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
    {"name": "DemandBound", "expression": "x[i] <= demand_limit[i]", "index": "I"},
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
Solve the Pyomo model using an external MILP solver (e.g., HiGHS, CBC). The workflow emphasizes proper solver configuration, robust handling of solution loading, and post-solution analysis to verify feasibility and understand constraint utilization.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = pyo.SolverFactory("highs")`.
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
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

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
