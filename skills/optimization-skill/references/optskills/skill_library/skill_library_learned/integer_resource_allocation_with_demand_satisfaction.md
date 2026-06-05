---
name: Integer Resource Allocation with Demand Satisfaction
description: |
  Model and solve integer linear programs for minimizing total resource usage while satisfying demand requirements and respecting individual usage limits.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling language for a declarative model definition, separating data from structure. It is well-suited for complex, sparse production matrices and integrates seamlessly with open-source solvers like HiGHS and CBC.

### Step 1 - Define Data Structures
- Organize problem parameters into distinct dictionaries for demand, usage limits, and production yields.
- Represent the production matrix as a nested dictionary `yield_matrix[pattern][order]` to efficiently handle sparsity.
- Use Python sets to define the indices for patterns and orders.

### Step 2 - Declare Variables and Objective
- Define non-negative integer decision variables `model.x[pattern]` using `pyo.Var(domain=pyo.NonNegativeIntegers)`.
- Set the objective to minimize the sum of all usage variables: `model.obj = pyo.Objective(expr=sum(model.x[p] for p in patterns), sense=pyo.minimize)`.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each order, create a constraint ensuring total production meets or exceeds demand.
- Use a generator expression with `.get(order, 0)` to safely sum contributions from all patterns: `sum(yield_matrix[p].get(o, 0) * model.x[p] for p in patterns) >= demand[o]`.

### Step 4 - Apply Individual Usage Limits
- Add upper bound constraints for each pattern: `model.x[p] <= usage_limit[p]`.
- Alternatively, set variable upper bounds directly during variable declaration for a more compact model.

### Formulation Template
```json
{
  "sets": ["patterns", "orders"],
  "parameters": {
    "demand": {"order": "quantity"},
    "usage_limit": {"pattern": "max_usage"},
    "yield_matrix": {"pattern": {"order": "yield_quantity"}}
  },
  "decision_variables": ["x[pattern] (non-negative integer)"],
  "objective": {
    "sense": "min",
    "expression": "sum(x[p] for p in patterns)"
  },
  "constraints": [
    "demand_satisfaction[o]: sum(yield_matrix[p][o] * x[p] for p in patterns) >= demand[o] for all o in orders",
    "usage_limit[p]: x[p] <= usage_limit[p] for all p in patterns"
  ]
}
```

### Common Pitfalls
- Forgetting to handle missing keys in sparse yield matrices, leading to KeyErrors. Always use `.get(key, default_value)`.
- Defining variable bounds as constraints instead of using the variable's native `bounds` argument, which increases model size unnecessarily.
- Using list comprehensions inside Pyomo expressions without `pyo.quicksum`, which can cause performance issues.

## Solving stage

### Strategy Overview
The solving stage focuses on configuring the solver, executing the solve, and rigorously verifying the solution's feasibility and optimality. It emphasizes robust status checking and post-solution validation.

### Step 1 - Configure and Execute Solver
- Instantiate the solver using `pyo.SolverFactory("highs")` or `pyo.SolverFactory("cbc")`.
- Configure key parameters: set a time limit (`time_limit`), optimality gap (`mip_rel_gap`), and number of threads.
- Execute the solve with `solver.solve(model, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Check `pyo.SolverStatus` and `pyo.TerminationCondition` from the results object.
- Accept solutions with status `ok` and termination condition `optimal` or `feasible`. Handle other conditions (e.g., `infeasible`, `maxTimeLimit`) with appropriate warnings.

### Step 3 - Extract and Verify Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Retrieve variable values with `pyo.value(model.x[p])` for non-zero usages.
- Implement a verification function that recalculates production per order from the solution and compares it against demand, reporting any violations.

### Step 4 - Report Results
- Format output clearly, separating the objective value, pattern usage, and verification results.
- For automation, print the objective value in a parseable format like `RESULT: <value>`.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (refer to Modeling Stage steps)
model = pyo.ConcreteModel()
# ... model construction code ...

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == pyo.SolverStatus.ok and termination in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    obj_val = pyo.value(model.obj)
    print(f"RESULT: {obj_val}")
    # Extract and print variable values...
else:
    print(f"Solver failed. Status: {status}, Termination: {termination}")
```

