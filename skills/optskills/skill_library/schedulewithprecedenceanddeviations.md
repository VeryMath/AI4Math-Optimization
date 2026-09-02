---
name: ScheduleWithPrecedenceAndDeviations
description: |
  Model and solve scheduling problems with precedence decisions, time windows, and piecewise-linear deviation penalties using MILP formulations and modern solvers.
---

# Workflow 1 (CP-SAT with Explicit Big-M)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) suitable for constraint programming/satisfiability solvers like OR-Tools CP-SAT. Use integer time variables, binary precedence variables, and linear constraints with a conservative Big-M to enforce disjunctive separation.

### Step 1 - Define Core Variables
- Create an integer variable `t[i]` for each entity `i`, bounded by its earliest and latest time.
- Create a binary variable `x[i,j]` for each unordered pair `(i, j)` where `i < j`, representing that `i` precedes `j`.
- Create non-negative continuous or integer variables `e[i]` and `l[i]` to capture early and late deviations from a target time.

### Step 2 - Enforce Time Windows and Deviation Definitions
- Add constraints `earliest[i] <= t[i] <= latest[i]` for each entity `i`.
- Define early deviation: `e[i] >= target[i] - t[i]`. Since `e[i]` is non-negative, it captures positive earliness.
- Define late deviation: `l[i] >= t[i] - target[i]`. Since `l[i]` is non-negative, it captures positive lateness.

### Step 3 - Model Precedence and Separation
- For each unordered pair `(i, j)`, enforce mutual exclusivity: `x[i,j] + x[j,i] = 1`.
- For each ordered pair, add a Big-M constraint to enforce separation if that order is chosen: `t[j] >= t[i] + sep[i,j] - M * (1 - x[i,j])`. Choose `M` as a sufficiently large constant (e.g., `max_time_range + max_separation`).

### Step 4 - Formulate Objective
- Minimize the weighted sum of deviations: `min sum( early_penalty[i] * e[i] + late_penalty[i] * l[i] )`.

### Formulation Template
```json
{
  "sets": [
    "Entities",
    "UnorderedPairs"
  ],
  "parameters": [
    {"name": "earliest", "domain": "Entities", "type": "float"},
    {"name": "latest", "domain": "Entities", "type": "float"},
    {"name": "target", "domain": "Entities", "type": "float"},
    {"name": "early_penalty", "domain": "Entities", "type": "float"},
    {"name": "late_penalty", "domain": "Entities", "type": "float"},
    {"name": "sep", "domain": "UnorderedPairs", "type": "float"},
    {"name": "M", "type": "float"}
  ],
  "decision_variables": [
    {"name": "t", "domain": "Entities", "type": "integer", "bounds": "[earliest[i], latest[i]]"},
    {"name": "x", "domain": "UnorderedPairs", "type": "binary"},
    {"name": "e", "domain": "Entities", "type": "continuous", "bounds": "[0, INF]"},
    {"name": "l", "domain": "Entities", "type": "continuous", "bounds": "[0, INF]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( early_penalty[i] * e[i] + late_penalty[i] * l[i] for i in Entities )"
  },
  "constraints": [
    {"name": "deviation_early", "formula": "e[i] >= target[i] - t[i]", "domain": "Entities"},
    {"name": "deviation_late", "formula": "l[i] >= t[i] - target[i]", "domain": "Entities"},
    {"name": "mutual_exclusion", "formula": "x[i,j] + x[j,i] == 1", "domain": "UnorderedPairs"},
    {"name": "separation_if_precedes", "formula": "t[j] >= t[i] + sep[i,j] - M * (1 - x[i,j])", "domain": "UnorderedPairs"}
  ]
}
```

### Common Pitfalls
- Using an excessively large Big-M value, which weakens the linear relaxation and slows solving.
- Forgetting to enforce mutual exclusivity of precedence variables, leading to infeasible or incorrect orders.
- Modeling deviations with `abs(target[i] - t[i])` directly, which is non-linear; always use separate non-negative variables.

## Solving stage

### Strategy Overview
Solve the MILP using OR-Tools CP-SAT solver. Configure search parameters for performance and reproducibility, extract and verify the solution, and handle solver statuses appropriately.

### Step 1 - Configure Solver and Build Model
- Instantiate a CP-SAT model.
- Create variables using `NewIntVar` for times (within integer bounds) and `NewBoolVar` for binaries.
- Add all constraints using `model.Add()` with linear expressions.

### Step 2 - Set Solver Parameters and Solve
- Configure the solver: set a time limit, number of parallel workers, random seed, and optionally a relative gap tolerance.
- Call the solver and capture the status.

### Step 3 - Extract and Verify Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Extract variable values using `solver.Value(var)`.
- Programmatically verify all hard constraints (time windows, separation) and recalculate the objective from primal values to ensure consistency.

### Step 4 - Output Structured Results
- Return a dictionary or JSON containing the status, objective value, schedule times, deviations, and the derived precedence order.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
# ... create variables and add constraints as per modeling stage ...

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    solution = {}
    solution['status'] = 'OPTIMAL' if status == cp_model.OPTIMAL else 'FEASIBLE'
    solution['objective'] = solver.ObjectiveValue()
    solution['times'] = {i: solver.Value(t_var[i]) for i in entities}
    # ... extract other variables ...
    # Verification logic here
    return solution
else:
    return {'status': 'INFEASIBLE_OR_UNBOUNDED', 'objective': None}
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions.
- Assuming variable values exist when the status is not feasible, leading to runtime errors.
- Omitting verification, which can mask modeling errors in constraint definitions.

