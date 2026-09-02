---
name: Capacitated Facility Location MILP
description: |
  Model and solve capacitated facility location problems with fixed opening costs and linear transportation costs using mixed-integer linear programming (MILP), with robust solver integration and solution validation.

---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's abstract modeling to define a MILP formulation, separating model logic from data. Designed for clarity, maintainability, and compatibility with open-source solvers like HiGHS and CBC.

### Step 1 - Define Model Sets and Parameters
- Declare sets for facilities (`F`) and customers (`C`) using `pyo.Set()`.
- Define parameters `fixed_cost[f]`, `capacity[f]`, `demand[c]`, and `shipping_cost[f,c]` using `pyo.Param()`.
- **Verify data consistency**: Ensure total demand does not exceed total available capacity (`sum(capacity[f] for f in F)`) to avoid trivially infeasible models.
- **Ensure consistent indexing**: If cost data is provided in (customer, facility) format, transpose it to (facility, customer) for modeling convenience.

### Step 2 - Declare Decision Variables
- Create binary variables `y[f]` for facility opening (`domain=pyo.Binary`).
- Create binary variables `x[f, c]` for customer assignment (`domain=pyo.Binary`). This enforces single-sourcing.

### Step 3 - Formulate Objective Function
- Construct a linear objective to minimize total cost: `sum(fixed_cost[f] * y[f] for f in F) + sum(shipping_cost[f,c] * x[f,c] for f in F for c in C)`.
- Set `sense=pyo.minimize`.

### Step 4 - Implement Core Constraints
- **Demand satisfaction**: For each customer `c`, `sum(x[f, c] for f in F) == 1`.
- **Capacity linking**: For each facility `f`, `sum(demand[c] * x[f, c] for c in C) <= capacity[f] * y[f]`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * y[f] for f in facilities) + sum(shipping_cost[f,c] * x[f,c] for f in facilities for c in customers)"
  },
  "constraints": [
    "demand_satisfaction[c]: sum(x[f,c] for f in facilities) == 1 for each c in customers",
    "capacity_link[f]: sum(demand[c] * x[f,c] for c in customers) <= capacity[f] * y[f] for each f in facilities"
  ]
}
```

### Common Pitfalls
- Incomplete parameter initialization causing `KeyError`. Ensure dictionaries are fully populated for all set indices.
- Incorrect `sum()` usage; pass a single iterable (e.g., `sum(x[f,c] for f in F for c in C)`).
- Mis-specifying the capacity linking constraint; ensure it is `demand[c] * x[f,c]`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver, with explicit checks for solution status and careful loading of results to ensure robustness.

### Step 1 - Configure and Instantiate Solver
- Instantiate the solver via `SolverFactory('solver_name')` (e.g., `'highs'` or `'cbc'`).
- Set performance options: `time_limit=[TIME_LIMIT]`, `mip_rel_gap=0.0` for exact solution, and `threads`.
- **Enable solver output for debugging**: Set `tee=True` to view branch-and-bound progress.

### Step 2 - Solve with Status Control
- Execute the solve command with `load_solutions=False` to prevent automatic loading.
- Capture the results object for status checking.

### Step 3 - Check Termination Status and Load Solution
- Verify the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- Only if the status is acceptable, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- **Handle floating-point precision**: If all input costs are integers, round the solver's objective value to the nearest integer or recompute the exact cost using the integer solution values.
- Identify opened facilities by checking `y[f].value > 0.5` (with tolerance).
- **Implement solution verification**:
  1. Verify each customer is assigned to exactly one facility: `sum(x[f,c].value for f in F) == 1` for all `c`.
  2. Verify capacity constraints: For each facility `f`, compute `assigned = sum(demand[c] * x[f,c].value for c in C)` and check `assigned <= capacity[f] * y[f].value + 1e-6`.
- **Calculate cost breakdown manually**: Recompute fixed costs and shipping costs from variable values to validate the reported objective.
- **Extract and report the solution**: List opened facilities and the assignment of each customer, along with capacity utilization percentages.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# 1. Build Model (ConcreteModel, Sets, Vars, Objective, Constraints)
# ... model definition as per Modeling Stage ...

# 2. Instantiate Solver & Set Options
solver = SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
solver.options['mip_rel_gap'] = 0.0

# 3. Solve with status control
results = solver.solve(model, tee=True, load_solutions=False)

# 4. Check Status & Termination
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)  # Load only after status check
    objective_value = float(pyo.value(model.obj))
    # 5. Extract and validate solution
    opened_facilities = [f for f in model.F if pyo.value(model.y[f]) > 0.5]
    # ... further processing and validation ...
else:
    # Handle non-optimal/infeasible case
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking status first.
- Misinterpreting termination condition; `feasible` is acceptable for a usable solution.
- Not using a tolerance when checking binary variable values.
- Forgetting to multiply by `demand[c]` in the capacity verification step.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
Use Google's OR-Tools `pywraplp` API for a direct, imperative model build. Suited for rapid prototyping and lightweight modeling.

### Step 1 - Initialize Solver and Define Variable Scope
- Create a solver instance using `pywraplp.Solver.CreateSolver("SCIP")` or `"CBC"`.
- Define index sets for facilities (`F`) and customers (`C`) as lists.

### Step 2 - Create Decision Variables
- Create binary variables for facility opening: `y[i] = solver.IntVar(0, 1, name)`.
- Create binary assignment variables: `x[i, j] = solver.IntVar(0, 1, name)`.

### Step 3 - Build Objective Function Term-by-Term
- Instantiate the objective with `solver.Objective()`.
- Add fixed cost terms: `objective.SetCoefficient(y[i], fixed_cost[i])`.
- Add transportation cost terms: `objective.SetCoefficient(x[i, j], shipping_cost[i][j])`.
- Set the optimization sense to minimization with `objective.SetMinimization()`.

### Step 4 - Add Constraints Directly
- For each customer `j`, add a demand satisfaction constraint: `solver.Add(sum(x[i, j] for i in F) == 1)`.
- For each facility `i`, add the capacity linking constraint: `solver.Add(sum(demand[j] * x[i, j] for j in C) <= capacity[i] * y[i])`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(shipping_cost[i][j] * x[i,j] for i in facilities for j in customers)"
  },
  "constraints": [
    "demand_satisfaction[j]: sum(x[i,j] for i in facilities) == 1 for each j in customers",
    "capacity_link[i]: sum(demand[j] * x[i,j] for j in customers) <= capacity[i] * y[i] for each i in facilities"
  ]
}
```