### Common Pitfalls
- Assuming a `feasible` solution is optimal without checking the optimality gap.
- Not verifying constraints post-solve, which can miss subtle numerical issues or solver errors.
- Forgetting to set `tee=False` in production, causing unwanted console output.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver (or MPSolver with SCIP/CBC) for a procedural, API-driven modeling approach. It is efficient for large-scale problems and offers fine-grained control over the solving process.

### Step 1 - Initialize Solver and Data
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")`.
- Load problem data into dictionaries, similar to Workflow 1, ensuring keys are hashable.

### Step 2 - Create Variables with Integrated Bounds
- Define integer variables using `solver.IntVar(lower_bound, upper_bound, name)`.
- Directly set the `upper_bound` argument to the pattern's usage limit, incorporating the limit into the variable definition instead of a separate constraint.

### Step 3 - Build Demand Constraints
- For each order, create a constraint object: `ct = solver.Constraint(demand[o], solver.infinity(), f"demand_{o}")`.
- Iterate over all patterns. For each pattern, if `yield_matrix[p][o] > 0`, set the coefficient: `ct.SetCoefficient(x[p], yield_matrix[p][o])`. This implements sparse coefficient setting.

### Step 4 - Define Linear Objective
- Create the objective expression: `objective = solver.Objective()`.
- Set all variable coefficients to 1.0: `objective.SetCoefficient(x[p], 1.0)`.
- Set the optimization sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["patterns", "orders"],
  "parameters": {
    "demand": {"order": "quantity"},
    "usage_limit": {"pattern": "max_usage"},
    "yield_matrix": {"pattern": {"order": "yield_quantity"}}
  },
  "decision_variables": ["x[pattern] (IntVar with lower=0, upper=limit)"],
  "objective": {
    "sense": "min",
    "expression": "sum(x[p] for p in patterns)"
  },
  "constraints": [
    "demand_satisfaction[o]: sum(yield_matrix[p][o] * x[p] for p in patterns) >= demand[o]"
  ]
}
```

### Common Pitfalls
- Creating constraints with `solver.infinity()` as the lower bound by mistake; the lower bound should be the demand.
- Not leveraging variable upper bounds for usage limits, which adds unnecessary constraints and slows down the solver.
- Using `solver.NumVar` instead of `solver.IntVar`, resulting in a continuous relaxation.

## Solving stage

### Strategy Overview
The solving stage focuses on configuring solver parameters for performance, executing the solve, and implementing a comprehensive verification routine to ensure the solution's integrity.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(30000)` (time in milliseconds).
- Configure parallelism: `solver.SetNumThreads(4)`.
- For CP-SAT, set additional parameters like `solver.parameters.max_time_in_seconds`.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve()`.
- Check for `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` status. Provide clear messages for other statuses like `INFEASIBLE` or `ABNORMAL`.

### Step 3 - Extract and Validate Solution
- If the status is acceptable, extract the objective value: `solver.Objective().Value()`.
- Extract variable values: `x[p].solution_value()`.
- Run a verification loop: for each order, sum `yield_matrix[p][o] * x[p].solution_value()` and assert it meets demand. Also verify variable values do not exceed their upper bounds.

### Step 4 - Format and Output Results
- Print a summary including the objective value and a table of non-zero variable values.
- Optionally, output results in JSON format for easy integration with other systems.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
# ... variable and constraint creation ...

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    print(f"RESULT: {obj_val}")
    # Verification loop
    for o in orders:
        total_prod = sum(yield_matrix[p].get(o, 0) * x[p].solution_value() for p in patterns)
        if total_prod < demand[o] - 1e-6: # tolerance for numerical issues
            print(f"WARNING: Demand for {o} not met.")
else:
    print(f"No feasible solution found. Solver status: {status}")
```

### Common Pitfalls
- Not using a tolerance when checking demand satisfaction post-solve, leading to false failures due to floating-point arithmetic.
- Ignoring the `FEASIBLE` status and only accepting `OPTIMAL`, potentially discarding good solutions when time limits are hit.
- Forgetting to check variable bounds during verification, missing potential model definition errors.
