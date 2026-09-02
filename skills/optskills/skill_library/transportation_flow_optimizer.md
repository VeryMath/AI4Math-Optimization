---
name: Transportation Flow Optimizer
description: |
  Model and solve capacitated transportation problems with supply limits, demand satisfaction, and arc capacity constraints to minimize total flow cost.

---
# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
Formulate the problem directly within a solver's native API (e.g., OR-Tools) by defining variables with bounds, adding constraints via summation, and setting a linear objective. This approach is procedural and tightly couples the model to the solver's construction methods.

### Step 1 - Define Problem Dimensions and Data
- Identify the number of origins (`num_origins`) and destinations (`num_dests`).
- Organize input data into 2D lists/arrays for `cost` and `capacity`, and 1D lists for `supply` and `demand`. Ensure all dimensions align.
- **Check Problem Balance**: Verify total supply equals total demand. If not balanced, introduce dummy nodes or adjust constraints accordingly.

### Step 2 - Create Solver and Decision Variables
- Instantiate the solver (e.g., `solver = pywraplp.Solver.CreateSolver('GLOP')`).
- Create a 2D array of continuous decision variables `flow[i][j]`. Set the lower bound to 0 and the upper bound to `capacity[i][j]` directly in the variable creation to implicitly handle arc capacities.

### Step 3 - Add Supply and Demand Constraints
- For each origin `i`, add a constraint: `sum(flow[i][j] for j in destinations) == supply[i]`.
- For each destination `j`, add a constraint: `sum(flow[i][j] for i in origins) == demand[j]`.

