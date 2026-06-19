---
name: BinarySelectionMaximinDistance
description: |
  Model and solve binary selection problems with pairwise activation constraints to maximize the minimum distance (or other pairwise metric) among selected items, using either a direct CP-SAT or a Pyomo-based MILP approach.

---
# Workflow 1 (CP-SAT Direct Formulation)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' CP-SAT solver directly. It is ideal for problems with purely binary and logical constraints, offering a concise API for variable creation, constraint addition, and objective definition without an intermediate algebraic modeling layer.

### Step 1 - Define Core Selection Variables
- Create a binary decision variable `x[i]` for each candidate item `i` in the set `N`. This variable equals 1 if the item is selected.
- Use `model.NewBoolVar(f"x_{i}")` to instantiate each variable.

### Step 2 - Define Pair Activation Variables
- For each unordered pair `(i, j)` where `i < j`, create an auxiliary binary variable `y[(i, j)]`.
- This variable indicates whether both items `i` and `j` are selected. Use `model.NewBoolVar(f"y_{i}_{j}")`.

### Step 3 - Link Pair Activation to Selection
- Add logical constraints to enforce `y[(i, j)] = 1` if and only if `x[i] = 1` and `x[j] = 1`.
- Implement with three linear constraints per pair:
    - `y[(i, j)] <= x[i]`
    - `y[(i, j)] <= x[j]`
    - `y[(i, j)] >= x[i] + x[j] - 1`

### Step 4 - Enforce Selection Cardinality
- Add a single linear constraint to select exactly `K` items: `sum(x[i] for i in N) == K`.

### Step 5 - Formulate Maximin Objective
- Introduce a continuous variable `z` to represent the minimum distance among selected pairs. Define it with appropriate bounds, e.g., `model.NewNumVar(0, M, "z")`.
- For each pair `(i, j)`, add a conditional lower bound constraint using a big-M formulation: `z <= distance[i][j] + M * (1 - y[(i, j)])`.
- The constant `M` must be larger than any possible pairwise distance to deactivate the constraint when the pair is not selected (`y=0`). A safe choice is `max(distance) * 1.1` or a fixed large value like `1e6`.
- Set the objective to maximize `z`.

### Formulation Template
```json
{
  "sets": [
    "N: Set of candidate items.",
    "P: Set of unordered pairs (i, j) where i, j in N and i < j."
  ],
  "parameters": [
    "distance[i][j]: Non-negative distance (or metric) for pair (i, j).",
    "K: Exact number of items to select (integer).",
    "M: A sufficiently large constant (e.g., max(distance) * 2)."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}, ∀ i ∈ N. Selection indicator.",
    "y[(i, j)] ∈ {0, 1}, ∀ (i, j) ∈ P. Pair activation indicator.",
    "z ∈ [0, M]. Continuous variable for the minimum distance."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "sum(x[i] for i in N) == K",
    "y[(i, j)] <= x[i], ∀ (i, j) ∈ P",
    "y[(i, j)] <= x[j], ∀ (i, j) ∈ P",
    "y[(i, j)] >= x[i] + x[j] - 1, ∀ (i, j) ∈ P",
    "z <= distance[i][j] + M * (1 - y[(i, j)]), ∀ (i, j) ∈ P"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which can cut off valid solutions. Calculate it as `max(distance) * 1.1` or a fixed large value like `1e6`.
- Forgetting to define the pair set `P` for unordered pairs, leading to duplicate variables and constraints for `(i, j)` and `(j, i)`.
- Not handling the trivial case where `K < 2`. The model is still valid, but `z` may be unbounded. Consider adding a constraint `sum(y) >= 1` if `K >= 2` is guaranteed.

## Solving stage

### Strategy Overview
Solve the model using the CP-SAT solver, which is designed for linear constraints over Boolean and integer variables. Configure solver parameters for performance and reliability, then extract and validate the solution.

### Step 1 - Instantiate Solver and Configure
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set key parameters to control the search:
    - `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`
    - `solver.parameters.num_search_workers = [NUM_CORES]`
    - `solver.parameters.random_seed = [SEED]` for reproducibility.
    - For an exact solution, ensure `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Execute Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check the result status against `cp_model.OPTIMAL`, `cp_model.FEASIBLE`, `cp_model.INFEASIBLE`, or `cp_model.UNKNOWN`.
