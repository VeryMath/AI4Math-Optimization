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
- Define parameters using `pyo.Param()`: `fixed_cost[f]`, `capacity[f]`, `demand[c]`, and `shipping_cost[f, c]`. Store data in fully populated dictionaries for clean initialization.

### Step 2 - Declare Decision Variables
- Create binary variables `y[f]` for facility opening decisions using `domain=pyo.Binary`.
- Create continuous, non-negative variables `x[f, c]` for flow assignments using `domain=pyo.NonNegativeReals`.

### Step 3 - Formulate Objective Function
- Construct a linear objective to minimize total cost: `sum(fixed_cost[f] * y[f] for f in F) + sum(shipping_cost[f, c] * x[f, c] for f in F for c in C)`. Use `sense=pyo.minimize`.

### Step 4 - Implement Core Constraints
- **Demand satisfaction**: For each customer `c`, add `sum(x[f, c] for f in F) == demand[c]`.
- **Capacity linking**: For each facility `f`, add `sum(x[f, c] for c in C) <= capacity[f] * y[f]`. This enforces the logical link that flow is only possible from open facilities.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[f] * y[f] for f in facilities) + sum(shipping_cost[f,c] * x[f,c] for f in facilities for c in customers)"
  },
  "constraints": [
    "demand_satisfaction[c]: sum(x[f,c] for f in facilities) == demand[c] for each c in customers",
    "capacity_link[f]: sum(x[f,c] for c in customers) <= capacity[f] * y[f] for each f in facilities"
  ]
}
```

### Common Pitfalls
- Ensure parameter dictionaries are fully populated for all set indices to avoid `KeyError`.
- Use a single iterable in `sum()` expressions (e.g., `sum(x[f,c] for f in F for c in C)`).
- Maintain consistent index order between variables and parameters in constraints.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver, with explicit checks for solution status and careful loading of results to ensure robustness.

### Step 1 - Configure and Instantiate Solver
- Instantiate the solver via `SolverFactory('solver_name')` (e.g., `'highs'` or `'cbc'`).
- Set performance options: `time_limit`, `mip_rel_gap` (or `ratio`), and `threads`. For reproducibility, set a random seed if supported.

### Step 2 - Solve with Status Control
- Execute the solve command with `load_solutions=False` to prevent automatic loading.
- Capture the results object for status checking.

### Step 3 - Check Termination Status and Load Solution
- Verify the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- Only if the status is acceptable, load the solution into the model using `model.solutions.load_from(results)`.

### Step 4 - Extract and Validate Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate over binary variables with a tolerance (e.g., `> 0.5`) to identify opened facilities.
- Compute derived metrics (total flow per facility, cost breakdown) and validate against original constraints (demand satisfaction, capacity limits) within a numerical tolerance (e.g., `1e-6`).
- **Perform forced-facility analysis for validation**: To verify optimality, solve restricted models with specific facilities forced open (e.g., `model.y[f].fix(1)`) to compare alternative configurations and confirm the solution is indeed optimal among candidate combinations.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverFactory, SolverStatus, TerminationCondition

# 1. Build Model (ConcreteModel, Sets, Vars, Objective, Constraints)
# ... model definition as per Modeling Stage ...

# 2. Instantiate Solver & Set Options
solver = SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
solver.options['mip_rel_gap'] = [MIP_GAP]

# 3. Solve with status control
results = solver.solve(model, tee=False, load_solutions=False)

# 4. Check Status & Termination
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)  # Load only after status check
    objective_value = float(pyo.value(model.obj))
    # 5. Extract solution...
    opened_facilities = [f for f in model.F if pyo.value(model.y[f]) > 0.5]
    # ... further processing and validation
else:
    # Handle non-optimal/infeasible case
    print(f"Solver failed: Status={status}, Termination={term}")
```

### Common Pitfalls
- Loading solutions automatically (`load_solutions=True`) without checking status first can cause errors if no feasible solution was found.
- `feasible` is acceptable for a usable solution, but `optimal` guarantees optimality.
- Use a tolerance when checking binary variable values to account for floating-point precision.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
Use Google's OR-Tools `pywraplp` API for a direct, imperative model build. Suited for rapid prototyping and lightweight, programmatic modeling.