# Workflow 2 (Pyomo with Tight Big-M and MILP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a MILP using an algebraic modeling language (Pyomo). Use continuous time variables, a tight, pair-specific Big-M derived from time windows, and separate deviation constraints. This formulation is solved by general-purpose MILP solvers (e.g., Gurobi, HiGHS).

### Step 1 - Define Variables and Bounds
- Create a continuous variable `t[i]` for each entity `i`. Set its bounds directly to `[earliest[i], latest[i]]`.
- Create non-negative continuous variables `e[i]` and `l[i]` for deviations.
- Create a binary variable `y[i,j]` for each unordered pair `(i, j)` where `i < j`, indicating `i` precedes `j`.

### Step 2 - Model Deviation Constraints
- For each entity `i`, add constraints: `t[i] + e[i] >= target[i]` and `t[i] - l[i] <= target[i]`. This ensures `e[i]` and `l[i]` capture the positive deviations.

### Step 3 - Enforce Disjunctive Separation with Tight Big-M
- For each unordered pair `(i, j)` with `i < j`, enforce mutual exclusivity: `y[i,j] + y[j,i] = 1`.
- Calculate a tight Big-M for each pair: `M_ij = latest[i] - earliest[j] + sep[i,j]`.
- Add the separation constraint: `t[j] >= t[i] + sep[i,j] - M_ij * (1 - y[i,j])`.

### Step 4 - Define Linear Objective
- Minimize the weighted deviation sum: `min sum( early_penalty[i] * e[i] + late_penalty[i] * l[i] )`.

### Formulation Template
```json
{
  "sets": [
    "Entities",
    "OrderedPairs"
  ],
  "parameters": [
    {"name": "earliest", "domain": "Entities", "type": "float"},
    {"name": "latest", "domain": "Entities", "type": "float"},
    {"name": "target", "domain": "Entities", "type": "float"},
    {"name": "early_penalty", "domain": "Entities", "type": "float"},
    {"name": "late_penalty", "domain": "Entities", "type": "float"},
    {"name": "sep", "domain": "OrderedPairs", "type": "float"}
  ],
  "decision_variables": [
    {"name": "t", "domain": "Entities", "type": "continuous", "bounds": "[earliest[i], latest[i]]"},
    {"name": "y", "domain": "OrderedPairs", "type": "binary"},
    {"name": "e", "domain": "Entities", "type": "continuous", "bounds": "[0, INF]"},
    {"name": "l", "domain": "Entities", "type": "continuous", "bounds": "[0, INF]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( early_penalty[i] * e[i] + late_penalty[i] * l[i] for i in Entities )"
  },
  "constraints": [
    {"name": "deviation_early_def", "formula": "t[i] + e[i] >= target[i]", "domain": "Entities"},
    {"name": "deviation_late_def", "formula": "t[i] - l[i] <= target[i]", "domain": "Entities"},
    {"name": "mutual_exclusion", "formula": "y[i,j] + y[j,i] == 1", "domain": "OrderedPairs where i < j"},
    {"name": "separation", "formula": "t[j] >= t[i] + sep[i,j] - (latest[i] - earliest[j] + sep[i,j]) * (1 - y[i,j])", "domain": "OrderedPairs where i != j"}
  ]
}
```

### Common Pitfalls
- Using a single, overly large Big-M for all pairs instead of calculating tight, pair-specific values.
- Incorrectly indexing separation parameters `sep[i,j]` when the separation is not symmetric.
- Defining deviation constraints that allow both `e[i]` and `l[i]` to be positive simultaneously, which is valid but may confuse interpretation.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a connected MILP solver (e.g., Gurobi, HiGHS, CBC). Configure solver-specific parameters for performance, handle termination conditions, and implement robust solution extraction and verification.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object via `SolverFactory`.
- Set key parameters: time limit, relative MIP gap tolerance, number of threads, and a random seed for reproducibility.

### Step 2 - Solve and Capture Results
- Execute the solve with `tee=True` for optional verbose output.
- Capture the solver status and termination condition.

### Step 3 - Process Solution Status
- Check if the solve was successful (`SolverStatus.ok` and `TerminationCondition.optimal` or `.feasible`).
- For successful solves, load the solution into the model instance and extract variable values.
- For failures (infeasible, unbounded, time limit), extract and report the relevant status information.

### Step 4 - Verify and Report
- Recalculate the objective from the primal variable values to verify consistency.
- Optionally, run a constraint verification function to ensure all hard constraints are satisfied.
- Output a standardized result structure containing all relevant solution data.

### Code Usage
```python
import pyomo.environ as pyo

# Build model (assuming `model` is a Pyomo ConcreteModel)
# ... variable and constraint definitions as per modeling stage ...

# Solve
solver = pyo.SolverFactory('gurobi')  # or 'highs', 'cbc'
solver_options = {
    'TimeLimit': 60,
    'MIPGap': 1e-4,
    'Threads': 4,
    'Seed': 42
}
results = solver.solve(model, options=solver_options, tee=False)

# Process results
from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in (TerminationCondition.optimal, TerminationCondition.feasible):
    solution = {}
    solution['status'] = str(termination)
    solution['objective'] = pyo.value(model.obj)
    solution['times'] = {i: pyo.value(model.t[i]) for i in model.A}
    # ... extract other variables ...
    # Verification logic here
    return solution
else:
    return {'status': f'{status}:{termination}', 'objective': None}
```

### Common Pitfalls
- Confusing Pyomo's `SolverStatus` with the solver's own termination condition; both must be checked.
- Not loading the solution into the model instance before extracting variable values, leading to `None` values.
- Ignoring time-limit stops; a feasible solution may still be available and should be extracted.
