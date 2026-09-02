---
name: Multi-Resource Assignment Optimization
description: |
  Model and solve linear cost-minimization problems where discrete or continuous resources with capacity contributions must be assigned to tasks to meet demands, subject to supply limits.
---

# Workflow 1 (Integer Assignment with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as an Integer Linear Program (ILP) using OR-Tools' MIP solver interface. This workflow is suited for problems requiring discrete, whole-unit assignments (e.g., assigning aircraft, machines, or personnel counts). It directly maps resource-task pairs to integer decision variables with linear constraints for supply and weighted demand coverage.

### Step 1 - Define Data Structures
- Organize problem data into indexed lists or dictionaries for resources and tasks.
- Define parameters: `availability[i]` (supply per resource), `demand[j]` (requirement per task), `capacity[i][j]` (contribution per unit), and `cost[i][j]` (cost per unit assignment).

### Step 2 - Create Integer Decision Variables
- For each resource `i` and task `j`, create an integer variable `x[i][j]` representing the assignment count.
- Set the variable domain to non-negative integers, optionally bounded above by the resource's availability.

### Step 3 - Formulate Supply Constraints
- For each resource `i`, add a linear inequality constraint: the sum of all assignments for that resource must not exceed its availability (`sum_j x[i][j] <= availability[i]`).

### Step 4 - Formulate Demand Coverage Constraints
- For each task `j`, add a linear inequality constraint: the weighted sum of assigned resources must meet or exceed the demand (`sum_i capacity[i][j] * x[i][j] >= demand[j]`).

### Step 5 - Define Linear Cost Objective
- Define the objective to minimize total cost: `minimize sum_i sum_j cost[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": [
    "availability[resource]",
    "demand[task]",
    "capacity[resource][task]",
    "cost[resource][task]"
  ],
  "decision_variables": ["x[resource][task] ∈ ℤ⁺"],
  "objective": {
    "sense": "min",
    "expression": "∑∑ cost[resource][task] * x[resource][task]"
  },
  "constraints": [
    "supply[resource]: ∑_task x[resource][task] ≤ availability[resource]",
    "demand[task]: ∑_resource capacity[resource][task] * x[resource][task] ≥ demand[task]"
  ]
}
```

### Common Pitfalls
- Forgetting to set upper bounds on integer variables, which can lead to unbounded or inefficient solving.
- Using floating-point values for `capacity` or `demand` when the solver expects integer coefficients; scale data appropriately.
- Mis-indexing parameters in nested loops when building constraints, leading to incorrect coefficient assignment.

## Solving stage

### Strategy Overview
Solve the ILP model using OR-Tools' wrapper for SCIP or CBC. Configure performance settings, execute the solve, and rigorously verify the solution's feasibility and integrality before extracting results.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set practical limits: `solver.SetTimeLimit(30000)` for a 30-second timeout and `solver.SetNumThreads(4)` for parallel processing.

### Step 2 - Build Model from Formulation
- Translate the modeling steps into code using loops to create variables, set objective coefficients, and add constraints via `constraint.SetCoefficient()`.

### Step 3 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: accept solutions marked as `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNBOUNDED` statuses with appropriate error reporting.

### Step 4 - Extract and Validate Solution
- If the status is acceptable, extract the objective value: `solver.Objective().Value()`.
- Extract variable values using `x[i][j].solution_value()` and convert to integers (e.g., `int(round(val))`).
- Programmatically verify constraints by recomputing total resource usage and delivered capacity per task against the original parameters.

### Step 5 - Structure and Output Results
- Package the results (status, objective value, non-zero assignments, verification metrics) into a structured JSON or dictionary for downstream use.

