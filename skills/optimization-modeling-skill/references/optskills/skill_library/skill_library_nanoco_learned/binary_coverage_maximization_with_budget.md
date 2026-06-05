---
name: Binary Coverage Maximization with Budget
description: |
  Model and solve binary selection problems to maximize weighted coverage subject to a budget constraint, using two-layer binary variables and activation constraints.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using the OR-Tools linear solver wrapper. The model uses two sets of binary variables to decouple selection decisions from coverage outcomes, linked via linear activation constraints.

### Step 1 - Define Data Structures
- Define clear sets for selectable items (e.g., `items`) and coverage targets (e.g., `targets`).
- Store parameters as dictionaries: `cost[item]`, `weight[target]`, and `budget`.
- Represent coverage relationships as a mapping `coverage_map[target] = [list_of_items]`.

### Step 2 - Create Binary Variables
- Create selection variables: `x[item] = solver.IntVar(0, 1, f'x_{item}')`.
- Create coverage indicator variables: `y[target] = solver.IntVar(0, 1, f'y_{target}')`.

### Step 3 - Build Coverage Activation Constraints
- For each target `t`, create a constraint: `solver.Constraint(-solver.infinity(), 0)`.
- Set coefficient for `y[t]` to `1`.
- For each covering item `i` in `coverage_map[t]`, set coefficient for `x[i]` to `-1`.
- This enforces `y[t] <= sum(x[i] for i in coverage_map[t])`.

### Step 4 - Add Budget Constraint
- Create a constraint: `solver.Constraint(-solver.infinity(), budget)`.
- For each item `i`, set coefficient `cost[i]` for variable `x[i]`.

### Step 5 - Define Weighted Objective
- Set the objective to maximize: `solver.Maximize(solver.Sum(weight[t] * y[t] for t in targets))`.

### Formulation Template
```json
{
  "sets": ["items", "targets"],
  "parameters": {
    "cost": {"item": "float"},
    "weight": {"target": "float"},
    "budget": "float",
    "coverage_map": {"target": ["list_of_items"]}
  },
  "decision_variables": {
    "x": {"item": "binary"},
    "y": {"target": "binary"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(weight[t] * y[t] for t in targets)"
  },
  "constraints": [
    "y[t] <= sum(x[i] for i in coverage_map[t]) for each target t",
    "sum(cost[i] * x[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Forgetting to set the coefficient for the coverage indicator variable `y[t]` to `1` in the activation constraint, resulting in an incorrect inequality.
- Using `==` instead of `<=` in coverage constraints, which forces coverage when an item is selected and may eliminate beneficial solutions.
- Not verifying that the `coverage_map` dictionary includes all targets, which can lead to missing constraints.

## Solving stage

### Strategy Overview
Solve the MIP using the OR-Tools wrapper for SCIP or CBC. Configure solver parameters for performance and implement robust solution extraction and validation.

### Step 1 - Initialize Solver
- Create solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`. Check if `solver` is not `None`.
- Configure performance: `solver.SetTimeLimit(time_limit_ms)` and `solver.SetNumThreads(num_threads)`.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve()`.
- Check status using `result_status = solver.ResultStatus()`, not `solver.Objective().Value()`. Verify status is `OPTIMAL` or `FEASIBLE`.

### Step 3 - Extract Solution with Tolerance
- For binary variables, use `if var.solution_value() > 0.5:` to determine selection/coverage.
- Collect lists: `selected_items = [i for i in items if x[i].solution_value() > 0.5]`.
- Calculate derived metrics: `total_cost = sum(cost[i] for i in selected_items)`.

### Step 4 - Validate Solution
- Verify budget: Ensure `total_cost <= budget`.
- Verify coverage: For each target where `y[t].solution_value() > 0.5`, confirm at least one item in `coverage_map[t]` is selected.

### Step 5 - Output Structured Results
- Return a JSON object containing solver status, objective value, total cost, selected items, covered targets, and a validation flag.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise RuntimeError('Solver not available.')
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)
result_status = solver.Solve()

status_map = {0: 'OPTIMAL', 1: 'FEASIBLE', 2: 'INFEASIBLE', ...}
status = status_map.get(result_status, 'UNKNOWN')
if status not in ['OPTIMAL', 'FEASIBLE']:
    return {'status': status, 'message': 'No feasible solution found.'}

# Extract solution
selected = [i for i in items if x[i].solution_value() > 0.5]
covered = [t for t in targets if y[t].solution_value() > 0.5]
total_cost = sum(cost[i] for i in selected)
obj_value = solver.Objective().Value()
# ... (validation and output)
```

### Common Pitfalls
- Assuming `solver.Objective().Value()` is valid without checking `ResultStatus()` first, which can lead to errors on infeasible models.
- Using `== 1.0` to interpret binary variables, risking misclassification due to floating-point tolerances.
- Not setting a time limit, potentially causing the solver to run indefinitely on large instances.

