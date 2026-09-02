---
name: Generator Commitment and Dispatch
description: |
  Model and solve unit commitment problems with startup logic, capacity constraints, and cost minimization using mixed-integer linear programming.

---

# Workflow 1 (Pyomo with Gurobi)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's concrete model paradigm with explicit index sets and parameter dictionaries. It employs integer variables for discrete activation decisions and continuous variables for power output, linked via linear constraints to enforce operational limits and startup logic.

### Step 1 - Define Sets and Parameters
- Declare index sets for generators and time periods.
- Organize all cost coefficients and operational limits into parameter dictionaries (e.g., `base_cost`, `variable_cost`, `startup_cost`, `max_active`, `min_output`, `max_output`, `max_startups`).
- Define time-series parameters for system demand and reserve requirements.

### Step 2 - Design Decision Variables
- Create integer variables `num_active[g,t]` for the count of active units per generator type and period.
- Create continuous variables `power_output[g,t]` for the total power output per generator type and period.
- Create integer variables `num_startup[g,t]` for the count of units started per generator type and period.

### Step 3 - Formulate Objective Function
- Construct a minimizing objective summing three cost components across all generators and periods: base cost (`base_cost[g] * num_active[g,t]`), variable cost (`variable_cost[g] * power_output[g,t]`), and startup cost (`startup_cost[g] * num_startup[g,t]`).

### Step 4 - Implement Core Operational Constraints
- **Demand Satisfaction**: Sum of `power_output` across all generators for each period must meet or exceed the period's demand.
- **Reserve Requirement**: Sum of maximum possible output (`max_output[g] * num_active[g,t]`) across all generators for each period must meet or exceed the demand plus a reserve threshold.
- **Output Bounds**: For each generator and period, enforce `min_output[g] * num_active[g,t] <= power_output[g,t] <= max_output[g] * num_active[g,t]`.
- **Capacity Limit**: For each generator and period, enforce `num_active[g,t] <= max_active[g]`.

### Step 5 - Enforce Startup Logic
- For the initial period, enforce `num_startup[g,0] <= num_active[g,0]`.
- For subsequent periods, enforce `num_startup[g,t] <= num_active[g,t] - num_active[g,t-1]` and `num_startup[g,t] >= 0`.
- For generators where startups are prohibited, add equality constraint `num_startup[g,t] == 0`.

### Formulation Template
```json
{
  "sets": [
    "generators",
    "time_periods"
  ],
  "parameters": [
    "base_cost[g]",
    "variable_cost[g]",
    "startup_cost[g]",
    "max_active[g]",
    "min_output[g]",
    "max_output[g]",
    "max_startups[g]",
    "demand[t]",
    "reserve_requirement[t]"
  ],
  "decision_variables": [
    "num_active[g,t] (integer)",
    "power_output[g,t] (continuous)",
    "num_startup[g,t] (integer)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{g,t} base_cost[g]*num_active[g,t] + variable_cost[g]*power_output[g,t] + startup_cost[g]*num_startup[g,t]"
  },
  "constraints": [
    "demand_satisfaction[t]: sum_g power_output[g,t] >= demand[t]",
    "reserve_requirement[t]: sum_g max_output[g]*num_active[g,t] >= demand[t] + reserve_requirement[t]",
    "output_lower_bound[g,t]: power_output[g,t] >= min_output[g]*num_active[g,t]",
    "output_upper_bound[g,t]: power_output[g,t] <= max_output[g]*num_active[g,t]",
    "capacity_limit[g,t]: num_active[g,t] <= max_active[g]",
    "startup_initial[g]: num_startup[g,0] <= num_active[g,0]",
    "startup_subsequent[g,t]: num_startup[g,t] <= num_active[g,t] - num_active[g,t-1]",
    "startup_nonneg[g,t]: num_startup[g,t] >= 0",
    "no_startup_if_prohibited[g,t]: num_startup[g,t] == 0 (if max_startups[g]==0)"
  ]
}
```

