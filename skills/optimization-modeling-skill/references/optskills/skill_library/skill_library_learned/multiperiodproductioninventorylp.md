---
name: MultiPeriodProductionInventoryLP
description: |
  Model and solve multi-period production-inventory problems with resource capacity constraints and sales limits using linear programming, with workflows for both direct solver APIs and algebraic modeling languages.
---

# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (OR-Tools) to construct the model imperatively. Variables and constraints are created one by one, which offers fine-grained control and is well-suited for prototyping or embedding within larger applications.

### Step 1 - Define Core Sets and Parameters
- Define sets for `periods`, `products`, and `machines` as lists or ranges.
- Create dictionaries for parameters: `profit_per_unit[p]`, `holding_cost`, `machine_time_required[m][p]`, `machine_capacity[m][t]`, `max_sales[p][t]`, and `target_inventory[p]`. Use consistent nested dictionary structures for clarity and easy iteration.

### Step 2 - Create Decision Variables
- Create three dictionaries of non-negative continuous variables: `production[t][p]`, `inventory[t][p]`, and `sales[t][p]`.
- Set variable bounds during creation: `sales[t][p]` bounded by `max_sales[p][t]`. Optionally bound `inventory[t][p]` by a storage capacity. This reduces constraint count and improves performance.

### Step 3 - Formulate Inventory Balance Constraints
- For the initial period (`t=0`), add constraints: `production[0][p] == sales[0][p] + inventory[0][p]`.
- For subsequent periods (`t>0`), add constraints: `inventory[t-1][p] + production[t][p] == sales[t][p] + inventory[t][p]`. This ensures material flow consistency across the planning horizon.

### Step 4 - Add Resource Constraints
- For each machine `m` and period `t`, add capacity constraints: `sum(machine_time_required[m][p] * production[t][p] for p in products) <= machine_capacity[m][t]`.
- **Enforce machine capacity constraints correctly for zero-capacity periods**: If `machine_capacity[m][t] == 0`, the constraint forces all production requiring that machine in that period to zero. Do not skip the constraint.

### Step 5 - Set Terminal Conditions and Objective
- Add terminal inventory constraints: `inventory[final_period][p] == target_inventory[p]`.
- Formulate the objective to maximize total profit: `sum(profit_per_unit[p] * sales[t][p] - holding_cost * inventory[t][p] for t in periods for p in products)`.

### Formulation Template
```json
{
  "sets": ["periods", "products", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "machine_time_required[machine][product]",
    "machine_capacity[machine][period]",
    "max_sales[product][period]",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[period][product] >= 0",
    "inventory[period][product] >= 0",
    "sales[period][product] >= 0"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[t][p] - holding_cost * inventory[t][p])"
  },
  "constraints": [
    "initial_balance: production[0][p] == sales[0][p] + inventory[0][p]",
    "balance: inventory[t-1][p] + production[t][p] == sales[t][p] + inventory[t][p] for t>0",
    "machine_capacity: sum(machine_time_required[m][p] * production[t][p]) <= machine_capacity[m][t]",
    "terminal_inventory: inventory[final_period][p] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Forgetting to handle the initial period (`t=0`) separately in the inventory balance, leading to an index error for `t-1`.
- Not verifying that all parameter dictionaries are fully populated for all indices, which can cause silent constraint omissions.
- Defining sales limits as separate constraints when they could be more efficiently set as upper bounds during variable creation.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' linear solver wrapper. Focus on setting practical limits, robust status checking, and systematic solution extraction for validation and reporting.

### Step 1 - Initialize Solver and Set Limits
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')` for LP or `'CBC'` for MIP. GLOP is free and handles medium-sized problems efficiently.
- Set a time limit to prevent hanging: `solver.SetTimeLimit([TIME_LIMIT_MS])` (e.g., 30000 milliseconds).

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check for optimal or feasible status: `if status in (solver.OPTIMAL, solver.FEASIBLE):`.

### Step 3 - Extract and Validate Solution
- Extract variable values using `.solution_value()` and store in structured dictionaries.
- Programmatically verify key constraints (e.g., inventory balance, capacity usage, sales bounds, terminal inventory) against the extracted values to confirm feasibility within tolerance (e.g., 1e-6).
- **Extract and analyze dual values for sensitivity analysis**: Access `constraint.DualValue()` for machine capacity and balance constraints. Positive dual values on capacity constraints indicate the marginal profit increase from an extra unit of capacity.
- **Analyze reduced costs for optimality insights**: For variables at their bounds (e.g., production = 0 or sales at max_sales), a non-zero reduced cost confirms the bound is active. For a maximization problem, a variable at its lower bound should have `reduced_cost <= 0`; a variable at its upper bound should have `reduced_cost >= 0`.

### Step 4 - Report Results
- Print the objective value rounded to two decimal places: `print(f'RESULT:{solver.Objective().Value():.2f}')`.
- Output a clear, actionable production plan: display production, inventory, and sales for each product and period where values are non-trivial (e.g., > 0.001). Include a summary with total revenue, holding cost, and profit, calculated separately from solution values for validation.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable and constraint creation code)
solver.SetTimeLimit([TIME_LIMIT_MS])

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract solution
    obj_val = solver.Objective().Value()
    print(f'RESULT:{obj_val:.2f}')
    # ... extract, validate, and report variable values