### Step 1 - Initialize Solver and Define Variable Scope
- Create a solver instance using `pywraplp.Solver.CreateSolver("SCIP")` or `"CBC"`.
- Define the index sets for facilities and customers as lists.

### Step 2 - Create Decision Variables
- Create binary variables for facility opening: `y[i] = solver.IntVar(0, 1, name)`.
- Create continuous flow variables: `x[i, j] = solver.NumVar(0, solver.infinity(), name)`.

### Step 3 - Build Objective Function Term-by-Term
- Instantiate the objective with `solver.Objective()`.
- Add the fixed cost terms: `objective.SetCoefficient(y[i], fixed_cost[i])`.
- Add the transportation cost terms: `objective.SetCoefficient(x[i, j], shipping_cost[i][j])`.
- Set the optimization sense to minimization with `objective.SetMinimization()`.

### Step 4 - Add Constraints Directly
- For each customer, add a demand satisfaction constraint: `solver.Add(sum(x[i, j] for i in facilities) == demand[j])`.
- For each facility, add the capacity linking constraint: `solver.Add(sum(x[i, j] for j in customers) <= capacity[i] * y[i])`.

### Formulation Template
```json
{
  "sets": ["facilities", "customers"],
  "parameters": ["fixed_cost[facilities]", "capacity[facilities]", "demand[customers]", "shipping_cost[facilities, customers]"],
  "decision_variables": ["y[facilities] ∈ {0,1}", "x[facilities, customers] ≥ 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(fixed_cost[i] * y[i] for i in facilities) + sum(shipping_cost[i][j] * x[i,j] for i in facilities for j in customers)"
  },
  "constraints": [
    "demand_satisfaction[j]: sum(x[i,j] for i in facilities) == demand[j] for each j in customers",
    "capacity_link[i]: sum(x[i,j] for j in customers) <= capacity[i] * y[i] for each i in facilities"
  ]
}
```

### Common Pitfalls
- Ensure the capacity linking constraint is added as `sum(x) <= capacity * y` with correct coefficient signs.
- Building the objective by looping over parameters must include all variable-coefficient pairs.

## Solving stage

### Strategy Overview
Execute the solver, handle its status codes, and extract solution values directly from the OR-Tools variable objects. Emphasizes straightforward solution retrieval and verification.

### Step 1 - Configure Solver Settings
- Set a time limit using `solver.SetTimeLimit(milliseconds)`.
- Control parallelism with `solver.SetNumThreads(number)`.
- (Optional) Set solver-specific parameters via `solver.SetSolverSpecificParametersAsString`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check if the status is `solver.OPTIMAL` or `solver.FEASIBLE`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) appropriately.

### Step 3 - Extract Solution Values
- If the status is acceptable, obtain the objective value via `objective.Value()`.
- Determine opened facilities by checking `y[i].solution_value() > 0.5`.
- Retrieve flow quantities using `x[i, j].solution_value()`.

### Step 4 - Post-Solve Validation
- Programmatically verify constraint satisfaction: recompute total flow to each customer and per facility, comparing against demand and capacity within a small tolerance (e.g., `1e-6`).
- Calculate a manual objective value from the extracted solution and compare it to the solver's reported value to catch potential inconsistencies.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Initialize Solver
solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit([TIME_LIMIT_MS])
solver.SetNumThreads([NUM_THREADS])

# 2. Build Model (Variables, Objective, Constraints)
# ... model definition as per Modeling Stage ...

# 3. Solve and check status
status = solver.Solve()

# 4. Extract results if feasible/optimal
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = solver.Objective().Value()
    opened_facilities = [i for i in facilities if y[i].solution_value() > 0.5]
    flow_assignments = {(i, j): x[i, j].solution_value() for i in facilities for j in customers if x[i, j].solution_value() > 1e-6}
    # 5. Optional validation
    # ...
else:
    print(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- `solver.FEASIBLE` provides a valid solution but without optimality guarantee.
- Use a tolerance when checking continuous flow values for positivity to avoid reporting near-zero flows.
- OR-Tools `SetTimeLimit` uses milliseconds, not seconds.
