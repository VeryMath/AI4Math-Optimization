---
name: MultiCommodityFlowOptimization
description: |
  Model multi-commodity flow problems with shared arc capacities and solve them using linear programming, with robust status checking and solution validation.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a multi-commodity flow network using Pyomo's declarative modeling. Define separate sets for origins, destinations, and commodities, with three-dimensional flow variables. Use linear equality constraints for supply and demand, and linear inequality constraints for shared arc capacities.

### Step 1 - Define Sets and Data Structure
- Define three index sets: `ORIGINS`, `DESTINATIONS`, `COMMODITIES`.
- Organize parameters as dictionaries with tuple keys: `supply[(i,k)]`, `demand[(j,k)]`, `cost[(i,j,k)]`, `capacity[(i,j)]`.

### Step 2 - Declare Decision Variables
- Create a continuous, non-negative variable `model.x[i, j, k]` representing the flow quantity of commodity `k` from origin `i` to destination `j`.
- Use `domain=pyo.NonNegativeReals`.

### Step 3 - Formulate Supply and Demand Constraints
- For each origin `i` and commodity `k`: `sum(model.x[i, j, k] for j in DESTINATIONS) == supply[i, k]`.
- For each destination `j` and commodity `k`: `sum(model.x[i, j, k] for i in ORIGINS) == demand[j, k]`.

### Step 4 - Formulate Arc Capacity Constraints
- For each origin-destination pair `(i, j)`: `sum(model.x[i, j, k] for k in COMMODITIES) <= capacity[i, j]`.

### Step 5 - Define Linear Cost Objective
- Minimize total cost: `model.obj = pyo.Objective(expr=sum(cost[i, j, k] * model.x[i, j, k] for i, j, k), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["ORIGINS", "DESTINATIONS", "COMMODITIES"],
  "parameters": [
    "supply[ORIGINS, COMMODITIES]",
    "demand[DESTINATIONS, COMMODITIES]",
    "cost[ORIGINS, DESTINATIONS, COMMODITIES]",
    "capacity[ORIGINS, DESTINATIONS]"
  ],
  "decision_variables": ["x[ORIGINS, DESTINATIONS, COMMODITIES] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j,k] * x[i,j,k])"
  },
  "constraints": [
    "supply_con[i,k]: sum_j x[i,j,k] == supply[i,k]",
    "demand_con[j,k]: sum_i x[i,j,k] == demand[j,k]",
    "capacity_con[i,j]: sum_k x[i,j,k] <= capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Assuming total supply-demand balance guarantees feasibility; arc capacity constraints can still cause infeasibility.
- Not verifying that parameter dictionaries are correctly indexed, leading to `KeyError` during constraint construction.
- Using overly complex constraint rules that obscure the linear structure; keep rules simple and direct.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP solver (HiGHS or CBC). Configure solver options for performance and determinism, then rigorously check solver status and termination condition before extracting results. Implement post-solution verification.

### Step 1 - Instantiate and Configure Solver
- Create solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set options: `solver.options["time_limit"] = 30`, `solver.options["mip_rel_gap"] = 0.0`.

### Step 2 - Solve and Check Status
- Execute: `results = solver.solve(model, tee=False)`.
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Validate Solution
- Extract objective value: `obj_val = float(pyo.value(model.obj))`.
- Optionally, iterate over variables to collect non-zero flows (`if pyo.value(model.x[i,j,k]) > 1e-6`).
- Programmatically verify all constraints by recomputing sums and comparing to limits with a tolerance (e.g., `1e-6`).

### Step 4 - Output Structured Results
- Output the objective value in a parseable format: `print(f"RESULT:{obj_val}")`.
- For detailed output, package results (status, objective, non-zero flows) into a JSON string.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation (sets, variables, constraints, objective as defined above)
model = pyo.ConcreteModel()
# ... model construction code ...

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 30
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    obj_val = float(pyo.value(model.obj))
    print(f"RESULT:{obj_val}")
    # Optional verification and detailed output
else:
    print("ERROR:Solver failed or no feasible solution found.")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to errors when extracting values from infeasible or failed solves.
- Setting solver options that conflict with the solver's environment (e.g., `threads` when already initialized).
- Interpreting solver errors generically; examine specific error messages for diagnostics like infeasibility.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
Model the multi-commodity flow problem using OR-Tools' linear solver wrapper. Build the model imperatively by creating variables and adding constraints directly. Use nested loops for systematic construction, leveraging OR-Tools' efficient coefficient setting.

### Step 1 - Initialize Solver and Data Structures
- Create solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Organize data as nested dictionaries or lists: `supply[i][k]`, `demand[j][k]`, `cost[i][j][k]`, `capacity[i][j]`.

### Step 2 - Create Flow Variables
- Use nested loops over origins, destinations, commodities to create variables: `x[i][j][k] = solver.NumVar(0, solver.infinity(), f'x_{i}_{j}_{k}')`.

### Step 3 - Add Supply and Demand Constraints
- For each origin `i` and commodity `k`: `solver.Add(sum(x[i][j][k] for j in destinations) == supply[i][k])`.
- For each destination `j` and commodity `k`: `solver.Add(sum(x[i][j][k] for i in origins) == demand[j][k])`.

### Step 4 - Add Arc Capacity Constraints
- For each origin-destination pair `(i, j)`: `solver.Add(sum(x[i][j][k] for k in commodities) <= capacity[i][j])`.

### Step 5 - Set Linear Cost Objective
- Create objective: `objective = solver.Objective()`.
- In nested loops, set coefficients: `objective.SetCoefficient(x[i][j][k], cost[i][j][k])`.
- Call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "commodities"],
  "parameters": [
    "supply[origins][commodities]",
    "demand[destinations][commodities]",
    "cost[origins][destinations][commodities]",
    "capacity[origins][destinations]"
  ],
  "decision_variables": ["x[origins][destinations][commodities] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j][k] * x[i][j][k])"
  },
  "constraints": [
    "supply: for each i,k: sum_j x[i][j][k] == supply[i][k]",
    "demand: for each j,k: sum_i x[i][j][k] == demand[j][k]",
    "capacity: for each i,j: sum_k x[i][j][k] <= capacity[i][j]"
  ]
}
```

