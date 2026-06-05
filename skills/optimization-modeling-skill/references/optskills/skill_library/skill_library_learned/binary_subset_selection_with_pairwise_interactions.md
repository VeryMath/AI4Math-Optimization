---
name: Binary Subset Selection with Pairwise Interactions
description: |
  Model and solve subset selection problems with cardinality constraints and pairwise interaction objectives using linearized binary variables.
---

# Workflow 1 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo to formulate a Mixed-Integer Programming (MIP) model. It explicitly linearizes the quadratic pairwise selection term using auxiliary binary variables and standard logical linking constraints, suitable for solvers like Gurobi, CPLEX, or HiGHS.

### Step 1 - Define Core Selection Variables
- Define a set `N` representing all candidate elements.
- Create binary decision variables `x[i]` for each `i` in `N`, where `x[i] = 1` indicates element `i` is selected.

### Step 2 - Define Pairwise Activation Variables
- For each ordered pair `(i, j)` where `i != j`, create auxiliary binary variables `z[i,j]`.
- The variable `z[i,j]` will be forced to equal `x[i] * x[j]` via constraints.

### Step 3 - Enforce Logical Linking
- Add constraints `z[i,j] <= x[i]` for all `i != j`.
- Add constraints `z[i,j] <= x[j]` for all `i != j`.
- Add constraints `z[i,j] >= x[i] + x[j] - 1` for all `i != j`. This set of constraints enforces `z[i,j] = 1` if and only if `x[i] = 1` and `x[j] = 1`.

### Step 4 - Apply Cardinality Constraint
- Add a single constraint: `sum(x[i] for i in N) == k`, where `k` is the required number of selected elements.

### Step 5 - Formulate Pairwise Sum Objective
- Define a parameter `d[i,j]` representing the pairwise contribution (e.g., distance, similarity, cost).
- Formulate the objective as `maximize sum(d[i,j] * z[i,j] for i in N for j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of candidate elements"
  ],
  "parameters": [
    "k: required number of selected elements (integer)",
    "d[i,j]: pairwise contribution value for ordered pair (i, j) where i != j"
  ],
  "decision_variables": [
    "x[i]: binary, 1 if element i is selected",
    "z[i,j]: binary, 1 if both i and j are selected (i != j)"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in N, j in N, i != j} d[i,j] * z[i,j]"
  },
  "constraints": [
    "cardinality: sum_{i in N} x[i] == k",
    "link_z_to_x_i: z[i,j] <= x[i] for all i, j in N, i != j",
    "link_z_to_x_j: z[i,j] <= x[j] for all i, j in N, i != j",
    "enforce_conjunction: z[i,j] >= x[i] + x[j] - 1 for all i, j in N, i != j"
  ]
}
```

### Common Pitfalls
- Creating `z[i,i]` variables for diagonal pairs, which are unnecessary and can complicate the model. Ensure `i != j`.
- Using asymmetric pairwise data `d[i,j]` when the problem context implies symmetry (e.g., distance). If symmetric, consider using `i < j` to reduce variable count.
- Over-constraining the model by adding redundant constraints beyond the standard linearization.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver via the `SolverFactory`. The focus is on robust solver configuration, explicit solution status checking, and verification of results.

### Step 1 - Configure Solver with Deterministic Settings
- Instantiate the solver (e.g., `SolverFactory("gurobi")`, `SolverFactory("highs")`).
- Set key options: a time limit, zero optimality gap tolerance for exact solutions, a fixed random seed for reproducibility, and thread count.
- Example: `solver.options["TimeLimit"] = 30`, `solver.options["MIPGap"] = 0.0`, `solver.options["Seed"] = 42`, `solver.options["Threads"] = 4`.

### Step 2 - Solve and Check Status
- Execute `results = solver.solve(model, tee=False)`.
- Check if the solver status is `SolverStatus.ok`.
- Check if the termination condition is `TerminationCondition.optimal` or `TerminationCondition.feasible`.

### Step 3 - Load and Extract Solution
- If status checks pass, load the solution: `model.solutions.load_from(results)`.
- Extract selected elements: `selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]`.
- Compute the objective value: `obj_val = pyo.value(model.obj)`.

### Step 4 - Verify Solution (Optional, for small instances)
- For validation, enumerate all `k`-combinations of elements.
- Calculate the objective for each combination by summing the relevant `d[i,j]` values.
- Confirm the solver's solution matches the best found via enumeration.