# Workflow 2 (Pyomo with CBC/HiGHS)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's `ConcreteModel` for a declarative formulation. This approach cleanly separates model construction from solver interaction and supports multiple open-source backends like CBC and HiGHS.

### Step 1 - Define Pyomo Sets and Parameters
- Define sets: `model.items = pyo.Set(initialize=items)`, `model.targets = pyo.Set(initialize=targets)`.
- Define parameters: `model.cost = pyo.Param(model.items, initialize=cost_dict)`, `model.weight = pyo.Param(model.targets, initialize=weight_dict)`, `model.budget = pyo.Param(initialize=budget)`.
- Define coverage parameter: `model.coverage = pyo.Param(model.targets, within=pyo.Any, initialize=coverage_map)`.

### Step 2 - Create Binary Variables
- Define selection variables: `model.x = pyo.Var(model.items, within=pyo.Binary)`.
- Define coverage variables: `model.y = pyo.Var(model.targets, within=pyo.Binary)`.

### Step 3 - Build Coverage Activation Constraints
- Define a rule: `def coverage_rule(model, t): return model.y[t] <= sum(model.x[i] for i in model.coverage[t])`.
- Create constraint: `model.coverage_constr = pyo.Constraint(model.targets, rule=coverage_rule)`.

### Step 4 - Add Budget Constraint
- Define rule: `def budget_rule(model): return sum(model.cost[i] * model.x[i] for i in model.items) <= model.budget`.
- Create constraint: `model.budget_constr = pyo.Constraint(rule=budget_rule)`.

### Step 5 - Define Weighted Objective
- Define objective: `model.obj = pyo.Objective(expr=sum(model.weight[t] * model.y[t] for t in model.targets), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["items", "targets"],
  "parameters": {
    "cost": {"item": "float"},
    "weight": {"target": "float"},
    "budget": "float",
    "coverage": {"target": ["list_of_items"]}
  },
  "decision_variables": {
    "x": {"item": "binary"},
    "y": {"target": "binary"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(weight[t] * y[t] for t in targets)"
  },
  "constraints": [
    "y[t] <= sum(x[i] for i in coverage[t]) for each target t",
    "sum(cost[i] * x[i] for i in items) <= budget"
  ]
}
```

### Common Pitfalls
- Using mutable data structures (like lists) inside Pyomo rules without proper handling, which can cause unexpected behavior.
- Defining the coverage parameter with an incorrect domain (e.g., `pyo.Reals`) instead of `pyo.Any` for a list.
- Forgetting to initialize all parameters, leading to `KeyError` during model construction.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or HiGHS solver via `SolverFactory`. Configure solver options, handle solution loading explicitly, and implement comprehensive status checking.

### Step 1 - Initialize Solver with Options
- Create solver: `solver = pyo.SolverFactory('cbc')`.
- Set options: `solver.options['seconds'] = time_limit`, `solver.options['ratio'] = optimality_gap`.

### Step 2 - Solve with Explicit Solution Loading
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=False)`.
- Check termination condition: `termination = str(results.solver.termination_condition)`.
- Check solver status: `status = results.solver.status`.

### Step 3 - Load and Extract Solution
- If status is `ok` and termination is `optimal` or `feasible`, load solution: `model.solutions.load_from(results)`.
- Extract selected items: `selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]`.
- Calculate total cost and objective value.

### Step 4 - Validate and Output
- Perform the same logical validation as in Workflow 1.
- Package results into a structured dictionary or JSON object.

### Step 5 - Implement Solver Fallback
- If the primary solver fails, try an alternative (e.g., switch from `'cbc'` to `'highs'`).
- Maintain the same model structure; only change the solver factory.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.items = pyo.Set(initialize=items)
# ... (build model as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0

results = solver.solve(model, load_solutions=False, tee=False)
status = results.solver.status
termination = str(results.solver.termination_condition)

if status == pyo.SolverStatus.ok and termination in ['optimal', 'feasible']:
    model.solutions.load_from(results)
    selected = [i for i in model.items if pyo.value(model.x[i]) > 0.5]
    covered = [t for t in model.targets if pyo.value(model.y[t]) > 0.5]
    total_cost = sum(pyo.value(model.cost[i]) for i in selected)
    obj_value = pyo.value(model.obj)
    # ... (validation and output)
else:
    return {'status': 'FAILED', 'termination': termination, 'solver_status': str(status)}
```

### Common Pitfalls
- Attempting to access variable values via `pyo.value()` before loading the solution, resulting in `ValueError`.
- Not checking both `solver.status` and `termination_condition`, potentially misinterpreting suboptimal or failed solves.
- Using `tee=True` in production without capturing or suppressing the verbose solver log output.