else:
    print('Solver failed to find a solution.')
```

### Common Pitfalls
- Assuming `solver.Solve()` returns only `OPTIMAL`; always also accept `FEASIBLE` for time-limited runs.
- Not setting a time limit, which can cause the process to hang on large or poorly formulated models.
- Extracting variable values without checking the solver status first, leading to errors.

# Workflow 2 (Algebraic Modeling Language - Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses an algebraic modeling language (Pyomo) to declare the model abstractly using sets, parameters, and rules. This approach enhances readability, maintainability, and is closer to the mathematical formulation.

### Step 1 - Declare Abstract Sets and Parameters
- Use `pyo.Set()` to define abstract sets for `periods`, `products`, and `machines`.
- Use `pyo.Param()` within indexed sets to declare all necessary parameters (profit, costs, capacities, limits). Ensure all required indices are initialized to avoid runtime errors.

### Step 2 - Define Decision Variables with Rules
- Define `pyo.Var()` for `production`, `inventory`, and `sales`, indexed over `periods` and `products`, with domain `pyo.NonNegativeReals`.
- Use `bounds` rule or parameter to set variable bounds (e.g., `sales[t,p] <= max_sales[p,t]`, inventory capacity).

### Step 3 - Construct Constraints with Rule Functions
- Define a rule function for inventory balance that uses conditional logic (`if t == 0`) or `Constraint.Skip` to handle the initial period.
- Define separate rule functions for machine capacity and sales limits, iterating over the respective sets.
- **Enforce machine capacity constraints correctly for zero-capacity periods**: When `machine_capacity[m,t] == 0`, the constraint `sum(machine_time_required[m,p] * production[t,p] for p in products) <= 0` must be added. Do not skip the constraint.

### Step 4 - Enforce Terminal Conditions and Objective
- Add a terminal inventory constraint as a simple equality rule indexed by products for the final period.
- Define the objective using a `pyo.Objective` rule that sums profit minus holding costs across all indices.

### Formulation Template
```json
{
  "sets": ["periods", "products", "machines"],
  "parameters": [
    "profit_per_unit[product]",
    "holding_cost",
    "machine_time_required[machine, product]",
    "machine_capacity[machine, period]",
    "max_sales[product, period]",
    "target_inventory[product]"
  ],
  "decision_variables": [
    "production[period, product] in NonNegativeReals",
    "inventory[period, product] in NonNegativeReals",
    "sales[period, product] in NonNegativeReals"
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit_per_unit[p] * sales[t,p] - holding_cost * inventory[t,p])"
  },
  "constraints": [
    "balance_rule(t, p): inventory[t-1,p] + production[t,p] == sales[t,p] + inventory[t,p], with special case for t=0",
    "machine_cap_rule(m, t): sum(machine_time_required[m,p] * production[t,p]) <= machine_capacity[m,t]",
    "terminal_inv_rule(p): inventory[final_period,p] == target_inventory[p]"
  ]
}
```

### Common Pitfalls
- Using 1-based indexing in rule logic while Python uses 0-based indexing for list-derived sets, causing off-by-one errors.
- Forgetting to handle the `t=0` case in the balance rule, resulting in an attempt to access `inventory[-1, p]`.
- Declaring parameters without initializing all required indices, which leads to runtime errors when the rule is constructed.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external solver interface (e.g., HiGHS, CBC). Configure solver options, implement robust solution loading, and perform post-solution verification.

### Step 1 - Configure and Execute Solver
- Create a solver instance: `solver = pyo.SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = [TIME_LIMIT]`, `solver.options['threads'] = [NUM_THREADS]`.

### Step 2 - Solve with Robust Status Handling
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=False)`.
- Check the solver status and termination condition before loading the solution.

### Step 3 - Load Solution and Verify
- If the status is acceptable (`optimal` or `feasible`), load the solution: `model.solutions.load_from(results)`.
- Programmatically verify constraint satisfaction by iterating through constraints and comparing the left-hand side and right-hand side values. Calculate the maximum absolute error to confirm feasibility within tolerance.
- **Perform a basic optimality verification**: Ensure reduced costs have the correct sign for the problem type (maximization). Variables at their lower bound should have `reduced_cost <= 0`; variables at their upper bound should have `reduced_cost >= 0`.

### Step 4 - Analyze and Report
- Extract the objective value: `pyo.value(model.objective)`.
- Print the result rounded to two decimal places: `print(f'RESULT:{pyo.value(model.objective):.2f}')`.
- Output a clear, actionable production plan: display production, inventory, and sales for each product and period where values are non-trivial (e.g., > 0.001). Include a summary with total revenue, holding cost, and profit.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (set, parameter, variable, constraint, objective definition)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
results = solver.solve(model, load_solutions=False)

from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    model.solutions.load_from(results)
    print(f'RESULT:{pyo.value(model.objective):.2f}')
    # ... perform verification and detailed reporting
else:
    print('Solver failed to find a solution.')
```

### Common Pitfalls
- Loading the solution without checking the termination condition, which may load an infeasible or suboptimal point.
- Not using `load_solutions=False`, which can cause confusion if the solver fails but the model retains a previous solution.
- Omitting post-solution verification, missing potential numerical issues or formulation errors.
