---
name: Weighted Set Cover Optimization
description: |
  Model binary selection problems with coverage requirements as weighted set cover MILP, then solve with open-source solvers via Pyomo or OR-Tools.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Model the problem as a concrete Pyomo model using structured sets and rules, enabling clear separation of data and logic for maintainability and solver portability.

### Step 1 - Define Sets and Parameters
- Identify the set of selectable items (e.g., facilities, cameras, teams) and the set of elements requiring coverage (e.g., areas, tasks).
- Define a linear cost parameter for each item and a binary coverage mapping for each element, listing which items can cover it.

### Step 2 - Create Binary Decision Variables
- Instantiate a binary variable for each selectable item, where a value of 1 indicates selection.

### Step 3 - Formulate Linear Objective
- Define the objective to minimize the total linear cost: the sum of each item's cost multiplied by its binary variable.

### Step 4 - Implement Coverage Constraints
- For each element requiring coverage, add a constraint ensuring the sum of the binary variables for items that cover it is at least one.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items.",
    "J: Set of elements requiring coverage."
  ],
  "parameters": [
    "cost[i ∈ I]: Linear cost of selecting item i.",
    "cover[j ∈ J]: List of items i ∈ I that can cover element j."
  ],
  "decision_variables": [
    "x[i ∈ I] ∈ {0, 1}: 1 if item i is selected."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost[i] * x[i]"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ cover[j]} x[i] ≥ 1, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Using inconsistent indexing between cost dictionary and coverage mapping, leading to missing coefficients.
- Forgetting to verify the coverage mapping is complete for all elements, resulting in infeasible models.
- Defining the coverage parameter as a dense matrix for sparse problems, causing unnecessary memory overhead.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source MILP solver (HiGHS or CBC), configuring performance limits and robustly checking solver status before extracting and verifying the solution.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory (e.g., `"highs"` or `"cbc"`). Set practical options: time limit, optimality gap tolerance (e.g., 0.0), and thread count for parallelism.
- Call the solver on the model, suppressing the log output (`tee=False`) unless debugging.

### Step 2 - Check Solver Status and Termination
- Inspect the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if the solve was successful.

### Step 3 - Extract and Verify Solution
- Retrieve selected items where the variable value exceeds 0.5 (accounting for numerical tolerance). Compute the total cost from the objective value.
- Programmatically verify that every element is covered by at least one selected item using the coverage mapping.

### Step 4 - Output Standardized Results
- Package the solution status, objective value, list of selected items, and verification result into a structured dictionary (e.g., JSON) for downstream use.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
def cover_rule(m, j):
    return sum(m.x[i] for i in coverage[j]) >= 1
model.cover = pyo.Constraint(model.J, rule=cover_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = float(pyo.value(model.obj))
    # Verification
    verified = all(any(pyo.value(model.x[i]) > 0.5 for i in coverage[j]) for j in elements)
    solution_payload = {
        "status": "optimal" if term == TerminationCondition.optimal else "feasible",
        "objective_value": total_cost,
        "selected_items": selected,
        "coverage_verified": verified
    }
else:
    solution_payload = {"status": "failed", "solver_status": str(status), "termination": str(term)}
```

### Common Pitfalls
- Not checking both solver status and termination condition, potentially extracting invalid solutions from interrupted solves.
- Using a loose optimality gap (`mip_rel_gap`) when an exact solution is required, leading to suboptimal selections.
- Failing to implement post-solve verification, which can miss modeling errors that the solver tolerated.

# Workflow 2 (OR-Tools MIP/CP-SAT)

## Modeling stage

### Strategy Overview
Model the set cover problem directly using the OR-Tools linear solver (MIP) or CP-SAT API, which is efficient for binary programs and offers fine-grained control over the solving process.

### Step 1 - Map Problem Data
- Define lists/dictionaries for item costs and for coverage, where each element maps to a list of covering item indices.

### Step 2 - Instantiate Solver and Variables
- Create a solver instance (e.g., `"SCIP"` for MIP or `CpModel()` for CP-SAT). For MIP, create binary integer variables. For CP-SAT, create Boolean variables.

### Step 3 - Build Coverage Constraints
- For each element, create a linear constraint with a lower bound of 1. Add the binary/Boolean variable for each covering item with a coefficient of 1.

### Step 4 - Set Linear Objective
- Define the objective as the sum of each item's cost multiplied by its variable, and set the sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "I: Index set of selectable items.",
    "J: Index set of elements requiring coverage."
  ],
  "parameters": [
    "cost[i ∈ I]: Linear cost of item i.",
    "cover[j ∈ J]: List of item indices i that cover element j."
  ],
  "decision_variables": [
    "x[i ∈ I] ∈ {0, 1}: Selection variable for item i."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost[i] * x[i]"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ cover[j]} x[i] ≥ 1, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Using the wrong OR-Tools solver type for the problem (e.g., MIP for very large combinatorial problems where CP-SAT may be more effective).
- Incorrectly setting constraint bounds (e.g., using `solver.infinity()` as the upper bound for a '≥1' constraint).
- Not naming variables and constraints, making debugging difficult for larger instances.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' MIP or CP-SAT solver, configure performance settings, extract the solution with numerical tolerance checks, and validate coverage.

### Step 1 - Configure Solver Settings
- Set a time limit (in milliseconds for MIP, seconds for CP-SAT) and the number of parallel workers (`SetNumThreads` for MIP, `num_search_workers` for CP-SAT) to balance speed and resource use.

### Step 2 - Execute Solve and Check Status
- Call the solver's `Solve()` method. Check the return status against `OPTIMAL` and `FEASIBLE` constants (MIP) or `OPTIMAL` and `FEASIBLE` (CP-SAT).

### Step 3 - Extract Selected Items
- Iterate through decision variables. For MIP, use `solution_value() > 0.5`. For CP-SAT, use `BooleanValue()` or `Value()`. Collect indices of selected items.

### Step 4 - Verify and Package Results
- Verify coverage by checking each element's covering list against the selected items. Assemble a result dictionary containing status, objective value, selection list, and verification flag.

### Code Usage
```python
# Option A: Using OR-Tools MIP Solver (SCIP/CBC)
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver("SCIP")
# Create variables
x = {i: solver.IntVar(0, 1, f'x_{i}') for i in items}
# Add coverage constraints
for j in elements:
    constraint = solver.Constraint(1, solver.infinity(), f'cover_{j}')
    for i in coverage[j]:
        constraint.SetCoefficient(x[i], 1)
# Set objective
objective = solver.Objective()
for i in items:
    objective.SetCoefficient(x[i], cost[i])
objective.SetMinimization()
# Configure and solve
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()
# Check status and extract
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [i for i in items if x[i].solution_value() > 0.5]
    total_cost = objective.Value()
    verified = all(any(x[i].solution_value() > 0.5 for i in coverage[j]) for j in elements)

# Option B: Using OR-Tools CP-SAT
from ortools.sat.python import cp_model

model = cp_model.CpModel()
x = {i: model.NewBoolVar(f'x_{i}') for i in items}
# Objective
model.Minimize(sum(cost[i] * x[i] for i in items))
# Constraints
for j in elements:
    model.Add(sum(x[i] for i in coverage[j]) >= 1)
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in items if solver.Value(x[i]) == 1]
    total_cost = solver.ObjectiveValue()
    verified = all(any(solver.Value(x[i]) == 1 for i in coverage[j]) for j in elements)
```

### Common Pitfalls
- Confusing MIP and CP-SAT status codes or solution value access methods, leading to runtime errors.
- Setting an overly restrictive time limit that prevents finding a feasible solution for larger instances.
- Neglecting to implement a fallback solver strategy if the primary solver fails or is unavailable.
