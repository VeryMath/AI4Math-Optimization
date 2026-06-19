---
name: Cardinality-Constrained Pairwise Selection
description: |
  Model and solve combinatorial problems where exactly K elements are selected from a set, and the objective maximizes the sum of pairwise benefits between selected elements, using linearized binary variables for pairwise activation.
---

# Workflow 1 (CP-SAT for Exact Binary Optimization)

## Modeling stage

### Strategy Overview
Formulate the problem as a pure binary integer program using OR-Tools CP-SAT. The core modeling technique is the linearization of the product `x[i] * x[j]` via auxiliary binary variables and logical constraints, which CP-SAT handles natively and efficiently.

### Step 1 - Define Core Decision Variables
- Create a binary variable `x[i]` for each element `i` in the set `N` to represent its selection status.
- Create a binary variable `y[(i, j)]` for each ordered pair `(i, j)` in the set `P` (where `i != j`) to represent the activation of the pairwise interaction.

### Step 2 - Enforce Selection Cardinality
- Add a single linear equality constraint: `sum(x[i] for i in N) == K`. This ensures exactly `K` elements are selected.

### Step 3 - Link Selection and Pairwise Activation
- For each ordered pair `(i, j)`, add three linear constraints to enforce `y[(i, j)] == x[i] * x[j]`:
  - `y[(i, j)] <= x[i]` (activation requires the first element selected).
  - `y[(i, j)] <= x[j]` (activation requires the second element selected).
  - `y[(i, j)] >= x[i] + x[j] - 1` (activation is mandatory if both elements are selected).

### Step 4 - Formulate the Objective
- Define the objective as `maximize sum(benefit[(i, j)] * y[(i, j)] for (i, j) in P)`, where `benefit` is a given parameter for each directed pair.

### Formulation Template
```json
{
  "sets": [
    "N: Set of elements (e.g., nodes, items).",
    "P: Set of ordered pairs (i, j) where i, j ∈ N and i ≠ j."
  ],
  "parameters": [
    "K: Integer, the exact number of elements to select.",
    "benefit[(i, j)]: Numeric weight (can be positive or negative) for the directed pair (i, j)."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}, ∀ i ∈ N. 1 if element i is selected.",
    "y[(i, j)] ∈ {0, 1}, ∀ (i, j) ∈ P. 1 if the pairwise interaction is active."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{ (i,j) ∈ P } benefit[(i, j)] * y[(i, j)]"
  },
  "constraints": [
    "cardinality: sum_{ i ∈ N } x[i] = K",
    "activation_lower_bound: y[(i, j)] ≤ x[i], ∀ (i, j) ∈ P",
    "activation_lower_bound_2: y[(i, j)] ≤ x[j], ∀ (i, j) ∈ P",
    "activation_upper_bound: y[(i, j)] ≥ x[i] + x[j] - 1, ∀ (i, j) ∈ P"
  ]
}
```

### Common Pitfalls
- Forgetting to define `y` for *ordered* pairs when benefits are asymmetric, which leads to an incorrect objective.
- Applying the linearization constraints to unordered pairs without adjusting the objective, potentially double-counting or missing benefits.
- Not verifying that the `benefit` parameter is defined for all pairs in `P`; missing keys will cause an error during model construction.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver, configured for deterministic and efficient search on binary combinatorial problems. The workflow includes explicit solver parameter tuning, solution verification, and a fallback validation method for small instances.

### Step 1 - Instantiate Model and Variables
- Create a `CpModel()` object.
- Use dictionaries to store `x` and `y` variables, creating them with `model.NewBoolVar(f"x_{i}")` and `model.NewBoolVar(f"y_{i}_{j}")` for traceability.

### Step 2 - Add Constraints and Objective
- Translate the formulation constraints directly using the model's `Add()` method and linear expression capabilities.
- Set the objective with `model.Maximize()`.