### Code Usage
```python
import pyomo.environ as pyo

# Assume `model` is built according to the modeling stage
solver = pyo.SolverFactory("highs")  # or "gurobi", "cplex"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4

results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    # Load solution before accessing values
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    print(f"RESULT:{obj_val}")
    print(f"Selected: {selected}")
else:
    # Handle failure
    error_payload = {"solver_status": str(status), "termination_condition": str(term)}
    print(f"ERROR:{error_payload}")
```

### Common Pitfalls
- Accessing variable values (`pyo.value`) before loading the solution, which raises an error. Always load the solution first.
- Setting an excessively low time limit or zero gap for large instances, causing the solver to fail to find a feasible solution.
- Forgetting to set a random seed, leading to non-reproducible results across runs.

# Workflow 2 (ORTools CP-SAT with Direct Multiplication)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which natively supports linear constraints and offers `AddMultiplicationEquality` to handle the product of binary variables without manually adding the three linearization constraints. This leads to a cleaner model.

### Step 1 - Define Core Selection Variables
- Create the CP-SAT model instance.
- For each element `i` in set `N`, create a binary variable `x[i]` using `model.NewBoolVar()`.

### Step 2 - Enforce Cardinality Constraint
- Use `model.Add(sum(x[i] for i in N) == k)` to enforce the exact selection count.

### Step 3 - Handle Pairwise Products for Objective
- For each relevant pair `(i, j)` (e.g., `i < j` for symmetric objectives), create an auxiliary variable `z[i,j]` using `model.NewBoolVar()`.
- Use `model.AddMultiplicationEquality(z[i,j], [x[i], x[j]])` to enforce `z[i,j] == x[i] * x[j]`. This single constraint replaces the three linear constraints used in Workflow 1.

### Step 4 - Formulate Linear Objective
- Define the objective as `maximize sum(d[i,j] * z[i,j] for all defined pairs)`.
- Use `model.Maximize()` to set the objective expression.

### Formulation Template
```json
{
  "sets": [
    "N: set of candidate elements"
  ],
  "parameters": [
    "k: required number of selected elements (integer)",
    "d[i,j]: pairwise contribution value for pair (i, j). For symmetric problems, can be defined for i < j."
  ],
  "decision_variables": [
    "x[i]: boolean CP-SAT variable",
    "z[i,j]: boolean CP-SAT variable representing x[i] * x[j]"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{defined pairs (i,j)} d[i,j] * z[i,j]"
  },
  "constraints": [
    "cardinality: sum_{i in N} x[i] == k",
    "product_relation: z[i,j] == x[i] * x[j] for all defined pairs (via AddMultiplicationEquality)"
  ]
}
```

### Common Pitfalls
- Manually adding the three linear constraints (`<=`, `<=`, `>=`) in CP-SAT, which is less efficient and more error-prone than using `AddMultiplicationEquality`.
- Defining `z` variables for all ordered pairs `(i, j)` when the objective is symmetric, unnecessarily doubling the variable count. Use `i < j` for symmetric `d`.
- Incorrectly using `model.NewIntVar` instead of `model.NewBoolVar` for binary variables.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver with appropriate parameters. The workflow emphasizes efficient solving and simple, robust result extraction due to CP-SAT's solution proto structure.

### Step 1 - Configure Solver Parameters
- Create a `CpSolverParameters()` object.
- Set parameters like `max_time_in_seconds`, `num_search_workers` (parallelism), and `random_seed` for reproducibility.
- For small instances, use default parameters or minimal configuration to avoid overhead.

### Step 2 - Solve and Check Status
- Instantiate `CpSolver()` and call `solver.Solve(model, parameters)`.
- Check the status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.

### Step 3 - Extract Solution
- If status is acceptable, iterate over `x[i]` variables: `selected = [i for i in N if solver.Value(x[i]) == 1]`.
- The objective value is obtained via `solver.ObjectiveValue()`.

### Step 4 - Optional Verification
- For small `N`, verify by enumerating combinations as in Workflow 1.

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Assume variables x and z are created, constraints and objective are added

solver = cp_model.CpSolver()
# Set parameters appropriately for problem size
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4  # Adjust based on available cores
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    obj_val = solver.ObjectiveValue()
    selected = [i for i in N if solver.Value(x[i]) == 1]
    print(f"RESULT:{obj_val}")
    print(f"Selected: {selected}")
else:
    # Handle failure
    error_payload = {"solver_status": status}
    print(f"ERROR:{error_payload}")
```

### Common Pitfalls
- Setting excessive parallelism (`num_search_workers`) for tiny problems, which can introduce overhead without benefit.
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when a time limit is reached.
- Assuming `solver.ObjectiveValue()` is valid for `FEASIBLE` status; it is, but only if an objective was set.
