---
name: MultiIndexFlowAssignmentLP
description: |
  Model and solve multi-index flow assignment problems with linear profit maximization and exact demand satisfaction using continuous variables, implemented via either direct solver APIs or algebraic modeling frameworks.
---

# Workflow 1 (Direct Solver API - OR-Tools GLOP)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (OR-Tools) to construct the linear program without an intermediate algebraic modeling language. It is efficient for straightforward LP formulations and provides fine-grained control over constraint building.

### Step 1 - Define Multi-Index Variables
- Create a non-negative continuous decision variable for each combination of source, destination, and product type.
- Use a descriptive naming convention (e.g., `x_src_dst_prod`) for debugging clarity.
- Store variables in a dictionary keyed by their indices for easy access during coefficient setting.

### Step 2 - Enforce Demand Satisfaction Constraints
- For each unique (destination, product) pair, create a single linear equality constraint.
- Set the constraint's lower and upper bounds to the exact demand value.
- Within the constraint, sum contributions from all source variables for that specific pair by setting their coefficients to 1.

### Step 3 - Formulate Linear Profit Objective
- Create a maximization objective.
- For each variable, add a term equal to the variable multiplied by its corresponding profit coefficient.
- Use nested loops over all index dimensions to systematically set all objective coefficients.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations",
    "products"
  ],
  "parameters": [
    "profit[source, destination, product]",
    "demand[destination, product]"
  ],
  "decision_variables": [
    "x[source, destination, product] >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,d,p] * x[s,d,p] for all s,d,p)"
  },
  "constraints": [
    "demand_satisfaction[d,p]: sum(x[s,d,p] for all s) == demand[d,p] for all d,p"
  ]
}
```

### Common Pitfalls
- Forgetting to set the coefficient for every variable within a constraint, leading to incorrect sums.
- Using loose tolerances when checking solution feasibility; always verify constraints with a small epsilon (e.g., 1e-6).
- Creating variables or constraints inside deeply nested loops inefficiently; prefer pre-initializing data structures.

## Solving stage

### Strategy Overview
Solve the constructed model using the GLOP linear programming solver. Focus on robust status checking, solution verification, and extracting a clean, sparse solution representation.

### Step 1 - Configure and Execute Solver
- Instantiate the GLOP solver.
- Invoke the solve method and capture the result status.

### Step 2 - Validate Solution Status
- Check for an `OPTIMAL` or `FEASIBLE` status. Treat both as successful solves for practical purposes.
- If the status is not acceptable, output a structured error message (e.g., JSON) with the solver status for debugging.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value.
- Iterate through all decision variables, collecting those with a value greater than a defined tolerance (e.g., 1e-6).
- Programmatically verify that the extracted solution satisfies all demand constraints by recalculating sums.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)

# solve with status / termination checks
status = solver.Solve()

if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    solution = {}
    tolerance = 1e-6
    # Extract non-zero flows
    for var_name, var in variables_dict.items():
        val = var.solution_value()
        if val > tolerance:
            solution[var_name] = val
    # Verification loop (pseudo-code)
    # for each (d,p): assert abs(sum(solution values) - demand[d,p]) < tolerance
else:
    # Output structured error
    error_info = {'status': status, 'message': 'Solver did not find a solution.'}
    print(f"RESULT_JSON:{error_info}")
```

### Common Pitfalls
- Assuming an `OPTIMAL` status guarantees exact constraint satisfaction; always perform numerical verification.
- Extracting all variable values for large problems, which can clutter output; filter by tolerance.
- Not handling the case where the solver might return `FEASIBLE` but not `OPTIMAL`.

# Workflow 2 (Algebraic Modeling - Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to declaratively define sets, parameters, variables, and constraints. It separates the problem formulation from the solver interface, improving readability and maintainability for complex models.

### Step 1 - Declare Model Sets and Parameters
- Define Pyomo `Set` objects for each index dimension (e.g., sources, destinations, products).
- Define `Param` objects for profit and demand data, initialized from nested dictionaries keyed by tuples.

### Step 2 - Define Decision Variables
- Create a `Var` object indexed over the Cartesian product of the defined sets.
- Specify the domain as `pyo.NonNegativeReals` for continuous, non-negative flows.

### Step 3 - Construct Objective and Constraints
- Define the objective as a `pyo.Objective` using a summation expression over all indices.
- Create demand satisfaction constraints using a `pyo.Constraint` rule that, for each (destination, product) pair, sums the appropriate variables and enforces equality with the demand parameter.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations",
    "products"
  ],
  "parameters": [
    "profit[source, destination, product]",
    "demand[destination, product]"
  ],
  "decision_variables": [
    "x[source, destination, product] in NonNegativeReals"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,d,p] * x[s,d,p] for all s,d,p)"
  },
  "constraints": [
    "demand_con[d,p]: sum(x[s,d,p] for all s) == demand[d,p] for all d,p"
  ]
}
```

### Common Pitfalls
- Incorrectly initializing multi-dimensional parameters; ensure the dictionary keys match the index order of the Pyomo `Param` declaration.
- Defining constraints inside loops instead of using Pyomo's indexed `Constraint` construct, which is less efficient and harder to debug.
- Confusing the order of indices in variable definitions, leading to mismatched coefficients in the objective and constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a high-performance LP solver like HiGHS or CBC. Implement a robust pattern for checking solver status, handling solution loading, and performing post-solution verification.

### Step 1 - Configure Solver and Solve
- Create a solver instance (e.g., `SolverFactory('highs')` or `'cbc'`).
- Set appropriate options such as time limit (`seconds`) and optimality gap tolerance (`ratio`).
- Execute the solve command, optionally with `tee=True` for debugging output.

### Step 2 - Check Termination Status
- Verify that `results.solver.status` is `SolverStatus.ok`.
- Check that `results.solver.termination_condition` is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If status checks fail, output a structured error before attempting to load the solution.

### Step 3 - Extract and Verify Solution
- Load the solution into the model instance.
- Retrieve the objective value via `pyo.value(model.obj)`.
- Iterate through the indexed variable object, collecting values above a tolerance into a sparse solution dictionary.
- Implement a verification loop to confirm demand constraints are satisfied numerically.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
# ... (set, parameter, variable, objective, constraint creation as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver_options = {'seconds': 30, 'ratio': 0.0}
results = solver.solve(model, options=solver_options, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal,
                                             TerminationCondition.feasible]):
    # Solution loading is typically automatic for common solvers
    objective_value = pyo.value(model.obj)
    solution = {}
    tolerance = 1e-6
    for index in model.x.index_set():
        val = pyo.value(model.x[index])
        if val > tolerance:
            solution[f'x[{index}]'] = val
    # Add verification logic here
else:
    error_info = {
        'solver_status': str(results.solver.status),
        'termination_condition': str(results.solver.termination_condition)
    }
    print(f"RESULT_JSON:{error_info}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition` before extracting results.
- Forgetting that some solvers require explicit solution loading (`load_solutions=False`/`model.solutions.load_from(results)`).
- Setting overly restrictive solver options (like `ratio=0.0`) on very large problems, potentially causing long solve times.
