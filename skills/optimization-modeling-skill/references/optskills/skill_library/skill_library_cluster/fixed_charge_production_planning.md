---
name: Fixed-Charge Production Planning
description: |
  Model and solve production planning problems with fixed activation costs and variable production costs using mixed-integer linear programming (MILP) with big-M constraints.
---

# Workflow 1 (OR-Tools MILP with SCIP/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using the OR-Tools `pywraplp` API. This approach directly builds a solver model with binary activation variables linked to continuous production variables via big-M constraints, suitable for direct solving with SCIP or CBC.

### Step 1 - Define Sets and Parameters
- Define clear index sets for production sources (e.g., `factories`) and time periods (e.g., `periods`).
- Store all problem data in dictionaries or lists indexed by these sets for easy reference during model building. This includes `fixed_cost`, `variable_cost`, `min_production`, `max_production`, and `demand`.

### Step 2 - Create Decision Variables
- For each source `i` and period `t`, create a binary variable `run[i, t]` (0/1) representing the activation decision.
- For each source `i` and period `t`, create a continuous, non-negative variable `production[i, t]` representing the production quantity.

### Step 3 - Link Activation and Production (Big-M)
- Add a constraint enforcing minimum production if active: `production[i, t] >= min_production[i] * run[i, t]`.
- Add a constraint enforcing maximum production (and zero if inactive): `production[i, t] <= max_production[i] * run[i, t]`. This couples the binary and continuous variables using a tight, data-driven big-M.

### Step 4 - Enforce Demand Satisfaction
- For each time period `t`, add a linear constraint ensuring total production meets demand: `sum(production[i, t] for i in sources) >= demand[t]`.