### Step 4 - Set the Objective Function
- Define the objective as the sum of `flow[i][j] * cost[i][j]` across all arcs.
- Set the objective for minimization using the solver's method (e.g., `solver.Minimize(objective_expression)`).

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply[origins]", "demand[destinations]", "cost[origins][destinations]", "capacity[origins][destinations]"],
  "decision_variables": ["flow[origins][destinations]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in origins for j in destinations)"
  },
  "constraints": [
    "sum(flow[i][j] for j in destinations) == supply[i] for all i in origins",
    "sum(flow[i][j] for i in origins) == demand[j] for all j in destinations",
    "0 <= flow[i][j] <= capacity[i][j] for all i in origins, j in destinations"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce non-negativity; ensure variable lower bounds are set to 0.
- Mismatching indices between supply/demand lists and the variable matrix, causing constraint errors.
- Using `<=` for supply/demand constraints when exact fulfillment (`==`) is required for a balanced problem.

## Solving stage

### Strategy Overview
Solve the constructed model using the solver's native methods, check the solution status, extract results, and perform post-solution validation to ensure all constraints are satisfied within a tolerance.

### Step 1 - Invoke the Solver
- Call the solver's `Solve()` method.
- Store the returned status code (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).

### Step 2 - Check Solution Status and Extract Results
- If status is `OPTIMAL` or `FEASIBLE`, retrieve the objective value.
- Iterate through all `flow` variables to collect their `solution_value()`.
- If the status indicates infeasibility or error, exit with a structured error message.

### Step 3 - Validate the Solution
- Recalculate total flow from each origin and into each destination.
- Verify these values are within tolerance of the `supply` (`==`) and `demand` (`==`) parameters.
- Check that no flow exceeds its `capacity`.

### Step 4 - Report the Solution
- Print the objective value in a parseable format: `RESULT:{objective_value}`.
- Optionally, output non-zero flows or a summary of constraint satisfaction for debugging.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
flow = [[solver.NumVar(0, capacity[i][j], f'flow_{i}_{j}') for j in range(num_dests)] for i in range(num_origins)]
# Add supply & demand constraints
for i in range(num_origins):
    solver.Add(sum(flow[i][j] for j in range(num_dests)) == supply[i])
for j in range(num_dests):
    solver.Add(sum(flow[i][j] for i in range(num_origins)) == demand[j])
# Set objective
objective = solver.Objective()
for i in range(num_origins):
    for j in range(num_dests):
        objective.SetCoefficient(flow[i][j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'RESULT:{objective.Value()}')
else:
    print(f'{{"status": "FAILED", "reason": "Solver returned status {status}"}}')
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, potentially missing valid solutions.
- Failing to handle solver instantiation errors (e.g., if `GLOP` is not available).
- Assuming variable values exist without checking the solve status first.

# Workflow 2 (Modeling Language with Solver Factory)

## Modeling stage

### Strategy Overview
Use a modeling abstraction (e.g., Pyomo) to declaratively define sets, parameters, variables, and constraints. This separates the problem formulation from the solver interface, allowing for solver agnosticism and easier model inspection.

### Step 1 - Declare Abstract Model Components
- Define Pyomo `Set` components for `origins` and `destinations`.
- Define `Param` components for `supply`, `demand`, `cost`, and `capacity`, indexed by the appropriate sets.
- **Check Problem Balance**: Verify total supply equals total demand. If not balanced, introduce dummy nodes or adjust constraints accordingly.

### Step 2 - Define Decision Variables and Bounds
- Define a `Var` component `flow`, indexed over `(origins, destinations)`, within `pyo.NonNegativeReals`.
- Apply upper bounds (`flow[i,j].ub = capacity[i,j]`) to enforce arc capacities, either during variable creation or via a rule.

### Step 3 - Construct Constraints Declaratively
- Define a `ConstraintList` or use rule-based `Constraint` components.
- Add supply limit constraint: `sum(flow[i,j] for j in destinations) == supply[i]`.
- Add demand satisfaction constraint: `sum(flow[i,j] for i in origins) == demand[j]`.

### Step 4 - Define the Objective Function
- Define an `Objective` rule to minimize `sum(cost[i,j] * flow[i,j] for i in origins for j in destinations)`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations"],
  "parameters": ["supply[origins]", "demand[destinations]", "cost[origins][destinations]", "capacity[origins][destinations]"],
  "decision_variables": ["flow[origins][destinations]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * flow[i][j] for i in origins for j in destinations)"
  },
  "constraints": [
    "sum(flow[i][j] for j in destinations) == supply[i] for all i in origins",
    "sum(flow[i][j] for i in origins) == demand[j] for all j in destinations",
    "flow[i][j] <= capacity[i][j] for all i in origins, j in destinations"
  ]
}
```

### Common Pitfalls
- Confusing Pyomo's `AbstractModel` with `ConcreteModel`; choose based on whether data is provided at model creation or later.
- Incorrectly indexing parameters within constraint rules, leading to `KeyError`.
- Forgetting to set the `sense` (minimize/maximize) on the objective.

## Solving stage

### Strategy Overview
Use a solver factory to interface with different solvers (e.g., HiGHS, CBC). Configure solver options, solve the model, and then programmatically interrogate the solver results and model instance to extract and validate the solution.

### Step 1 - Select and Configure the Solver
- Use `SolverFactory('solver_name')` to create a solver interface.
- Set options like time limit (`sec`), optimality gap (`ratio`), and number of threads (`threads`) if applicable.

### Step 2 - Solve and Check Termination Status
- Execute `solver.solve(model)`.
- Check the solver status (`model.solver.status`) and termination condition (`model.solver.termination_condition`) to confirm optimality or feasibility.

### Step 3 - Extract and Validate Solution
- If solve was successful, retrieve the objective value via `pyo.value(model.obj)`.
- Iterate through the `flow` variable to collect its `value`.
- Perform post-solve validation: recalculate sums and compare against `supply` and `demand` with a tolerance (e.g., `1e-6`).

### Step 4 - Output and Error Handling
- Output the objective value as `RESULT:{objective_value}`.
- If the solve failed, output a JSON object containing the solver status and termination condition for diagnostics.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.origins = pyo.Set(initialize=origins_list)
model.dests = pyo.Set(initialize=dests_list)
model.flow = pyo.Var(model.origins, model.dests, within=pyo.NonNegativeReals, bounds=lambda m, i, j: (0, capacity[i][j]))
# Define constraints
model.supply_con = pyo.Constraint(model.origins, rule=lambda m, i: sum(m.flow[i,j] for j in m.dests) == supply[i])
model.demand_con = pyo.Constraint(model.dests, rule=lambda m, j: sum(m.flow[i,j] for i in m.origins) == demand[j])
# Define objective
model.obj = pyo.Objective(expr=sum(cost[i][j] * model.flow[i,j] for i in model.origins for j in model.dests), sense=pyo.minimize)

# solve with status / termination checks
solver = SolverFactory('highs')
results = solver.solve(model)
if model.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f'RESULT:{pyo.value(model.obj)}')
else:
    print(f'{{"status": "{model.solver.status}", "termination_condition": "{model.solver.termination_condition}"}}')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`; a status of `ok` does not guarantee optimality.
- Attempting to access variable values from an unsolved or infeasible model, which may raise an error.
- Misconfiguring solver options specific to the chosen solver (e.g., using `timeLimit` for one solver vs. `sec` for another).