### Common Pitfalls
- Using `solver.infinity()` for variable upper bounds when capacities are already constrained; it's acceptable but less explicit.
- Building constraints inefficiently with repeated `solver.Add()` inside deep loops; pre-aggregate expressions where possible.
- Not using descriptive variable names, making debugging difficult for larger instances.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' GLOP solver for linear programming. After solving, verify solution feasibility by checking all constraints against the variable values. Output results in a structured format suitable for automation.

### Step 1 - Execute Solve
- Call `solver.Solve()`.
- Check status: `status = solver.Solve()`.

### Step 2 - Validate Solution Status
- Verify `status == pywraplp.Solver.OPTIMAL` (or `FEASIBLE` for non-optimal but feasible solutions).
- If not optimal/feasible, report infeasibility and avoid extracting values.

### Step 3 - Extract and Verify Solution
- Extract objective value: `obj_val = objective.Value()`.
- For verification, compute actual flows: `flow_val = x[i][j][k].solution_value()`.
- Recalculate supply usage, demand satisfaction, and capacity usage, comparing to limits with a tolerance (e.g., `1e-6`).

### Step 4 - Output Results
- Output the objective value: `print(f"RESULT:{obj_val}")`.
- Optionally, output a JSON payload with non-zero flows and verification details.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... variable and constraint creation ...

# Solve with status / termination checks
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    obj_val = solver.Objective().Value()
    print(f"RESULT:{obj_val}")
    # Optional verification
    for i in origins:
        for k in commodities:
            used = sum(x[i][j][k].solution_value() for j in destinations)
            if abs(used - supply[i][k]) > 1e-6:
                print(f"Warning: Supply violation for ({i},{k})")
else:
    print("ERROR:No optimal or feasible solution found.")
```

### Common Pitfalls
- Assuming `solver.Solve()` returns only `OPTIMAL`; also check for `FEASIBLE`.
- Not performing post-solution verification, potentially accepting numerically invalid solutions.
- Using the solver's default parameters for large problems; consider setting time limits if needed.
