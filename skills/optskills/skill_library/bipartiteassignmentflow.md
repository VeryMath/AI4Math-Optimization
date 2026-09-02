---
name: BipartiteAssignmentFlow
description: |
  Model and solve linear bipartite assignment problems with flow quantities, demand satisfaction, and unconstrained supply to maximize total profit or minimize total cost.
---

# Workflow 1 (Linear Programming with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the problem as a linear program using Google's OR-Tools `pywraplp` API. It is ideal for prototyping and solving pure LP formulations with a clean, imperative modeling style. The solver backend (GLOP) is efficient for continuous problems.

### Step 1 - Define Data Structures
- Organize problem data into lists or dictionaries for clear indexing. Use `profit[i][j]` for the per-unit profit from source `i` to sink `j` and `demand[j]` for the required flow to each sink.
- Use `solver.infinity()` to represent unlimited upper bounds, reflecting the unconstrained supply capacity.

### Step 2 - Create Decision Variables
- Instantiate a continuous, non-negative decision variable `x[i][j]` for each source-sink pair using `solver.NumVar(lb, ub, name)`.
- Set the lower bound (`lb`) to `0` and the upper bound (`ub`) to `solver.infinity()` to enforce non-negativity and allow any flow quantity.

### Step 3 - Formulate the Objective
- Build a linear expression by summing `profit[i][j] * x[i][j]` over all variable indices.
- Set the objective sense to maximization using `solver.Maximize(expression)` or `solver.Minimize(expression)` for cost minimization.

### Step 4 - Add Demand Satisfaction Constraints
- For each sink `j`, create an equality constraint with `solver.Constraint(rhs, rhs)`, where `rhs` is `demand[j]`.
- Iterate over all sources `i` and set the coefficient of `x[i][j]` to `1.0` using `constraint.SetCoefficient(var, coeff)` to enforce `sum_i x[i][j] == demand[j]`.

### Formulation Template
```json
{
  "sets": [
    "sources: list of source identifiers",
    "sinks: list of sink identifiers"
  ],
  "parameters": [
    "profit[sources][sinks]: per-unit profit matrix",
    "demand[sinks]: required flow for each sink"
  ],
  "decision_variables": [
    "x[sources][sinks]: continuous, >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in sources, j in sinks} profit[i][j] * x[i][j]"
  },
  "constraints": [
    "demand_satisfaction: for each j in sinks, sum_{i in sources} x[i][j] == demand[j]"
  ]
}
```

### Common Pitfalls
- Forgetting to set the upper bound to infinity, which incorrectly imposes a default bound of 1.0 and limits flow.
- Building constraints with incorrect coefficient signs or values, leading to infeasible or suboptimal solutions.
- Not using a tolerance (e.g., `1e-6`) when checking variable values, which may misclassify near-zero flows as active.

## Solving stage

### Strategy Overview
The solving stage uses the OR-Tools wrapper to invoke the GLOP solver, configures runtime limits, rigorously checks the solution status, and extracts a clean, validated result.

### Step 1 - Configure and Execute the Solver
- Create the solver instance with `pywraplp.Solver.CreateSolver('GLOP')`.
- Set a reasonable time limit using `solver.SetTimeLimit(milliseconds)` to prevent excessive runtime.
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Verify Solution Status
- Check the solver's return status using `status = solver.Solve()`.
- Proceed only if `status` is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract and Validate Results
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate through all decision variables, using `.solution_value()` to get their values. Filter and store only those with values exceeding a small tolerance (e.g., `> 1e-6`).
- Optionally, perform a verification step by recomputing total flow per sink from the extracted solution and comparing it to the original demand.

### Step 4 - Package and Output Results
- Structure the results into a dictionary or JSON payload containing the status, objective value, and a dictionary of non-zero flows.
- Include a simple constraint satisfaction report for debugging purposes.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation as per modeling stage)
solver.SetTimeLimit(30000)  # 30-second limit

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    solution = {}
    for i in sources:
        for j in sinks:
            val = x[i][j].solution_value()
            if val > 1e-6:
                solution[(i, j)] = val
    # Package results...
else:
    # Handle infeasible/unbounded/time limit status
    print(f"Solver did not find an optimal solution. Status: {status}")