### Step 3 - Configure and Execute the Solver
- Instantiate a `CpSolver()`.
- Set key parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = [NUM_WORKERS]`, `solver.parameters.random_seed = [SEED]`. For optimality proof, set `solver.parameters.relative_gap_limit = 0.0`.
- Call `solver.Solve(model)` and capture the status.

### Step 4 - Extract and Verify Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- Extract the selected set: `selected = [i for i in N if solver.Value(x[i]) == 1]`.
- Verify cardinality constraint: `len(selected) == K`.
- For small `N` (e.g., |N| ≤ 20), optionally validate optimality via brute-force enumeration over all `K`-combinations to confirm the solver's solution value.
- **Manually compute the realized objective** by summing `benefit[(i,j)]` for all pairs within the selected set to validate against `solver.ObjectiveValue()`.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model
model = cp_model.CpModel()

# Variable creation
x = {i: model.NewBoolVar(f"x_{i}") for i in N}
y = {(i, j): model.NewBoolVar(f"y_{i}_{j}") for (i, j) in P}

# Cardinality constraint
model.Add(sum(x[i] for i in N) == K)

# Pairwise consistency constraints
for (i, j) in P:
    model.Add(y[(i, j)] <= x[i])
    model.Add(y[(i, j)] <= x[j])
    model.Add(y[(i, j)] >= x[i] + x[j] - 1)

# Objective
model.Maximize(sum(benefit[(i, j)] * y[(i, j)] for (i, j) in P))

# solve with status / termination checks
solver = cp_model.CpSolver()
# Set parameters (e.g., solver.parameters.max_time_in_seconds = [TIME_LIMIT])
solver.parameters.num_search_workers = [NUM_WORKERS]  # parallelize
solver.parameters.random_seed = [SEED]
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in N if solver.Value(x[i]) == 1]
    objective_value = solver.ObjectiveValue()
    # Further processing...
else:
    # Handle no solution found
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting a `max_time_in_seconds` for large instances, risking excessively long runs.
- Misinterpreting the `status`; `FEASIBLE` does not guarantee optimality unless a time or gap limit was set.
- Attempting to use `solver.Value()` on a variable before checking the solver status, which may cause errors.

# Workflow 2 (Pyomo with MILP Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling constructs. This approach provides solver-agnostic flexibility and explicit set-based definitions, suitable for integration with commercial (e.g., Gurobi) or open-source (e.g., HiGHS) solvers.

### Step 1 - Declare Model and Sets
- Instantiate a `ConcreteModel()` or `AbstractModel()`.
- Define Pyomo `Set` objects for the elements `model.N` and the ordered pairs `model.P`.

### Step 2 - Define Parameters and Variables
- Declare `Param` for `benefit` indexed over `model.P`.
- Declare binary `Var` for selection (`model.x`, indexed over `model.N`) and pairwise activation (`model.y`, indexed over `model.P`).

### Step 3 - Construct Constraints via Rules
- Define a `Constraint` rule for the cardinality constraint: `sum(model.x[i] for i in model.N) == K`.
- For each pair in `model.P`, define three constraints using rules or a `ConstraintList` to implement the linearization: `model.y[i,j] <= model.x[i]`, `model.y[i,j] <= model.x[j]`, `model.y[i,j] >= model.x[i] + model.x[j] - 1`.

### Step 4 - Define the Objective
- Use an `Objective` rule: `maximize sum(model.benefit[i,j] * model.y[i,j] for (i,j) in model.P)`.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of elements.",
    "P: Pyomo Set of ordered pairs (i, j), a subset of N × N with i ≠ j."
  ],
  "parameters": [
    "K: Integer, cardinality requirement.",
    "benefit[i,j]: Pyomo Param defined over P, representing the directed pairwise weight."
  ],
  "decision_variables": [
    "x[i]: Pyomo Var (domain=Binary), ∀ i ∈ N.",
    "y[i,j]: Pyomo Var (domain=Binary), ∀ (i, j) ∈ P."
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( benefit[i,j] * y[i,j] for (i,j) in P )"
  },
  "constraints": [
    "cardinality_rule: sum( x[i] for i in N ) == K",
    "link1_rule: y[i,j] <= x[i], ∀ (i,j) ∈ P",
    "link2_rule: y[i,j] <= x[j], ∀ (i,j) ∈ P",
    "link3_rule: y[i,j] >= x[i] + x[j] - 1, ∀ (i,j) ∈ P"
  ]
}
```

