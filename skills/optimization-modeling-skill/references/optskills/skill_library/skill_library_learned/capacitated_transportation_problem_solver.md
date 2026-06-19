---
name: Capacitated Transportation Problem Solver
description: |
  Model and solve balanced capacitated transportation problems with linear costs, supply/demand equality, and per-route capacity limits using continuous flow variables.
---

# Workflow 1 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a linear program using the OR-Tools wrapper for the GLOP solver. Variables are created with explicit upper bounds to embed capacity constraints, and equality constraints enforce exact supply and demand fulfillment.

### Step 1 - Define Data Structures
- Organize problem data into Python lists or dictionaries for supply, demand, cost, and capacity.
- Use zero-based indexing for sources (facilities) and destinations (centers).
- **Prerequisite check**: Verify that total supply equals total demand for a balanced problem. If not balanced, add a dummy source or destination with zero cost and infinite capacity before proceeding.

### Step 2 - Create Variables with Bounds
- Instantiate a `pywraplp.Solver` with the `"GLOP"` backend.
- Create a non-negative continuous variable `x[i][j]` for each source-destination pair.
- Set the variable's upper bound directly to `capacity[i][j]` during creation to enforce per-route limits.

### Step 3 - Add Supply and Demand Constraints
- For each source `i`, create a linear equality constraint: `sum_j x[i][j] = supply[i]`.
- For each destination `j`, create a linear equality constraint: `sum_i x[i][j] = demand[j]`.
- Use `solver.Constraint(value, value)` to set both lower and upper bounds to the same value.

### Step 4 - Define Linear Objective
- Create the objective function: `minimize sum_i sum_j cost[i][j] * x[i][j]`.
- Set coefficients for each variable using `objective.SetCoefficient(x[i][j], cost[i][j])`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations"
  ],
  "parameters": [
    "supply[sources]",
    "demand[destinations]",
    "cost[sources][destinations]",
    "capacity[sources][destinations]"
  ],
  "decision_variables": [
    "flow[sources][destinations] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in sources, j in destinations} cost[i][j] * flow[i][j]"
  },
  "constraints": [
    "supply_constraint[i in sources]: sum_{j in destinations} flow[i][j] = supply[i]",
    "demand_constraint[j in destinations]: sum_{i in sources} flow[i][j] = demand[j]",
    "capacity_constraint[i in sources, j in destinations]: flow[i][j] <= capacity[i][j]"
  ]
}
```

### Common Pitfalls
- Forgetting to check for problem balance (total supply vs. total demand) before building the model, which leads to infeasibility.
- Setting variable upper bounds to `infinity` instead of the specific `capacity[i][j]`, which omits the per-route limit.
- Not verifying the solver status (`OPTIMAL` or `FEASIBLE`) before extracting solution values.

## Solving stage

### Strategy Overview
Solve the linear program using the GLOP solver, check termination status, and extract the solution. Implement post-solve verification to ensure constraints are satisfied within a numerical tolerance.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()` and capture the status.
- Check if the status is `solver.OPTIMAL` or `solver.FEASIBLE`. If not, log the solver status code and exit.

### Step 2 - Extract and Verify Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- Iterate through all variables to get flow values `x[i][j].solution_value()`.
- **Post-solve verification**: Recompute aggregate flows for each source and destination to verify supply/demand constraints are met within a tolerance (e.g., 1e-6). Also verify no variable exceeds its upper bound.

### Step 3 - Report Results
- Print the objective value in a parseable format (e.g., `RESULT:{objective_value}`).
- For debugging, log a summary of non-zero flows (values > 1e-6) and their utilization relative to capacity.

