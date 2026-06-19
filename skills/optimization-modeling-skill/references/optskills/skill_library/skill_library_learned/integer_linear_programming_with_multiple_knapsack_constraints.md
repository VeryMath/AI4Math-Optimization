---
name: Integer Linear Programming with Multiple Knapsack Constraints
description: |
  Model and solve integer linear programs with bounded, nonnegative integer variables, a linear objective to maximize profit, and multiple linear inequality (knapsack) constraints using structured formulations and robust solver backends.
---

# Workflow 1 (OR-Tools / SCIP Backend)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to construct a Mixed-Integer Linear Programming (MILP) model. It is ideal for direct, low-level model building with explicit variable and constraint creation, leveraging the robust SCIP or CBC solvers for integer problems.

### Step 1 - Define Sets and Parameters
- Declare sets for items and constraints as Python lists or ranges for indexing.
- Store parameters (e.g., profit coefficients, demand upper bounds, constraint capacities, and constraint coefficients) in dictionaries or lists keyed by set indices.
- For each constraint, structure data to efficiently list the included item indices (e.g., `constraint["packages"]`) and its `capacity`.

### Step 2 - Create Bounded Integer Variables
- For each item, create an integer decision variable using `solver.IntVar(lower_bound, upper_bound, name)`.
- Set the lower bound to 0 (nonnegative) and the upper bound to the item's demand limit, incorporating bounds directly to reduce constraint count.

### Step 3 - Formulate Linear Objective
- Create an objective expression using `solver.Objective()`.
- For each variable, set its coefficient using `objective.SetCoefficient(variable, profit_coefficient)`.
- Call `objective.SetMaximization()` to define the optimization sense.

### Step 4 - Add Multiple Knapsack Constraints
- For each constraint, create a linear expression summing the relevant variables (using the pre-structured list of included item indices).
- Add the inequality to the solver using `solver.Add(sum_expr <= capacity)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "C: set of constraints (knapsacks)"
  ],
  "parameters": [
    "profit[i]: profit coefficient for item i in I",
    "demand_limit[i]: upper bound for item i in I",
    "capacity[c]: capacity of constraint c in C",
    "included_items[c]: list of item indices included in constraint c"
  ],
  "decision_variables": [
    "x[i]: nonnegative integer quantity of item i to select, 0 <= x[i] <= demand_limit[i]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in included_items[c]) <= capacity[c] for each c in C"
  ]
}
```

### Common Pitfalls
- Forgetting to set the upper bound on integer variables, leading to unbounded or unrealistic solutions.
- Inefficiently building constraint expressions inside nested loops for large problems; pre-structure coefficient data as lists of included indices.
- Not using descriptive variable names, making debugging and solution interpretation difficult.

## Solving stage

### Strategy Overview
Solve the constructed model using the SCIP or CBC backend via OR-Tools. Configure solver parameters for performance, rigorously check the solution status, and extract and verify the integer solution.

### Step 1 - Configure Solver and Solve
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Set practical limits: `solver.SetTimeLimit([TIME_LIMIT_IN_MS])` and `solver.SetNumThreads([THREAD_COUNT])`.
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Check Solver Status
- Check the result status: `status = solver.Solve()`.
- Proceed only if status is `OPTIMAL` or `FEASIBLE`. Use `if status in [solver.OPTIMAL, solver.FEASIBLE]:`.

### Step 3 - Extract and Verify Solution
- If the status is acceptable, extract variable values using `variable.solution_value()` and cast to integers.
- Programmatically verify that all variable bounds and constraints are satisfied within a small numerical tolerance.
- Recompute the objective value from the extracted solution for cross-checking.
- Print key statistics: total units selected, number of non-zero items, and which constraints are tight (at capacity).

### Step 4 - Structure Output
- Return a consistent output structure containing the solution status, objective value, and a dictionary of variable values.
- Log any warnings for non-optimal statuses or constraint violations.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
# ... (variable and constraint creation as per modeling stage)
solver.SetTimeLimit(30000)  # 30 seconds
solver.SetNumThreads(4)