### Common Pitfalls
- Using Pyomo reserved keywords (e.g., `active`) as variable or parameter names, causing syntax errors.
- Omitting the non-negativity constraint on the difference in the startup logic, which can lead to incorrect model behavior.
- Failing to handle edge cases like generators with zero allowed startups or initial conditions.

## Solving stage

### Strategy Overview
This stage configures the Gurobi solver via Pyomo's `SolverFactory`, sets performance and reproducibility options, rigorously checks the solution status, extracts and verifies results, and provides structured output for both success and failure cases.

### Step 1 - Configure Solver and Solve
- Instantiate the solver using `SolverFactory("gurobi")`.
- Set solver options such as time limit, MIP gap tolerance, thread count, and random seed for reproducibility.
- Call the solver's `solve` method on the model instance.

### Step 2 - Validate Solution Status
- Check that `solver.status == SolverStatus.ok`.
- Check that the model's termination condition is either `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If checks fail, proceed to error handling without extracting variable values.

### Step 3 - Extract and Verify Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Access variable values via their `.value` attribute.
- Optionally, implement post-solution verification logic to confirm key constraints (demand, reserve) are satisfied within a small tolerance.

### Step 4 - Format and Output Results
- For a successful solve, print the objective value in a parseable format (e.g., `RESULT:{objective_value}`).
- Output a detailed breakdown of the solution (active counts, outputs, startups per period) and cost decomposition for debugging.
- For infeasible or error cases, output a structured JSON payload containing the status, reason, solver status, and termination condition.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... (model construction code as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0001
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.obj)
    print(f"RESULT:{objective_value}")
    # ... extract and print detailed solution
