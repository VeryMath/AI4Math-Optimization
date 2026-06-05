---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set covering problems with binary selection variables, coverage constraints, and fixed-cost minimization using either CP-SAT or MILP frameworks.
---

# Workflow 1 (CP-SAT for Exact Binary Optimization)

## Modeling stage

### Strategy Overview
Use OR-Tools CP-SAT, a constraint programming solver optimized for binary integer problems. It is ideal for pure set covering where all variables are Boolean and an exact optimal solution is required.

### Step 1 - Define Problem Structure
- Identify the collection of selectable items (sets) and the elements that must be covered.
- Map the coverage relationship: for each element, list all items that can cover it. This dictionary mapping is more efficient than a full incidence matrix.
- Define a fixed cost for selecting each item.
- For each element, specify a minimum coverage requirement (default 1).

### Step 2 - Build CP-SAT Model
- Instantiate a `CpModel` object.
- Create one binary decision variable (`NewBoolVar`) for each selectable item.
- Formulate the linear cost objective: minimize the sum of selection costs.
- Add coverage constraints: for each element, the sum of its covering variables must be at least the required minimum coverage count.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., facilities, locations).",
    "J: Set of elements that must be covered (e.g., zones, requirements)."
  ],
  "parameters": [
    "cost_i: Fixed cost of selecting item i ∈ I.",
    "cover_j: List of items i ∈ I that can cover element j ∈ J.",
    "min_coverage_j: Minimum number of covering items required for element j ∈ J (default 1)."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1}: 1 if item i is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{i ∈ I} cost_i * x_i"
  },
  "constraints": [
    "Coverage: ∑_{i ∈ cover_j} x_i ≥ min_coverage_j, ∀ j ∈ J"
  ]
}
```

### Common Pitfalls
- Forgetting to map coverage for all elements, leading to missing constraints.
- Using integer variables instead of Boolean variables, which reduces solver efficiency.
- Not verifying that the coverage mapping is correct (e.g., an element with an empty covering list makes the problem infeasible).

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with parameters for deterministic performance and time management. Extract and rigorously verify the solution against the original coverage requirements.

### Step 1 - Configure Solver
- Create a `CpSolver` instance.
- Set a time limit (`max_time_in_seconds`) to prevent excessive runtime.
- Enable parallel search (`num_search_workers`) for speed.
- Set a random seed (`random_seed`) for reproducibility.
- Set the relative optimality gap to zero (`relative_gap_limit = 0.0`) for an exact solution.

### Step 2 - Solve and Validate
- Call `solver.Solve(model)` and capture the status.
- If status is `OPTIMAL` or `FEASIBLE`, extract selected items where the variable value equals 1.
- **Programmatically verify coverage**: For each element, check that the number of selected covering items meets or exceeds its minimum coverage requirement.
- Compute the total cost from the extracted solution for output consistency.
- **Optionally check minimality**: Test if any selected item can be removed while still satisfying all coverage constraints; this can reveal trivial suboptimality.

### Code Usage
```python
from ortools.sat.python import cp_model

# 1. Define data (placeholders)
costs = {i: cost_value for i in items}  # item -> cost
coverage = {j: (min_cov, [list_of_covering_items]) for j in elements}  # element -> (min_coverage, covering items)

# 2. Build Model
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in items}

# Objective
model.Minimize(sum(costs[i] * x[i] for i in items))

# Coverage Constraints
for j, (min_cov, covering_items) in coverage.items():
    model.Add(sum(x[i] for i in covering_items) >= min_cov)

# 3. Configure and Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [NUM_WORKERS]
solver.parameters.random_seed = [RANDOM_SEED]
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

# 4. Extract and Verify
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in items if solver.Value(x[i]) == 1]
    total_cost = sum(costs[i] for i in selected)
    
    # Verification
    for j, (min_cov, covering_items) in coverage.items():
        if sum(1 for i in selected if i in covering_items) < min_cov:
            raise AssertionError(f"Element {j} is not sufficiently covered.")
    # Output results (e.g., as JSON)