### Common Pitfalls
- Incorrectly building the capacity linking constraint; ensure it is `sum(demand[j] * x[i,j]) <= capacity[i] * y[i]`.
- Using `solver.infinity()` for binary variable bounds; use `IntVar(0, 1)`.
- Omitting variable-coefficient pairs in the objective, leading to an incorrect total cost.

## Solving stage

### Strategy Overview
Execute the solver, handle its status codes, and extract solution values directly from the OR-Tools variable objects.

### Step 1 - Configure Solver Settings
- Set a time limit using `solver.SetTimeLimit([TIME_LIMIT_MS])`.
- Control parallelism with `solver.SetNumThreads([NUMBER])`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check if the status is `solver.OPTIMAL` or `solver.FEASIBLE`. Handle other statuses appropriately.

### Step 3 - Extract Solution Values
- If the status is acceptable, obtain the objective value via `solver.Objective().Value()`.
- **Handle floating-point precision**: If all input costs are integers, round the objective value to the nearest integer or recompute the exact cost using the integer solution values.
- Determine opened facilities by checking `y[i].solution_value() > 0.5`.
- Retrieve assignment decisions using `x[i, j].solution_value()`.

### Step 4 - Post-Solve Validation
- **Implement solution verification**:
  1. Verify each customer is assigned to exactly one facility.
  2. For each facility `i`, compute `assigned = sum(demand[j] * x[i,j].solution_value() for j in C)` and check `assigned <= capacity[i] * y[i].solution_value() + 1e-6`.
- **Calculate cost breakdown manually**: Recompute fixed and shipping costs from extracted variable values to validate the solver's reported objective.
- **Extract and report the solution**: List opened facilities and the assignment of each customer, along with capacity utilization percentages.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize Solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit([TIME_LIMIT_MS])
solver.SetNumThreads(4)

# 2. Build Model (Variables, Objective, Constraints)
# ... model definition as per Modeling Stage ...

# 3. Solve and check status
status = solver.Solve()

# 4. Extract results if feasible/optimal
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    opened_facilities = [i for i in F if y[i].solution_value() > 0.5]
    assignments = {(i, j): x[i, j].solution_value() for i in F for j in C if x[i, j].solution_value() > 0.5}
    # 5. Optional validation
    # ...
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Confusing `solver.OPTIMAL` with `solver.FEASIBLE`; the latter provides a valid solution without optimality guarantee.
- Not using a tolerance when checking binary variable values.
- Assuming the solver's internal time limit units are seconds; OR-Tools uses milliseconds.
- Forgetting to multiply by `demand[j]` in the capacity verification step.
