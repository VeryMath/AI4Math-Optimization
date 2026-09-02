---
name: Bipartite Flow Allocation with Capacity
description: |
  Model and solve bipartite resource allocation problems with supply-demand balance, individual capacity limits, and linear costs using linear programming.

---
# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a structured linear program. It is ideal for problems where data is cleanly separated from model logic, enabling easy modification and reuse.

### Step 1 - Define Sets and Parameters
- Define two distinct sets: `sources` (e.g., employees, factories) and `destinations` (e.g., projects, warehouses).
- Load or define parameter dictionaries for `supply`, `demand`, `capacity`, and `cost`, ensuring they are indexed appropriately by source, destination, or both.

### Step 2 - Instantiate Model and Variables
- Instantiate a `ConcreteModel`.
- Define a continuous, non-negative decision variable `x[i, j]` for the flow from source `i` to destination `j`.

### Step 3 - Formulate Objective and Constraints
- Formulate a linear objective to minimize total cost: `sum(cost[i,j] * x[i,j] for i in sources for j in destinations)`.
- Add supply constraints: total outflow from each source must equal its supply.
- Add demand constraints: total inflow to each destination must equal its demand.
- Add capacity constraints: each individual flow `x[i,j]` must not exceed its upper bound.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    "supply[s] for s in sources",
    "demand[d] for d in destinations",
    "capacity[s, d] for s in sources, d in destinations",
    "cost[s, d] for s in sources, d in destinations"
  ],
  "decision_variables": ["x[s, d] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[s, d] * x[s, d])"
  },
  "constraints": [
    "supply_balance[s]: sum(x[s, d] for d in destinations) == supply[s]",
    "demand_balance[d]: sum(x[s, d] for s in sources) == demand[d]",
    "capacity_limit[s, d]: x[s, d] <= capacity[s, d]"
  ]
}
```

### Common Pitfalls
- Forgetting to define the domain of variables as `NonNegativeReals`, leading to negative flows.
- Mismatching indices between parameter dictionaries and constraint rules, causing `KeyError`.
- Using `==` for supply/demand constraints when the problem might require `<=` or `>=` for surplus/shortage.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an efficient open-source LP solver (HiGHS or CBC) with proper configuration and robust solution status checking to ensure a valid result is extracted.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory (e.g., `SolverFactory('highs')` or `SolverFactory('cbc')`).
- Set practical solver options like `time_limit` and `threads` for performance control.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Verify Solution Status
- Check the solver status (`results.solver.status`) is `SolverStatus.ok`.
- Check the termination condition (`results.solver.termination_condition`) is `optimal` or `feasible`.
- If checks fail, print the status and termination condition for diagnostics before proceeding.

### Step 3 - Extract and Validate Results
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate through the `model.x` variable to retrieve the optimal flows.
- Optionally, implement a post-solve verification by recalculating constraint sums to ensure they match supply and demand parameters.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (Model built as per Modeling Stage)

# Solve
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
results = solver.solve(model, tee=False)

# Check results
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    # Extract solution
    solution = {(i, j): pyo.value(model.x[i, j]) for i in model.sources for j in model.destinations}
    print(f"Optimal cost: {objective_value}")
    # Add verification logic here
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Not checking both solver status *and* termination condition, potentially extracting results from an infeasible or error state.
- Assuming the solver variable `model.x` is automatically populated; always use `pyo.value()` to access the solution.
- Setting `tee=True` in production scripts, which can clutter logs with excessive solver output.

# Workflow 2 (Google OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' imperative API to build the model step-by-step. It is well-suited for rapid prototyping and integration into applications where a more procedural coding style is preferred.

### Step 1 - Initialize Solver and Data Structures
- Create a linear solver instance (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- Check the solver was successfully instantiated (`if solver is None:`).
- Store parameters in lists or dictionaries for easy access.

### Step 2 - Create Variables with Bounds
- Create decision variables `x[i][j]` using `solver.NumVar(lower_bound, upper_bound, name)`.
- Directly encode the `capacity[i][j]` as the variable's upper bound during creation, setting the lower bound to 0.

### Step 3 - Build Constraints and Objective
- For each source `i`, create a constraint `sum(x[i][j] for j) == supply[i]` using `solver.Add()`.
- For each destination `j`, create a constraint `sum(x[i][j] for i) == demand[j]`.
- Set the objective to minimize `sum(cost[i][j] * x[i][j])` using `solver.Minimize()`.

### Formulation Template
```json
{
  "sets": ["sources", "destinations"],
  "parameters": [
    "supply[i] for i in sources",
    "demand[j] for j in destinations",
    "capacity[i][j] for i in sources, j in destinations",
    "cost[i][j] for i in sources, j in destinations"
  ],
  "decision_variables": ["x[i][j] where 0 <= x[i][j] <= capacity[i][j]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "for each i: sum_j x[i][j] == supply[i]",
    "for each j: sum_i x[i][j] == demand[j]"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` instead of `solver.NumVar` for continuous flows, unnecessarily making the problem an integer program.
- Adding constraints in nested loops without clearing or reusing constraint objects, which is inefficient but not an error in OR-Tools.
- Not naming variables meaningfully, making debugging difficult for larger models.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver object, check the result status, and extract the solution. The imperative style makes solution extraction straightforward via the variable objects.

### Step 1 - Invoke Solver and Check Status
- Call `solver.Solve()`.
- Check the result status against `pywraplp.Solver.OPTIMAL` or `FEASIBLE`. Handle other statuses (INFEASIBLE, UNBOUNDED) with appropriate error messages.

### Step 2 - Extract Solution and Verify
- If optimal/feasible, retrieve the objective value via `solver.Objective().Value()`.
- Iterate through all variable objects to get their solution values with `var.solution_value()`.
- Implement an optional verification loop to sum flows and compare against original supply/demand parameters.

### Step 3 - Report Results and Handle Failures
- Print a summary of the objective value and key assignments.
- In case of failure, use the solver status to provide a clear diagnostic message (e.g., "Model is infeasible; check supply/demand totals").

### Code Usage
```python
from ortools.linear_solver import pywraplp

# ... (Data structures defined: supply, demand, capacity, cost)

# Initialize solver
solver = pywraplp.Solver.CreateSolver('GLOP')
if solver is None:
    raise Exception('Solver backend not available.')

# Create variables
x = {}
for i in sources:
    for j in destinations:
        x[i, j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')

# Add supply constraints
for i in sources:
    ct = solver.Constraint(supply[i], supply[i])
    for j in destinations:
        ct.SetCoefficient(x[i, j], 1)

# Add demand constraints
for j in destinations:
    ct = solver.Constraint(demand[j], demand[j])
    for i in sources:
        ct.SetCoefficient(x[i, j], 1)

# Set objective
objective = solver.Objective()
for i in sources:
    for j in destinations:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# Solve
status = solver.Solve()

# Check and extract
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    print(f'Optimal cost: {solver.Objective().Value()}')
    # Extract flows
    for i in sources:
        for j in destinations:
            flow_val = x[i, j].solution_value()
            if flow_val > 1e-6:  # Print non-zero assignments
                print(f'{i} -> {j}: {flow_val}')
else:
    print(f'No optimal solution found. Status: {status}')
```

### Common Pitfalls
- Confusing `solver.Solve()` return status codes with model feasibility; `OPTIMAL` and `FEASIBLE` are both success codes.
- Forgetting to check `if solver is None` after creation, leading to runtime errors if the requested backend is unavailable.
- Not using a tolerance (e.g., `1e-6`) when checking for non-zero flows, as solvers may return very small numerical values.
