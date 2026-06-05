---
name: Multi-Period Production-Inventory Planning
description: |
  Formulate and solve multi-period production planning problems with inventory balance, capacity constraints, and terminal conditions, using both continuous and integer variable approaches.
---

# Workflow 1 (Linear Programming Relaxation)

## Modeling stage

### Strategy Overview
Model the problem as a Linear Program (LP) using continuous variables. This provides a theoretical upper bound on profit and is useful for initial feasibility checks, sensitivity analysis, or when fractional production is acceptable (e.g., in high-volume fluid production).

### Step 1 - Define Sets and Parameters
- Define sets for `products`, `machines`, and `periods`.
- Define parameters for `profit_per_unit`, `holding_cost`, `production_time`, `machine_capacity`, `max_sales`, `max_inventory`, and `terminal_inventory_target`.

### Step 2 - Define Continuous Decision Variables
- Define `production[product, period]` as `NonNegativeReals`.
- Define `sales[product, period]` as `NonNegativeReals`.
- Define `inventory[product, period]` as `NonNegativeReals`.

### Step 3 - Formulate Inventory Balance Constraints
- For the first period, enforce `production[p,0] = sales[p,0] + inventory[p,0]`.
- For subsequent periods, enforce `inventory[p,t-1] + production[p,t] = sales[p,t] + inventory[p,t]`.

### Step 4 - Formulate Capacity and Bound Constraints
- For each machine and period, enforce `sum(production_time[m][p] * production[p,t] for p in products) <= machine_capacity[m][t]`.
- For each product and period, enforce `sales[p,t] <= max_sales[p][t]`.
- For each product and period, enforce `inventory[p,t] <= max_inventory`.

### Step 5 - Formulate Terminal Inventory and Objective
- For each product, enforce `inventory[p, final_period] = terminal_inventory_target[p]`.
- Maximize `sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)`.

### Formulation Template
```json
{
  "sets": ["products", "machines", "periods"],
  "parameters": {
    "profit_per_unit": {"product": "float"},
    "holding_cost": "float",
    "production_time": {"machine": {"product": "float"}},
    "machine_capacity": {"machine": {"period": "float"}},
    "max_sales": {"product": {"period": "float"}},
    "max_inventory": "float",
    "terminal_inventory_target": {"product": "float"}
  },
  "decision_variables": {
    "production": {"product": "period", "domain": "NonNegativeReals"},
    "sales": {"product": "period", "domain": "NonNegativeReals"},
    "inventory": {"product": "period", "domain": "NonNegativeReals"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)"
  },
  "constraints": [
    "inventory_balance_first_period",
    "inventory_balance_subsequent_periods",
    "machine_capacity",
    "sales_upper_bound",
    "inventory_upper_bound",
    "terminal_inventory"
  ]
}
```

### Common Pitfalls
- Using continuous variables for problems requiring discrete unit decisions, leading to operationally infeasible fractional solutions.
- Overlooking the implicit integer requirement signaled by terms like "number of units" in the problem context.
- Accepting the LP solution as final without verifying if the context demands integer feasibility.

## Solving stage

### Strategy Overview
Solve the LP model using a high-performance solver (e.g., HiGHS) to obtain a continuous solution. Focus on verifying feasibility, analyzing constraints, and using the result as a bound for integer models.

### Step 1 - Configure and Run Solver
- Instantiate the solver (e.g., `SolverFactory('highs')`).
- Set options for performance: `time_limit=30`, `threads=4`, `presolve='on'`.
- Solve the model with `tee=True` for initial debugging.

### Step 2 - Check Solver Status and Load Solution
- After solving, check the solver termination condition (e.g., `optimal`, `feasible`).
- Use `load_solutions=False` initially to avoid errors on infeasible runs, then load solutions only if status is acceptable.

### Step 3 - Verify Solution and Analyze Results
- Programmatically verify key constraints are satisfied (e.g., terminal inventory equals target, capacity limits).
- Extract and display production, sales, and inventory quantities.
- Calculate and report total revenue, holding costs, and net profit separately to validate the objective value.

### Step 4 - Perform Bottleneck Analysis
- Calculate machine utilization per period: `sum(production_time[m][p] * production[p,t]) / machine_capacity[m][t]`.
- Identify periods and machines with 100% utilization, as these constrain further profit improvement.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (model construction based on formulation template)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, load_solutions=False, tee=False)

# Check status and load solution
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    print("Optimal LP solution found.")
    # ... (solution verification and analysis)
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    model.solutions.load_from(results)
    print("Feasible LP solution found.")
else:
    print("Solver failed. Status:", results.solver.termination_condition)
    # ... (diagnostic output for infeasibility)