- **Prerequisite Check:** If the status is not `OPTIMAL` or `FEASIBLE`, do not proceed to solution extraction. Handle the failure (e.g., log status, return empty solution).

### Step 3 - Extract and Post-process Solution
- If the solve was successful, retrieve the objective value: `obj_val = solver.ObjectiveValue()`.
- Extract selected items by checking `solver.Value(x_var) == 1` for each `x` variable.
- Optionally, extract active pairs by checking `solver.Value(y_var) == 1`.
- Package the solution (selected indices, objective value, solver status) into a structured output (e.g., a dictionary).

### Code Usage
```python
# build model from formulation
import ortools.sat.python.cp_model as cp

model = cp.CpModel()
# ... (build variables and constraints as per Modeling Stage)

# solve with status / termination checks
solver = cp.CpSolver()
# Apply configuration
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in (cp.OPTIMAL, cp.FEASIBLE):
    selected_items = [i for i, var in x_vars.items() if solver.Value(var) == 1]
    min_distance = solver.ObjectiveValue()
    solution = {
        "status": "OPTIMAL" if status == cp.OPTIMAL else "FEASIBLE",
        "objective": min_distance,
        "selected": selected_items
    }
else:
    # Do not output pseudo numeric answers when execution fails.
    solution = {
        "status": "INFEASIBLE" if status == cp.INFEASIBLE else "UNKNOWN",
        "objective": None,
        "selected": []
    }
print(solution)
```

### Common Pitfalls
- Assuming `solver.Value(var)` is valid without checking the solve status first, which can cause runtime errors.
- Not setting a time limit for large instances, potentially causing the solver to run indefinitely.
- Misinterpreting `FEASIBLE` as `OPTIMAL`; for reporting, distinguish between proven optimal and heuristic solutions.

# Workflow 2 (Pyomo MILP with External Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the problem as a Mixed-Integer Linear Program (MILP). It separates the model definition from the solver interface, allowing flexibility to use various solvers (e.g., Gurobi, SCIP, CBC) and enabling more complex model extensions.

### Step 1 - Define Abstract Sets and Parameters
- Declare an abstract Pyomo `Set` for candidate items `model.N`.
- Declare a `Set` for unordered pairs `model.P`, defined as a subset of `model.N × model.N` with `i < j`.
- Declare `Param` for distances `model.dist` indexed over `model.P` and the selection count `model.K`.

### Step 2 - Define Decision Variables
- Create binary selection variables: `model.x = Var(model.N, within=Binary)`.
- Create binary pair activation variables: `model.y = Var(model.P, within=Binary)`.
- Create a continuous variable for the minimum distance: `model.z = Var(within=NonNegativeReals, bounds=(0, M))`.

### Step 3 - Enforce Logical and Cardinality Constraints
- Add the cardinality constraint: `sum(model.x[i] for i in model.N) == model.K`.
- For each pair in `model.P`, add the three linking constraints using Pyomo's `Constraint` construct.
- Use a `ConstraintList` or a rule-based `Constraint` for efficient generation.

### Step 4 - Implement Maximin via Big-M Constraints
- For each pair `(i, j)` in `model.P`, add constraint: `model.z <= model.dist[i, j] + M * (1 - model.y[i, j])`.
- This ensures `model.z` is bounded by the distance of every active pair.