else:
    error_payload = {
        "status": "error",
        "reason": "Solver did not return an optimal or feasible solution.",
        "solver_status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }
    print(json.dumps(error_payload))
```

### Common Pitfalls
- Trusting a non-zero return code or an `unknown` termination condition as a valid solution.
- Attempting to access `.value` attributes on variables before confirming a successful solve, which may raise exceptions.
- Outputting pseudo-numeric answers or partial results when the solver execution has failed.

# Workflow 2 (PuLP with CBC)

## Modeling stage

### Strategy Overview
This workflow uses PuLP's Pythonic API for rapid prototyping of MILP models. It employs binary variables for individual unit commitment decisions, aggregating them to model counts, and uses list comprehensions for concise constraint definition.

### Step 1 - Define Problem and Data Structures
- Instantiate a `pulp.LpProblem` with a name and sense (`LpMinimize`).
- Store cost coefficients and operational limits in Python dictionaries or lists indexed by generator and period.
- Define time-series data for demand and reserve as lists.

### Step 2 - Design Decision Variables
- Create binary variables `is_active[g,u,t]` for each individual unit `u` of generator type `g` in each period `t`.
- Create continuous variables `unit_output[g,u,t]` for the power output of each individual unit.
- Create binary variables `unit_startup[g,u,t]` for the startup decision of each individual unit.

### Step 3 - Formulate Objective Function
- Construct the objective by summing: base cost per active unit, variable cost per unit output, and startup cost per unit started, across all units, generators, and periods.

### Step 4 - Implement Aggregated Operational Constraints
- **Demand Satisfaction**: Sum of all `unit_output` variables for each period must meet or exceed demand.
- **Reserve Requirement**: Sum of `max_output[g] * is_active[g,u,t]` across all units for each period must meet demand plus reserve.
- **Output Bounds**: For each unit, enforce `min_output[g] * is_active[g,u,t] <= unit_output[g,u,t] <= max_output[g] * is_active[g,u,t]`.
- **Unit Count Limit**: For each generator type and period, the sum of `is_active` variables for its units must be less than or equal to `max_active[g]`.

### Step 5 - Enforce Per-Unit Startup Logic
- For the initial period, enforce `unit_startup[g,u,0] <= is_active[g,u,0]`.
- For subsequent periods, enforce `unit_startup[g,u,t] <= is_active[g,u,t] - is_active[g,u,t-1]`.
- Add non-negativity for startup variables.

### Formulation Template
```json
{
  "sets": [
    "generators",
    "units[g]",
    "time_periods"
  ],
  "parameters": [
    "base_cost[g]",
    "variable_cost[g]",
    "startup_cost[g]",
    "max_active[g]",
    "min_output[g]",
    "max_output[g]",
    "demand[t]",
    "reserve_requirement[t]"
  ],
  "decision_variables": [
    "is_active[g,u,t] (binary)",
    "unit_output[g,u,t] (continuous)",
    "unit_startup[g,u,t] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{g,u,t} base_cost[g]*is_active[g,u,t] + variable_cost[g]*unit_output[g,u,t] + startup_cost[g]*unit_startup[g,u,t]"
  },
  "constraints": [
    "demand_satisfaction[t]: sum_{g,u} unit_output[g,u,t] >= demand[t]",
    "reserve_requirement[t]: sum_{g,u} max_output[g]*is_active[g,u,t] >= demand[t] + reserve_requirement[t]",
    "output_lower_bound[g,u,t]: unit_output[g,u,t] >= min_output[g]*is_active[g,u,t]",
    "output_upper_bound[g,u,t]: unit_output[g,u,t] <= max_output[g]*is_active[g,u,t]",
    "capacity_limit[g,t]: sum_{u in units[g]} is_active[g,u,t] <= max_active[g]",
    "startup_initial[g,u]: unit_startup[g,u,0] <= is_active[g,u,0]",
    "startup_subsequent[g,u,t]: unit_startup[g,u,t] <= is_active[g,u,t] - is_active[g,u,t-1]",
    "startup_nonneg[g,u,t]: unit_startup[g,u,t] >= 0"
  ]
}
```

### Common Pitfalls
- Creating an excessively large number of binary variables if unit counts are very high, impacting solve time.
- Incorrectly aggregating unit-level variables in constraints (e.g., confusing generator-level and unit-level indices).
- Forgetting to enforce the binary nature of startup variables in the per-unit formulation.

## Solving stage

### Strategy Overview
This stage uses PuLP's default CBC solver or an installed alternative. It focuses on extracting solution information directly from PuLP's variable objects, providing basic status checks, and generating a clear solution summary.

### Step 1 - Solve the Problem
- Call the `solve()` method on the `pulp.LpProblem` instance. PuLP will use the default solver (CBC) unless specified otherwise.
- Optionally, pass solver-specific options via the `solve` method if using a different solver like GLPK.

### Step 2 - Check Solution Status
- Check the problem's status attribute (`LpStatus`) for `'Optimal'` or `'Feasible'`.
- Do not proceed with value extraction if the status is `'Infeasible'`, `'Unbounded'`, or `'Not Solved'`.

### Step 3 - Extract Solution Values
- Access the objective value via `pulp.value(problem.objective)`.
- Iterate through the problem's variables and retrieve their `varValue` attribute.
- Aggregate unit-level results to generator-level totals for reporting.

### Step 4 - Generate Output
- Print the objective value in a consistent format.
- Output a summary table showing aggregated active units, total output, and startup counts per generator type and period.
- For unsuccessful solves, print the problem status and avoid outputting numerical results.

### Code Usage
```python
import pulp

# build model from formulation
prob = pulp.LpProblem('Generator_Commitment', pulp.LpMinimize)
# ... (model construction code as per Modeling Stage)

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(msg=False, timeLimit=30) # Optional: use and configure CBC
prob.solve(solver)

status = pulp.LpStatus[prob.status]
if status in ['Optimal', 'Feasible']:
    objective_value = pulp.value(prob.objective)
    print(f"RESULT:{objective_value}")
    # ... iterate through variables, aggregate, and print summary
else:
    print(f"STATUS:{status}")
    # Do not output variable values
```

### Common Pitfalls
- Assuming the solve was successful without checking `LpStatus`, leading to errors when accessing `varValue`.
- Outputting variable values from an infeasible model, which may be `None` or misleading.
- Neglecting to set a time limit or other solver options, potentially resulting in very long run times for large instances.