```

### Common Pitfalls
- Accepting the first solver output without examining solution feasibility (e.g., fractional values for discrete units).
- Neglecting to verify constraint satisfaction programmatically after solving.
- Switching to an integer model without first using the LP solution to identify binding constraints and performance bounds.

# Workflow 2 (Mixed-Integer Programming)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Program (MIP) using integer variables for production, sales, and inventory. This yields operationally feasible solutions for contexts requiring whole units and is necessary when the LP relaxation is not implementable.

### Step 1 - Define Sets and Parameters
- Use the same set and parameter structure as Workflow 1.

### Step 2 - Define Integer Decision Variables
- Define `production[product, period]` as `NonNegativeIntegers`.
- Define `sales[product, period]` as `NonNegativeIntegers`.
- Define `inventory[product, period]` as `NonNegativeIntegers`.

### Step 3 - Formulate Inventory Balance Constraints
- Apply the same inventory balance constraints as in Workflow 1, ensuring material flow consistency with integer variables.

### Step 4 - Formulate Capacity and Bound Constraints
- Apply the same capacity, sales upper bound, and inventory upper bound constraints as in Workflow 1.

### Step 5 - Formulate Terminal Inventory and Objective
- Enforce the same terminal inventory equality constraints.
- Use the same profit-maximizing objective function.

### Formulation Template
```json
{
  "sets": ["products", "machines", "periods"],
  "parameters": {
    "profit_per_unit": {"product": "float"},
    "holding_cost": "float",
    "production_time": {"machine": {"product": "float"}},
    "machine_capacity": {"machine": {"period": "float"}},
    "max_sales": {"product": {"period": "float"}},
    "max_inventory": "float",
    "terminal_inventory_target": {"product": "float"}
  },
  "decision_variables": {
    "production": {"product": "period", "domain": "NonNegativeIntegers"},
    "sales": {"product": "period", "domain": "NonNegativeIntegers"},
    "inventory": {"product": "period", "domain": "NonNegativeIntegers"}
  },
  "objective": {
    "sense": "max",
    "expression": "sum(profit_per_unit[p] * sales[p,t] - holding_cost * inventory[p,t] for p in products for t in periods)"
  },
  "constraints": [
    "inventory_balance_first_period",
    "inventory_balance_subsequent_periods",
    "machine_capacity",
    "sales_upper_bound",
    "inventory_upper_bound",
    "terminal_inventory"
  ]
}
```

### Common Pitfalls
- Starting with an LP model when the problem context clearly requires integer decisions, wasting time on an infeasible relaxation.
- Using the same variable domain (e.g., `NonNegativeReals`) for all formulations without justifying the choice.
- Overlooking the potential for a significant gap between the LP upper bound and the integer optimum.

## Solving stage

### Strategy Overview
Solve the MIP model using a MIP-capable solver (e.g., HiGHS, CBC) with appropriate optimality gap settings. Focus on obtaining and verifying a proven optimal or high-quality feasible integer solution.

### Step 1 - Configure MIP Solver with Tight Gaps
- Instantiate the solver (e.g., `SolverFactory('highs')`).
- Set MIP-specific options: `mip_rel_gap=0.000001` (or a small tolerance), `time_limit=60`.
- Enable presolving and set thread count for performance.

### Step 2 - Solve and Rigorously Check Status
- Solve the model with `load_solutions=False`.
- Check both the solver termination condition and solution status.
- Load the solution only if status indicates optimal or integer feasible.

### Step 3 - Verify Integer Feasibility and Constraints
- Programmatically verify that all decision variable values are integers.
- Re-check all constraints (capacity, inventory balance, bounds) to ensure the integer solution is feasible.
- Confirm terminal inventory requirements are met exactly.

### Step 4 - Analyze Optimality and Performance
- Report the MIP optimality gap from the solver results.
- Compare the MIP objective value to the LP upper bound from Workflow 1 to understand the integrality gap.
- Extract and display the integer production plan.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (model construction with integer variables)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = 1e-6
solver.options['threads'] = 4
results = solver.solve(model, load_solutions=False, tee=False)

# Check status and load solution
status_ok = (
    results.solver.termination_condition == pyo.TerminationCondition.optimal or
    results.solver.termination_condition == pyo.TerminationCondition.feasible
)
if status_ok and results.solver.status == pyo.SolverStatus.ok:
    model.solutions.load_from(results)
    print("Integer solution loaded.")
    # ... (integer feasibility and constraint verification)
else:
    print("Solver did not find a suitable integer solution.")
    print("Termination condition:", results.solver.termination_condition)
```

### Common Pitfalls
- Not setting a tight MIP gap, leading to premature acceptance of suboptimal solutions.
- Assuming an integer solution is optimal without checking solver statistics (e.g., nodes explored, gap).
- Neglecting to verify that the loaded solution satisfies all constraints, especially after a non-optimal termination.
