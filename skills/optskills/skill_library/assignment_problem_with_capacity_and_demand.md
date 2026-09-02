---
name: Assignment Problem with Capacity and Demand
description: |
  Model and solve linear assignment problems with resource availability, task demand, and per-assignment capacity limits using continuous variables and linear programming solvers.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using a direct solver API (e.g., OR-Tools). Define continuous assignment variables with built-in bounds to represent capacity limits. Structure data as indexed lists or dictionaries for clarity and efficient model construction.

### Step 1 - Define Data Structures
- Organize problem parameters into clear, indexed data structures.
- Create lists for resource availability and task demand.
- Create a 2D structure (list-of-lists or dictionary) for assignment costs and capacity limits.

### Step 2 - Instantiate Model and Variables
- Create a solver instance for linear programming (e.g., `GLOP`).
- Define continuous decision variables `x[i][j]` for assignment quantity from resource `i` to task `j`.
- Set variable bounds directly: lower bound `0`, upper bound `capacity[i][j]`.

### Step 3 - Build Demand Satisfaction Constraints
- For each task `j`, create an equality constraint.
- Set the constraint's right-hand side to `demand[j]`.
- Add the coefficient `1` for each variable `x[i][j]` across all resources `i`.

### Step 4 - Build Resource Availability Constraints
- For each resource `i`, create a less-than-or-equal constraint.
- Set the constraint's upper bound to `availability[i]`.
- Add the coefficient `1` for each variable `x[i][j]` across all tasks `j`.

### Step 5 - Define the Objective Function
- Create a linear objective to minimize total cost.
- For each `(i, j)` pair, add the term `cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "tasks"
  ],
  "parameters": [
    "availability[resource]",
    "demand[task]",
    "cost[resource][task]",
    "capacity[resource][task]"
  ],
  "decision_variables": [
    "x[resource][task] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_over_resources_tasks(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "demand_satisfaction[task]: sum_over_resources(x[i][j]) == demand[j]",
    "resource_availability[resource]: sum_over_tasks(x[i][j]) <= availability[i]",
    "capacity_limit[resource][task]: x[i][j] <= capacity[i][j] (enforced via variable bounds)"
  ]
}
```

### Common Pitfalls
- Forgetting to handle resources with zero availability, which can lead to unnecessary variables; consider explicitly fixing their assignments to zero.
- Using inconsistent indexing between parameters and variables, causing `KeyError` or incorrect model construction.
- Not setting variable upper bounds, requiring separate capacity constraints and increasing model size.

## Solving stage

### Strategy Overview
Solve the constructed LP model using the chosen solver. Implement robust solution status checking and post-solve verification of all constraints. Extract and report the solution in a clear, actionable format.

### Step 1 - Solve and Check Status
- Call the solver's `Solve()` method.
- Check the result status (e.g., `OPTIMAL`, `FEASIBLE`).
- If not optimal or feasible, log an informative error and analyze infeasibility.

### Step 2 - Extract and Store Solution
- If the status is acceptable, iterate over all variables to extract their solution values.
- Store assignments in a data structure mirroring the variable indexing.

### Step 3 - Verify Solution Against Constraints
- Recompute totals per task and compare to demand within a small tolerance.
- Recompute totals per resource and compare to availability within a tolerance.
- Check each non-zero assignment against its capacity limit.
- Recompute the objective value from assignments and compare to the solver's reported value.