### Step 5 - Define Linear Cost Objective
- Define the objective to minimize total cost: `sum(fixed_cost[i] * run[i, t] + variable_cost[i] * production[i, t] for all i, t)`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "periods"
  ],
  "parameters": [
    "fixed_cost[sources]",
    "variable_cost[sources]",
    "min_production[sources]",
    "max_production[sources]",
    "demand[periods]"
  ],
  "decision_variables": [
    "run[sources, periods] ∈ {0, 1}",
    "production[sources, periods] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_i Σ_t (fixed_cost[i] * run[i, t] + variable_cost[i] * production[i, t])"
  },
  "constraints": [
    "production_lower[i,t]: production[i, t] ≥ min_production[i] * run[i, t]",
    "production_upper[i,t]: production[i, t] ≤ max_production[i] * run[i, t]",
    "demand_satisfaction[t]: Σ_i production[i, t] ≥ demand[t]"
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound for the continuous `production` variable, which can default to infinity.
- Using an excessively large "M" value in the upper bound constraint; the parameter `max_production[i]` serves as a tight, data-driven big-M.
- Creating variables and constraints with manual loops that risk missing indices; use nested loops over the defined sets.

## Solving stage

### Strategy Overview
Solve the built MILP model using the OR-Tools wrapper for SCIP or CBC. Configure solver limits for performance, check the solution status rigorously, and extract results into a structured format for verification and analysis.

### Step 1 - Initialize Solver and Set Parameters
- Create the solver instance (e.g., `solver = pywraplp.Solver.CreateSolver("SCIP")`). Provide a fallback to "CBC" if preferred solver is unavailable.
- Set practical limits: `solver.SetTimeLimit(time_limit_ms)` and `solver.SetNumThreads(num_threads)` to balance speed and resource use.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve()`.
- Check the result status: `status = solver.optimal()` or `solver.feasible()`. Proceed only if status is `True`; otherwise, handle infeasible or non-optimal outcomes.

### Step 3 - Extract and Verify Solution
- Extract the objective value: `total_cost = solver.Objective().Value()`.
- Extract variable values by iterating over all indices: `run_val = run[i, t].solution_value()` and `prod_val = production[i, t].solution_value()`.
- Implement a post-solve verification: recompute aggregated production per period and ensure it meets demand within a small tolerance (e.g., `1e-6`). Validate that production is zero when `run` is 0 and within bounds when `run` is 1.

### Step 4 - Output Structured Results
- Compile results into a dictionary or JSON object containing the status, objective value, activation decisions, production levels, and aggregated totals (e.g., monthly production).
- This structured output aids in debugging, reporting, and further analysis.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    solver = pywraplp.Solver.CreateSolver("CBC")

# Define sets, parameters, and create variables as per modeling steps.
# ... (variable creation loops)
# ... (constraint addition loops)
# ... (objective definition)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)
status = solver.Solve()

if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    total_cost = solver.Objective().Value()
    solution = {"status": "optimal" if status == pywraplp.Solver.OPTIMAL else "feasible",
                "objective": total_cost,
                "decisions": {}}
    # Extract variable values into solution['decisions']
    # ... (extraction loops)
    # Post-solve verification
    # ... (verification logic)
else:
    solution = {"status": "infeasible_or_unbounded", "objective": None}
```

### Common Pitfalls
- Not checking solver status before extracting variable values, which can cause runtime errors.
- Assuming the solver found an optimal solution; always check for `OPTIMAL` or `FEASIBLE` status.
- Ignoring numerical precision when verifying constraints; use a small tolerance (e.g., `1e-6`) for comparisons.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's concrete modeling environment. This approach separates the problem formulation from the solver interface, improving readability and maintainability. The model is then solved using an external MILP solver like HiGHS or CBC.

### Step 1 - Define Pyomo Sets and Parameters
- Use `pyo.Set` objects to define index sets for sources and periods (e.g., `model.SOURCES`, `model.PERIODS`).
- Use `pyo.Param` objects or Python dictionaries to store all cost, capacity, and demand parameters, indexed by the defined sets.

### Step 2 - Declare Decision Variables
- Declare a binary variable `model.run` indexed over sources and periods, with domain `pyo.Binary`.
- Declare a continuous, non-negative variable `model.production` indexed over the same sets, with domain `pyo.NonNegativeReals`.

### Step 3 - Implement Constraint Rules
- Define a rule function for the production lower bound: `model.production_lower = pyo.Constraint(model.SOURCES, model.PERIODS, rule=prod_lower_rule)`. Inside the rule, return `model.production[i, t] >= min_prod[i] * model.run[i, t]`.
- Similarly, define rules for the production upper bound and demand satisfaction constraints.

### Step 4 - Define Objective Rule
- Define an objective rule function that sums the fixed and variable costs across all indices: `model.total_cost = pyo.Objective(rule=obj_rule, sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": [
    "SOURCES",
    "PERIODS"
  ],
  "parameters": [
    "fixed_cost[SOURCES]",
    "variable_cost[SOURCES]",
    "min_production[SOURCES]",
    "max_production[SOURCES]",
    "demand[PERIODS]"
  ],
  "decision_variables": [
    "run[SOURCES, PERIODS] ∈ Binary",
    "production[SOURCES, PERIODS] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * run[i, t] + variable_cost[i] * production[i, t] for i in SOURCES, t in PERIODS)"
  },
  "constraints": [
    "production_lower[i,t]: production[i, t] ≥ min_production[i] * run[i, t]",
    "production_upper[i,t]: production[i, t] ≤ max_production[i] * run[i, t]",
    "demand_satisfaction[t]: sum(production[i, t] for i in SOURCES) ≥ demand[t]"
  ]
}
```

### Common Pitfalls
- Defining constraint or objective rules with incorrect indexing, leading to `KeyError` or missing constraints.
- Using mutable default arguments (like lists) inside Pyomo rule functions.
- Confusing Pyomo's `value()` function with variable values during model construction; `pyo.value()` is for evaluating expressions *after* solving.

## Solving stage

### Strategy Overview
Solve the Pyomo model by instantiating a solver object (e.g., HiGHS, CBC) via `SolverFactory`. Configure solver options for performance and gap tolerance, enable output for debugging, and rigorously check the termination condition before extracting and verifying the solution.

### Step 1 - Select and Configure Solver
- Create a solver instance: `solver = pyo.SolverFactory("highs")`. Implement a fallback check (e.g., if `solver is None`, try `"cbc"`).
- Set key options: `solver.options["time_limit"] = time_limit`, `solver.options["mip_rel_gap"] = 0.0` (for exact solution), and `solver.options["threads"] = num_threads`.

### Step 2 - Solve with Diagnostics
- Invoke the solver with `results = solver.solve(model, tee=True)`. The `tee=True` flag streams solver output, which is invaluable for debugging and understanding progress.

### Step 3 - Check Solver Status and Termination
- Check if the solver run completed: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: `if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:`. Only extract results under these conditions.

### Step 4 - Extract and Validate Solution
- Extract the objective value: `total_cost = pyo.value(model.total_cost)`.
- Iterate through variables to extract values: `run_val = pyo.value(model.run[i, t])`, `prod_val = pyo.value(model.production[i, t])`. For binary variables, interpret values using a threshold (e.g., `> 0.5`).
- Programmatically verify all constraints: check production bounds against activation status and ensure demand is met. Recalculate the total cost from extracted values to confirm numerical consistency.

### Step 5 - Serialize and Output Results
- Compile results into a structured format. Convert tuple keys (e.g., `(i, t)`) to strings (e.g., `f"source{i}_period{t}"`) for easy JSON serialization.
- Include cost breakdowns (fixed vs. variable) and aggregated production totals in the output.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.SOURCES = pyo.Set(initialize=sources_list)
model.PERIODS = pyo.Set(initialize=periods_list)
# Define parameters (as Pyomo Param or dictionaries)
# ... (parameter definitions)
model.run = pyo.Var(model.SOURCES, model.PERIODS, domain=pyo.Binary)
model.production = pyo.Var(model.SOURCES, model.PERIODS, domain=pyo.NonNegativeReals)
# Define constraints via rules
# ... (constraint definitions)
model.total_cost = pyo.Objective(rule=objective_rule, sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory("highs")
if solver is None:
    solver = pyo.SolverFactory("cbc")
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=True)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    total_cost = pyo.value(model.total_cost)
    solution_summary = {"status": results.solver.termination_condition.name,
                        "objective": total_cost}
    # Extract and verify variable values
    # ... (extraction and verification loops)
else:
    solution_summary = {"status": "failed", "termination_condition": results.solver.termination_condition.name}
```

### Common Pitfalls
- Not verifying `solver is None` after `SolverFactory`, which can lead to cryptic errors if the requested solver is not installed.
- Accessing variable values via `pyo.value()` before checking the termination condition, which may load invalid or stale values.
- Forgetting to handle the case where the solver finds a feasible but non-optimal solution; the extraction logic should still proceed.