# solve with status / termination checks
status = solver.Solve()
solution = {}
if status in [solver.OPTIMAL, solver.FEASIBLE]:
    objective_value = solver.Objective().Value()
    for i in items:
        val = x[i].solution_value()
        solution[i] = int(round(val))  # Ensure integer
    # ... (verification logic)
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Assuming `OPTIMAL` status without checking, leading to errors when accessing solution values on failed solves.
- Not converting floating-point solution values to integers, which may cause issues in downstream integer-required applications.
- Omitting solution verification, potentially accepting solutions that violate constraints due to numerical tolerances.

# Workflow 2 (Pyomo / HiGHS Backend)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo for abstract, declarative model formulation, separating model structure from data. It leverages the HiGHS solver via Pyomo's `SolverFactory` for solving MILPs, benefiting from Pyomo's set-based indexing and rule-based constraint definitions.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo Sets (`pyo.Set`) for items and constraints to enable indexed components.
- Define Pyomo Parameters (`pyo.Param`) for profit, demand limits, capacities, and constraint coefficients, initialized from data dictionaries.
- For efficient constraint definition, pre-structure data: for each constraint, store a list of included item indices.

### Step 2 - Declare Bounded Integer Variables
- Create a Pyomo `Var` for items with domain `pyo.NonNegativeIntegers`.
- Set variable bounds using the `bounds` argument (e.g., `bounds=(0, model.demand_limit[i])`) to embed demand limits.

### Step 3 - Formulate Objective Function
- Define a Pyomo `Objective` rule that maximizes the sum of profit coefficients multiplied by their corresponding variables.

### Step 4 - Define Constraint Rules
- For each constraint, define a rule function that sums the variables for the pre-computed list of included items.
- Use Pyomo's `Constraint` component, indexed by the constraint set, to create all inequalities efficiently.

### Formulation Template
```json
{
  "sets": [
    "I: set of items",
    "C: set of constraints (knapsacks)"
  ],
  "parameters": [
    "profit[i]: profit coefficient for item i in I",
    "demand_limit[i]: upper bound for item i in I",
    "capacity[c]: capacity of constraint c in C",
    "included_items[c]: list of item indices included in constraint c"
  ],
  "decision_variables": [
    "x[i]: nonnegative integer quantity of item i to select"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[i] * x[i] for i in I)"
  },
  "constraints": [
    "sum(x[i] for i in included_items[c]) <= capacity[c] for each c in C",
    "x[i] <= demand_limit[i] for each i in I (implicit in variable bounds)"
  ]
}
```

### Common Pitfalls
- Defining constraint rules that inefficiently iterate over full sets; instead, use pre-computed lists of included indices for each constraint.
- Confusing Pyomo's 1-based indexing if data uses 0-based indexing; ensure consistent index mapping.
- Not using `initialize` correctly for Parameters, leading to uninitialized data errors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS MILP solver. Configure solver options for time limit and optimality gap, check termination conditions rigorously, and extract the solution while verifying its integer feasibility.

### Step 1 - Configure and Execute Solver
- Create a solver object: `solver = pyo.SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = [TIME_LIMIT]` and `solver.options['threads'] = [THREAD_COUNT]`.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Inspect Solver Status and Termination
- Check `results.solver.status` is `pyo.SolverStatus.ok`.
- Check `results.solver.termination_condition` is `pyo.TerminationCondition.optimal` or `...feasible`.
- Proceed only if both checks indicate a valid solution.

### Step 3 - Extract and Process Solution
- Access variable values using `pyo.value(model.x[i])` and convert to integers.
- Recompute constraint left-hand sides to verify satisfaction within tolerance.
- Calculate the objective value from the extracted solution as a sanity check.
- Compute and report key statistics: total units selected and constraint utilization.

### Step 4 - Generate Structured Output
- Package the solution into a dictionary or dataclass, including status, objective value, variable values, and verification flags.
- Provide clear warnings or errors if the solution is not integer-feasible.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.C = pyo.Set(initialize=constraints)
# ... (parameter and variable definition as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.obj)
    solution = {i: int(pyo.value(model.x[i])) for i in model.I}
    # ... (verification logic)
else:
    print("Solver did not return a valid solution.")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially misinterpreting infeasible or error states.
- Extracting variable values without converting `pyo.value` result to integer, risking floating-point values for integer variables.
- Ignoring the `tee` option during debugging; setting `tee=True` can provide valuable solver log output.