### Step 4 - Report Results
- Print a summary of the total cost and solver status.
- Print a detailed report of non-zero assignments.
- Print per-resource and per-task utilization summaries.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
x = {}
for i in resources:
    for j in tasks:
        x[i, j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')

# Demand constraints
for j in tasks:
    ct = solver.Constraint(demand[j], demand[j])
    for i in resources:
        ct.SetCoefficient(x[i, j], 1)

# Availability constraints
for i in resources:
    ct = solver.Constraint(0, availability[i])
    for j in tasks:
        ct.SetCoefficient(x[i, j], 1)

# Objective
objective = solver.Objective()
for i in resources:
    for j in tasks:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract solution...
else:
    print(f'Solver did not find optimal solution. Status: {status}')
```

### Common Pitfalls
- Extracting solution values without first checking the solver status, leading to errors.
- Using an absolute tolerance of zero for floating-point comparisons in verification, causing false failures.
- Not verifying the solution independently, potentially missing solver or model-building errors.

# Workflow 2 (Modeling Framework - Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem using a modeling framework (e.g., Pyomo) to separate the model declaration from the solver interface. Define abstract sets and parameters for flexibility, and use constraint rules for clean, maintainable model construction.

### Step 1 - Declare Abstract Sets and Parameters
- Define the abstract sets `resources` and `tasks`.
- Declare `Param` components for `availability`, `demand`, `cost`, and `capacity`, indexed appropriately.

### Step 2 - Define Continuous Variables
- Declare a `Var` component `x` indexed over `resources` and `tasks`.
- Set the variable domain to `NonNegativeReals`.
- Optionally, set variable upper bounds using the `capacity` parameter within a rule or initialization.

### Step 3 - Define Objective Rule
- Create a `Objective` component with `sense=minimize`.
- Define a rule that returns the sum of `cost[i,j] * x[i,j]` over all indices.

### Step 4 - Define Constraint Rules
- Create a `Constraint` component for demand satisfaction, indexed by `tasks`.
- The rule for each task `j` returns the sum of `x[i,j]` over `resources` equals `demand[j]`.
- Create a `Constraint` component for resource availability, indexed by `resources`.
- The rule for each resource `i` returns the sum of `x[i,j]` over `tasks` less than or equal to `availability[i]`.

### Step 5 - Handle Edge Cases Explicitly
- Add a preprocessing step or additional constraints to fix variables to zero for resources with zero availability, improving model clarity and presolve.

### Formulation Template
```json
{
  "sets": [
    "resources",
    "tasks"
  ],
  "parameters": [
    "availability[resource]",
    "demand[task]",
    "cost[resource][task]",
    "capacity[resource][task]"
  ],
  "decision_variables": [
    "x[resource][task] in NonNegativeReals"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for i in resources for j in tasks)"
  },
  "constraints": [
    "demand_satisfaction[task]: sum(x[i,j] for i in resources) == demand[j]",
    "resource_availability[resource]: sum(x[i,j] for j in tasks) <= availability[i]",
    "capacity_limit[resource][task]: x[i,j] <= capacity[i,j] (optional, can be variable bound)"
  ]
}
```

### Common Pitfalls
- Defining variable bounds within a constraint rule instead of the variable declaration, which can be less efficient for the solver.
- Using concrete data initialization with abstract sets, causing runtime errors.
- Not attaching parameter dictionaries to the model object, making them inaccessible during post-solve verification.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a compatible LP solver (e.g., HiGHS, CBC). Use a pattern that separates solving from solution loading to handle statuses robustly. Perform comprehensive numerical verification of the solution.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory`.
- Set essential options like `time_limit` and `threads`. Avoid over-specifying options.

### Step 2 - Solve with Careful Solution Loading
- Execute `solve(model, load_solutions=False)` to get results without immediate loading.
- Check the solver termination condition (e.g., `optimal`, `feasible`).
- If termination is acceptable, manually load the solution into the model.

### Step 3 - Verify All Constraints
- Iterate through all constraints, evaluating their expressions and comparing to bounds with a tolerance.
- Compute per-task and per-resource totals from the variable values to verify demand and availability.
- Check variable values against their upper bounds (capacity).

### Step 4 - Compute and Report Metrics
- Recalculate the objective value from the loaded variable values.
- Generate a structured report showing assignment details, constraint slack, and total cost.
- Summarize resource utilization and task fulfillment.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.resources = pyo.Set(initialize=resources)
model.tasks = pyo.Set(initialize=tasks)
# ... define parameters, variables, objective, and constraints ...

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
results = solver.solve(model, load_solutions=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    # Verification and reporting...
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print('Feasible solution found, may not be optimal.')
    model.solutions.load_from(results)
    # Verification and reporting...
else:
    print(f'Solve failed: {results.solver.termination_condition}')
```

### Common Pitfalls
- Loading solutions automatically without checking termination condition, which can load invalid results.
- Using a solver interface that requires specific option syntax; stick to documented, minimal options.
- Neglecting to use a tolerance (e.g., `1e-6`) when verifying equality constraints due to numerical precision.