### Step 5 - Define the Objective
- Set the objective to maximize `model.z`: `model.obj = Objective(expr=model.z, sense=maximize)`.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of candidate items.",
    "P: Pyomo Set of unordered pairs (i, j) where i, j in N and i < j."
  ],
  "parameters": [
    "dist[i, j]: Pyomo Param for distance, indexed over P.",
    "K: Pyomo Param (or scalar) for the number of items to select.",
    "M: Scalar large constant for big-M constraints."
  ],
  "decision_variables": [
    "x[i]: Pyomo Var, within=Binary, ∀ i ∈ N.",
    "y[i, j]: Pyomo Var, within=Binary, ∀ (i, j) ∈ P.",
    "z: Pyomo Var, within=NonNegativeReals."
  ],
  "objective": {
    "sense": "max",
    "expression": "z"
  },
  "constraints": [
    "cardinality: sum(x[i] for i in N) == K",
    "link_lower_i: y[i, j] <= x[i], ∀ (i, j) ∈ P",
    "link_lower_j: y[i, j] <= x[j], ∀ (i, j) ∈ P",
    "link_upper: y[i, j] >= x[i] + x[j] - 1, ∀ (i, j) ∈ P",
    "min_distance: z <= dist[i, j] + M * (1 - y[i, j]), ∀ (i, j) ∈ P"
  ]
}
```

### Common Pitfalls
- Defining the pair set `P` incorrectly, leading to key errors when accessing `dist[i, j]`. Ensure it aligns with the distance dictionary's keys.
- Using a mutable default argument (like a list) in Pyomo constraint rules; define rules with explicit function signatures.
- Forgetting to deactivate the big-M constraint for inactive pairs by setting `M` large enough; otherwise, `z` may be incorrectly constrained.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with an external MILP solver (e.g., Gurobi, SCIP, CBC). Configure solver-specific options for performance, then solve and rigorously check the termination condition before extracting results.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object: `solver = SolverFactory('SOLVER_NAME')` (e.g., `'gurobi'`, `'scip'`, `'cbc'`).
- Set solver options to control the optimization:
    - Time limit: `solver.options['TimeLimit'] = [TIME_LIMIT]`
    - Optimality gap tolerance: `solver.options['MIPGap'] = 0.0` for exact solution.
    - Thread count: `solver.options['Threads'] = [NUM_CORES]`
    - Random seed for reproducibility, if supported.

### Step 2 - Solve and Check Termination Status
- Execute the solve: `results = solver.solve(model, tee=False)`.
- Check the high-level solver status: `status = results.solver.status`.
- Check the detailed termination condition: `term = results.solver.termination_condition`.
- **Prerequisite Check:** A successful solve requires `status == SolverStatus.ok` and `term` in `{TerminationCondition.optimal, TerminationCondition.feasible}`. Do not trust non-zero return codes or infeasible/unknown statuses.

### Step 3 - Extract and Validate Solution
- If the solve was successful, access the objective value: `obj_val = model.obj()`.
- Extract selected items by evaluating `value(model.x[i]) > 0.5`.
- For verification, compute the actual minimum distance among selected items using the original distance data to ensure it matches `obj_val`.
- Return the solution in a structured format.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
# ... (build sets, params, variables, constraints, objective as per Modeling Stage)

# solve with status / termination checks
solver = pyo.SolverFactory('scip')  # Example with SCIP
solver.options['limits/time'] = 30
solver.options['limits/gap'] = 0.0

results = solver.solve(model, tee=False)

from pyomo.opt import SolverStatus, TerminationCondition
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected_items = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    min_distance = pyo.value(model.z)
    solution = {
        "status": "OPTIMAL" if term == TerminationCondition.optimal else "FEASIBLE",
        "objective": min_distance,
        "selected": selected_items
    }
else:
    # Do not output pseudo numeric answers when execution fails.
    solution = {
        "status": str(term),
        "objective": None,
        "selected": []
    }
print(solution)
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, which can lead to extracting invalid solutions from interrupted or infeasible runs.
- Assuming variable values are loaded automatically; after solving, Pyomo automatically loads the solution into the model object.
- Using `tee=True` in production code, which prints extensive solver logs; reserve it for debugging.