### Code Usage
```python
# Example using OR-Tools for integer assignment
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise RuntimeError("Solver backend not available.")
solver.SetTimeLimit(30000)

# 2. Define data (placeholders)
resources = [...]  # list of resource identifiers
tasks = [...]      # list of task identifiers
availability = {...}
demand = {...}
capacity = {...}   # dict of dicts: capacity[resource][task]
cost = {...}       # dict of dicts: cost[resource][task]

# 3. Create variables
x = {}
for i in resources:
    for j in tasks:
        x[i, j] = solver.IntVar(0, solver.infinity(), f'x_{i}_{j}')

# 4. Add supply constraints
for i in resources:
    constraint = solver.Constraint(0, availability[i])
    for j in tasks:
        constraint.SetCoefficient(x[i, j], 1)

# 5. Add demand constraints
for j in tasks:
    constraint = solver.Constraint(demand[j], solver.infinity())
    for i in resources:
        constraint.SetCoefficient(x[i, j], capacity[i][j])

# 6. Set objective
objective = solver.Objective()
for i in resources:
    for j in tasks:
        objective.SetCoefficient(x[i, j], cost[i][j])
objective.SetMinimization()

# 7. Solve and check status
status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    obj_val = objective.Value()
    assignments = {}
    for i in resources:
        for j in tasks:
            val = x[i, j].solution_value()
            if val > 0.5:  # tolerance for integer extraction
                assignments[(i, j)] = int(round(val))
    # ... verification and output ...
else:
    # Handle failure
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Not checking solver backend availability, which can cause runtime errors.
- Extracting variable values without verifying the solve status first, leading to access errors.
- Ignoring numerical precision when converting floating-point solution values to integers; use rounding with a tolerance.

# Workflow 2 (Linear/Integer Assignment with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem as a ConcreteModel in Pyomo, providing a declarative, solver-agnostic definition. This workflow cleanly separates model construction from solving, supporting both continuous (LP) and integer (MILP) domains. It is ideal for prototyping and leveraging Pyomo's advanced features like sets and rules.

### Step 1 - Define Pyomo Sets and Parameters
- Create Pyomo `Set` objects for `model.R` (resources) and `model.T` (tasks).
- Define `Param` objects or use plain dictionaries for `availability`, `demand`, `capacity`, and `cost` parameters, indexed by the appropriate sets.

### Step 2 - Declare Decision Variables
- Create a Pyomo `Var` object `model.x` indexed over `model.R` and `model.T`.
- Choose the domain: `pyo.NonNegativeReals` for continuous allocation or `pyo.NonNegativeIntegers` for discrete assignment.

### Step 3 - Implement Constraint Rules
- Define a rule function for supply constraints: for each resource `r`, `sum(model.x[r, t] for t in model.T) <= availability[r]`.
- Define a rule function for demand constraints: for each task `t`, `sum(capacity[r][t] * model.x[r, t] for r in model.R) >= demand[t]`.
- Optionally, add individual assignment limit constraints: `model.x[r, t] <= max_assignment[r][t]`.

### Step 4 - Define the Objective Rule
- Create an `Objective` rule: `sum(cost[r][t] * model.x[r, t] for r in model.R for t in model.T)` with sense `minimize`.

### Formulation Template
```json
{
  "sets": ["R (resources)", "T (tasks)"],
  "parameters": [
    "availability[R]",
    "demand[T]",
    "capacity[R][T]",
    "cost[R][T]",
    "max_assignment[R][T] (optional)"
  ],
  "decision_variables": ["x[R, T] ∈ ℝ⁺ or ℤ⁺"],
  "objective": {
    "sense": "min",
    "expression": "∑∑ cost[R][T] * x[R, T]"
  },
  "constraints": [
    "supply[R]: ∑_T x[R, T] ≤ availability[R]",
    "demand[T]: ∑_R capacity[R][T] * x[R, T] ≥ demand[T]",
    "limit[R, T]: x[R, T] ≤ max_assignment[R, T] (optional)"
  ]
}
```

### Common Pitfalls
- Defining constraint or objective rules that directly reference external data instead of model parameters, breaking model portability.
- Using mutable default arguments (like `[]`) in rule functions.
- Confusing Pyomo's 1-based indexing with Python's 0-based indexing when initializing sets from lists.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an appropriate solver factory (e.g., `'highs'` for LP, `'cbc'` for MILP). Configure solver options, handle solution loading carefully, and implement systematic verification of the results.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = pyo.SolverFactory('cbc')` for integer problems or `'highs'` for continuous ones.
- Set options: `solver.options['seconds'] = 30` (time limit), `solver.options['ratio'] = 0.0` (optimality gap).

### Step 2 - Solve with Robust Status Handling
- Execute the solve with `load_solutions=False` to prevent errors on failed solves: `results = solver.solve(model, tee=False, load_solutions=False)`.
- Check the high-level status: `assert results.solver.status == pyo.SolverStatus.ok`.
- Check the termination condition: accept `optimal` or `feasible`.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Iterate through variables to collect non-zero assignments, applying a tolerance (e.g., `if pyo.value(model.x[r, t]) > 1e-6`).

### Step 4 - Verify Solution Feasibility
- Programmatically compute total resource usage and delivered capacity per task from the extracted assignments.
- Compare these computed values against the original `availability` and `demand` parameters to verify all constraints are satisfied within a small tolerance.

### Step 5 - Package Output
- Structure the output into a dictionary or JSON containing the solve status, objective value, assignment list, and verification results.

### Code Usage
```python
# Example using Pyomo for flexible assignment
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build model
model = pyo.ConcreteModel()
model.R = pyo.Set(initialize=resources)
model.T = pyo.Set(initialize=tasks)

# Parameters (using dictionaries)
availability_dict = {...}
demand_dict = {...}
capacity_dict = {...}  # capacity_dict[r][t]
cost_dict = {...}      # cost_dict[r][t]

# Variables (choose domain)
model.x = pyo.Var(model.R, model.T, domain=pyo.NonNegativeIntegers)  # or NonNegativeReals

# Objective
def obj_rule(m):
    return sum(cost_dict[r][t] * m.x[r, t] for r in m.R for t in m.T)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Supply constraints
def supply_rule(m, r):
    return sum(m.x[r, t] for t in m.T) <= availability_dict[r]
model.supply_con = pyo.Constraint(model.R, rule=supply_rule)

# Demand constraints
def demand_rule(m, t):
    return sum(capacity_dict[r][t] * m.x[r, t] for r in m.R) >= demand_dict[t]
model.demand_con = pyo.Constraint(model.T, rule=demand_rule)

# 2. Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0

results = solver.solve(model, tee=False, load_solutions=False)

# 3. Check status and load
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                             TerminationCondition.feasible)):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    assignments = {}
    for r in model.R:
        for t in model.T:
            val = pyo.value(model.x[r, t])
            if val > 0.5:  # tolerance for integer extraction
                assignments[(r, t)] = int(round(val))
    # ... verification and output ...
else:
    # Handle failure
    print(f"Solver failed. Status: {results.solver.status}, "
          f"Termination: {results.solver.termination_condition}")
```

### Common Pitfalls
- Attempting to access variable values (`pyo.value`) before loading the solution, resulting in `ValueError`.
- Not setting `load_solutions=False` when solving, which can cause crashes on infeasible or unbounded models.
- Overlooking the difference between `SolverStatus` and `TerminationCondition`; both must be checked for reliable solution extraction.