```

### Common Pitfalls
- Assuming the solver always returns `OPTIMAL`; failing to check for `FEASIBLE` or other statuses can lead to runtime errors when extracting values.
- Not applying a tolerance when filtering the solution, resulting in verbose output with many near-zero values.
- Omitting the time limit configuration, which may cause the process to hang on large or numerically challenging instances.

# Workflow 2 (Structured Modeling with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract or concrete modeling to define the problem in a declarative, solver-agnostic manner. It separates model specification from solver execution, promoting reusability and integration with advanced features like piecewise linear functions or custom callbacks.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for `model.sources` and `model.sinks`.
- Declare `Param` objects for `model.profit` (indexed by both sets) and `model.demand` (indexed by sinks). Use `initialize` with a dictionary or rule to populate data.

### Step 2 - Declare Decision Variables
- Define a Pyomo `Var` object `model.x`, indexed over `model.sources` and `model.sinks`.
- Set the domain to `pyo.NonNegativeReals` to enforce non-negativity. No upper bound is specified, reflecting unconstrained supply.

### Step 3 - Construct the Objective Function
- Define a `pyo.Objective` rule that sums `model.profit[i, j] * model.x[i, j]` over all indices.
- Set the sense to `pyo.maximize` for profit maximization.

### Step 4 - Implement Demand Constraints via Rules
- Define a `pyo.Constraint` object indexed by `model.sinks`.
- For each sink `j`, the constraint rule should return the expression `sum(model.x[i, j] for i in model.sources) == model.demand[j]`.

### Formulation Template
```json
{
  "sets": [
    "sources: Pyomo Set",
    "sinks: Pyomo Set"
  ],
  "parameters": [
    "profit[sources, sinks]: Pyomo Param",
    "demand[sinks]: Pyomo Param"
  ],
  "decision_variables": [
    "x[sources, sinks]: Pyomo Var, domain=NonNegativeReals"
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[i,j] * x[i,j] for i in sources for j in sinks)"
  },
  "constraints": [
    "demand_satisfaction: for each j in sinks, sum(x[i,j] for i in sources) == demand[j]"
  ]
}
```

### Common Pitfalls
- Confusing 1-based and 0-based indexing when initializing parameters from Python data structures, leading to `KeyError`.
- Defining constraint rules that modify global state or have side effects, which can cause unpredictable behavior during model construction.
- Forgetting to deactivate the default `sense` on the objective, which defaults to minimization.

## Solving stage

### Strategy Overview
The solving stage uses Pyomo's `SolverFactory` to interface with a backend solver (e.g., HiGHS, CBC). It emphasizes robust status checking, solution extraction through the model object, and post-solution validation.

### Step 1 - Select and Configure the Solver
- Instantiate a solver object using `SolverFactory('solver_name')`, e.g., `'highs'` or `'cbc'`.
- Set solver options such as `time_limit` and `threads` for performance control, using `solver.options['key'] = value`.

### Step 2 - Solve and Check Termination Conditions
- Execute `results = solver.solve(model, tee=False)`.
- Inspect `results.solver.status` (should be `SolverStatus.ok`) and `results.solver.termination_condition` (should be `optimal` or `feasible`). Handle other conditions like `infeasible` or `unbounded` appropriately.

### Step 3 - Extract and Process the Solution
- Retrieve the objective value via `pyo.value(model.obj)` (if the objective is named `obj`).
- Iterate over `model.x` to access variable values using `pyo.value(model.x[i, j])` or `model.x[i, j].value`.
- Apply a tolerance to filter out near-zero flows and store the non-zero allocations in a clean dictionary.

### Step 4 - Validate and Report
- Programmatically verify that the extracted solution satisfies the demand constraints within a small numerical tolerance.
- Package the final output, including solver status, objective value, and the filtered solution dictionary.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.sinks = pyo.Set(initialize=sinks_list)
# ... (parameter, variable, objective, and constraint definitions as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    obj_val = pyo.value(model.obj)
    solution = {}
    for i in model.sources:
        for j in model.sinks:
            val = pyo.value(model.x[i, j])
            if val > 1e-6:
                solution[(i, j)] = val
    # Package results...
else:
    # Handle unsuccessful termination
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`; a status of `ok` with a termination of `maxTimeLimit` indicates a suboptimal solution.
- Directly printing the entire model variable dictionary, which can be overwhelming for large problems.
- Assuming the solver updates the model in-place for all solver interfaces; some require explicit loading of the solution.