```

### Common Pitfalls
- Not checking for `FEASIBLE` status, which may provide a valid but suboptimal solution if time runs out.
- Assuming solver status `OPTIMAL` guarantees coverage without explicit verification.
- Using floating-point arithmetic for cost summation in verification; use integer costs or exact types if possible.

# Workflow 2 (Pyomo MILP with Open-Source Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo, an algebraic modeling language, to formulate the set cover as a Mixed-Integer Linear Program (MILP). It connects to solvers like HiGHS or CBC, offering flexibility and detailed model inspection.

### Step 1 - Structure Model with Sets
- Define Pyomo `Set` objects for the indices of items and elements.
- Declare cost and coverage as parameters, typically using Python dictionaries.
- Create binary decision variables (`Var(domain=Binary)`) for each item.

### Step 2 - Formulate Objective and Constraints
- Define the objective function as a `sum` of cost times variable.
- Implement coverage constraints via a `Constraint` rule that iterates over elements, ensuring the sum of relevant variables is at least the required minimum coverage count.

### Formulation Template
```json
{
  "sets": [
    "I: Pyomo Set of selectable items.",
    "J: Pyomo Set of elements to cover."
  ],
  "parameters": [
    "cost: Pyomo Param or dict, cost[i] for i ∈ I.",
    "cover: Dict, cover[j] = (min_coverage, list_of_covering_items) for each j ∈ J."
  ],
  "decision_variables": [
    "x[i] ∈ {0, 1}: Pyomo Var with domain=Binary."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "Coverage: sum(x[i] for i in cover[j][1]) >= cover[j][0], for each j in J"
  ]
}
```

### Common Pitfalls
- Defining Pyomo sets with incorrect initialization, leading to indexing errors.
- Using mutable default arguments (like `[]`) in constraint rule functions.
- Not separating model data from model structure, reducing reusability.

## Solving stage

### Strategy Overview
Instantiate a solver via Pyomo's `SolverFactory`, configure it for performance and exact solutions, solve, and then check termination conditions before extracting and validating results.

### Step 1 - Configure and Execute Solver
- Create a solver object (e.g., `SolverFactory("highs")` or `SolverFactory("cbc")`).
- Set key options: time limit (`time_limit`), optimality gap (`mip_rel_gap=0.0`), and threads (`threads`).
- Call `solver.solve(model, tee=False)` and capture the results object.

### Step 2 - Process and Verify Solution
- Check that the solver status is `ok` and the termination condition is `optimal` or `feasible`.
- Extract selected items by iterating over variables where `value(x[i]) > 0.5`.
- **Verify coverage** by checking each element against the selected items.
- Compute the objective value from the model or the results.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Define data (placeholders)
cost_data = {i: cost_value for i in items}
coverage_data = {j: (min_cov, [list_of_covering_items]) for j in elements}

# 2. Build Pyomo Concrete Model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)
model.cost = pyo.Param(model.I, initialize=cost_data)
model.x = pyo.Var(model.I, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[i] * model.x[i] for i in model.I),
    sense=pyo.minimize
)

# Coverage Constraints
def cover_rule(m, j):
    min_cov, covering_items = coverage_data[j]
    return sum(m.x[i] for i in covering_items) >= min_cov
model.cover = pyo.Constraint(model.J, rule=cover_rule)

# 3. Solve
solver = pyo.SolverFactory("[SOLVER_NAME]")  # e.g., "highs" or "cbc"
solver_options = {
    "time_limit": [TIME_LIMIT],
    "mip_rel_gap": 0.0,
    "threads": [NUM_THREADS]
}
results = solver.solve(model, options=solver_options, tee=False)

# 4. Check Status and Extract
status_ok = results.solver.status == SolverStatus.ok
term_acceptable = results.solver.termination_condition in (
    TerminationCondition.optimal, TerminationCondition.feasible
)

if status_ok and term_acceptable:
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_cost = pyo.value(model.obj)
    
    # Verification
    for j in model.J:
        min_cov, covering_items = coverage_data[j]
        if sum(1 for i in selected if i in covering_items) < min_cov:
            raise AssertionError(f"Element {j} is not sufficiently covered.")
    # Output results (e.g., as JSON)
```

### Common Pitfalls
- Confusing solver status (`ok`) with termination condition (`optimal`); both must be checked.
- Using `pyo.value()` on an uninitialized variable if the solve failed.
- Not setting `mip_rel_gap=0.0`, which may allow early stopping with a suboptimal solution.