### Common Pitfalls
- Defining the set `P` as unordered pairs (`i < j`) but using it with an asymmetric `benefit` parameter, leading to key errors or incorrect objective calculation.
- Using an `AbstractModel` without properly initializing all parameters via a data file or dictionary before instantiation, causing runtime errors.
- Creating overly complex constraint rules that perform unnecessary computations, slowing down model construction for large `N`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver interface (e.g., Gurobi, HiGHS). The workflow emphasizes robust solver configuration, careful handling of solution loading, and post-solution verification to ensure correctness and manage numerical precision.

### Step 1 - Instantiate Solver and Set Options
- Use `SolverFactory('solver_name')` (e.g., `'gurobi'`, `'highs'`).
- Pass solver options via `options_dict` or keyword arguments (e.g., `TimeLimit=[TIME_LIMIT]`, `MIPGap=0.0` for optimality, `Threads=[NUM_THREADS]`, `Seed=[SEED]`). For HiGHS, note that `threads` may be set via a different option.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=False)`.
- Always check the solver status (`results.solver.status`) and termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` as successful.

### Step 3 - Load and Extract Solution
- If the solve was successful, load the solution into the model. For robustness, especially with HiGHS, use `model.solutions.load_from(results)`.
- Extract selected elements: `selected = [i for i in model.N if value(model.x[i]) > 0.5]`.
- **Manually compute the realized objective** by summing `benefit[i,j]` for pairs where both corresponding `x` variables are 1, to verify against the solver's reported objective value.

### Step 4 - Validate Model Constraints
- Programmatically verify the cardinality constraint: `len(selected) == K`.
- Verify pairwise consistency: for all `(i,j)` in `P`, check that `value(model.y[i,j])` equals `value(model.x[i]) * value(model.x[j])` within a small tolerance.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()

# Sets
model.N = pyo.Set(initialize=N_set)
model.P = pyo.Set(initialize=P_set, dimen=2)

# Parameters
model.K = pyo.Param(initialize=K, mutable=True)
model.benefit = pyo.Param(model.P, initialize=benefit_dict)

# Variables
model.x = pyo.Var(model.N, domain=pyo.Binary)
model.y = pyo.Var(model.P, domain=pyo.Binary)

# Objective
def obj_rule(m):
    return sum(m.benefit[i, j] * m.y[i, j] for (i, j) in m.P)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# Constraints
def cardinality_rule(m):
    return sum(m.x[i] for i in m.N) == m.K
model.cardinality = pyo.Constraint(rule=cardinality_rule)

def link_rule1(m, i, j):
    return m.y[i, j] <= m.x[i]
model.link1 = pyo.Constraint(model.P, rule=link_rule1)

def link_rule2(m, i, j):
    return m.y[i, j] <= m.x[j]
model.link2 = pyo.Constraint(model.P, rule=link_rule2)

def link_rule3(m, i, j):
    return m.y[i, j] >= m.x[i] + m.x[j] - 1
model.link3 = pyo.Constraint(model.P, rule=link_rule3)

# solve with status / termination checks
solver = pyo.SolverFactory('solver_name')  # e.g., 'gurobi'
solver_options = {'TimeLimit': [TIME_LIMIT], 'MIPGap': 0.0}
results = solver.solve(model, options=solver_options)

# Check status
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    pyo.SolverFactory('solver_name').load_solutions(results, model)
    selected = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    # Further processing...
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print("Feasible solution found, but not proven optimal.")
    # Load solution and proceed with caution
else:
    print("Solver failed to find a feasible solution.")
```

### Common Pitfalls
- Assuming `pyo.value()` can be called immediately after `solve()` without checking status or loading the solution, leading to `ValueError` or stale variable values.
- Ignoring numerical precision: comparing floating-point objective values directly for equality; use a tolerance or recalculate using integer arithmetic on the selected set.
- For HiGHS, setting the `threads` option when the solver is already multi-threaded via environment variables, which can cause conflicts or ignored parameters.