### Code Usage
```python
# build model from formulation
import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver("GLOP")
if not solver:
    raise RuntimeError("Solver not available.")

# 2. Define data (placeholders)
num_sources = len(supply)
num_dests = len(demand)
# supply = [...]; demand = [...]; cost = [[...]]; capacity = [[...]]

# 3. Create variables with capacity bounds
x = {}
for i in range(num_sources):
    for j in range(num_dests):
        x[i, j] = solver.NumVar(0, capacity[i][j], f'flow_{i}_{j}')

# 4. Add supply constraints
for i in range(num_sources):
    ct = solver.Constraint(supply[i], supply[i])
    for j in range(num_dests):
        ct.SetCoefficient(x[i, j], 1)

# 5. Add demand constraints
for j in range(num_dests):
    ct = solver.Constraint(demand[j], demand[j])
    for i in range(num_sources):
        ct.SetCoefficient(x[i, j], 1)

# 6. Set objective
objective = solver.Objective()
for i in range(num_sources):
    for j in range(num_dests):
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f"RESULT:{objective.Value()}")
    # Optional verification
    for i in range(num_sources):
        total = sum(x[i, j].solution_value() for j in range(num_dests))
        if abs(total - supply[i]) > 1e-6:
            print(f"Warning: supply mismatch for source {i}")
    for j in range(num_dests):
        total = sum(x[i, j].solution_value() for i in range(num_sources))
        if abs(total - demand[j]) > 1e-6:
            print(f"Warning: demand mismatch for destination {j}")
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status.
- Not handling numerical precision issues when verifying constraint satisfaction.
- Using `solver.INFINITY` as an upper bound, which can hide modeling errors if capacity data is missing.

# Workflow 2 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's concrete modeling environment. Define sets, parameters, variables, and constraints declaratively. This approach separates the model formulation from the solver interface, enabling easy solver swapping.

### Step 1 - Define Sets and Parameters
- Create Pyomo `Set` objects for sources and destinations.
- Define `Param` objects for supply, demand, cost, and capacity, indexed over the appropriate sets.
- Use dictionaries to initialize parameter data.
- **Prerequisite check**: Verify total supply equals total demand before building the model instance. If unbalanced, add a dummy source or destination with zero cost and infinite capacity.

### Step 2 - Declare Decision Variables
- Create a `Var` object `model.flow` indexed over the Cartesian product of source and destination sets.
- Specify the domain as `pyo.NonNegativeReals` for continuous, non-negative flows.

### Step 3 - Construct Constraints via Rules
- Define a rule function for the supply constraint that returns `sum(model.flow[i, j] for j in destinations) == supply[i]`.
- Define a rule function for the demand constraint that returns `sum(model.flow[i, j] for i in sources) == demand[j]`.
- Define a rule function for the capacity constraint that returns `model.flow[i, j] <= capacity[i, j]`.

### Step 4 - Formulate the Objective
- Define the objective function as `sum(cost[i, j] * model.flow[i, j] for i in sources for j in destinations)`.
- Set the sense to `minimize`.

### Formulation Template
```json
{
  "sets": [
    "sources",
    "destinations"
  ],
  "parameters": [
    "supply[sources]",
    "demand[destinations]",
    "cost[sources, destinations]",
    "capacity[sources, destinations]"
  ],
  "decision_variables": [
    "flow[sources, destinations] in NonNegativeReals"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in sources, j in destinations} cost[i,j] * flow[i,j]"
  },
  "constraints": [
    "supply_rule(i): sum_{j in destinations} flow[i,j] == supply[i]",
    "demand_rule(j): sum_{i in sources} flow[i,j] == demand[j]",
    "capacity_rule(i,j): flow[i,j] <= capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing parameters in constraint rules, leading to `KeyError`.
- Forgetting to initialize all parameters before creating the model instance, resulting in uninitialized data errors.
- Using mutable default arguments (like lists) in Pyomo rule functions.

## Solving stage

### Strategy Overview
Instantiate a solver (HiGHS or CBC) via Pyomo's `SolverFactory`, configure it with performance options, solve the model, and rigorously check the termination condition before extracting results.

### Step 1 - Configure and Execute Solver
- Create a solver object: `solver = SolverFactory('highs')` (or `'cbc'`).
- Set solver options such as time limit (`time_limit`), optimality gap (`mip_rel_gap` for MIPs), and thread count (`threads`).
- Call `results = solver.solve(model, tee=False)` to solve silently, or `tee=True` for log output.

### Step 2 - Validate Termination Status
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `...feasible`.
- If status is not acceptable, log the termination condition and investigate infeasibility (e.g., re-verify problem balance and data correctness).

### Step 3 - Extract and Verify Solution
- Retrieve the objective value: `pyo.value(model.obj)`.
- Access variable values: `pyo.value(model.flow[i, j])`.
- **Post-solve verification**: Recompute constraint left-hand sides and compare to parameters with a tolerance (e.g., 1e-6). Verify no variable exceeds its capacity bound.

### Step 4 - Output Structured Results
- Print the objective value in a consistent format (e.g., `RESULT:{objective_value}`).
- Optionally, generate a report of the solution, listing non-zero flows and constraint slack.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Create a ConcreteModel
model = pyo.ConcreteModel()

# 2. Define sets (placeholders)
model.sources = pyo.Set(initialize=range(num_sources))
model.dests = pyo.Set(initialize=range(num_dests))

# 3. Define parameters (initialize with your data)
model.supply = pyo.Param(model.sources, initialize=supply_dict)
model.demand = pyo.Param(model.dests, initialize=demand_dict)
model.cost = pyo.Param(model.sources, model.dests, initialize=cost_dict)
model.capacity = pyo.Param(model.sources, model.dests, initialize=capacity_dict)

# 4. Define variables
model.flow = pyo.Var(model.sources, model.dests, domain=pyo.NonNegativeReals)

# 5. Define objective
def obj_rule(m):
    return sum(m.cost[i, j] * m.flow[i, j] for i in m.sources for j in m.dests)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# 6. Define constraints
def supply_rule(m, i):
    return sum(m.flow[i, j] for j in m.dests) == m.supply[i]
model.supply_con = pyo.Constraint(model.sources, rule=supply_rule)

def demand_rule(m, j):
    return sum(m.flow[i, j] for i in m.sources) == m.demand[j]
model.demand_con = pyo.Constraint(model.dests, rule=demand_rule)

def capacity_rule(m, i, j):
    return m.flow[i, j] <= m.capacity[i, j]
model.capacity_con = pyo.Constraint(model.sources, model.dests, rule=capacity_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    print(f"RESULT:{pyo.value(model.obj)}")
    # Optional verification loop
    for i in model.sources:
        total = sum(pyo.value(model.flow[i, j]) for j in model.dests)
        if abs(total - pyo.value(model.supply[i])) > 1e-6:
            print(f"Verification warning for source {i}")
    for j in model.dests:
        total = sum(pyo.value(model.flow[i, j]) for i in model.sources)
        if abs(total - pyo.value(model.demand[j])) > 1e-6:
            print(f"Verification warning for destination {j}")
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` with `TerminationCondition`; both must be checked.
- Not setting the `sense` on the objective, defaulting to minimization.
- Attempting to access variable values from an unsolved or infeasible model, causing `ValueError`.

## Fallback Strategy
- If `pywraplp` (OR-Tools) is unavailable, switch to Pyomo with HiGHS or CBC as demonstrated in Workflow 2.
- If the primary solver fails to find an optimal solution, verify the problem balance prerequisite and check for data errors (e.g., negative costs, zero capacities on required routes).
