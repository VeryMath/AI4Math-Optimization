---
name: Set Cover Cost Minimization
description: |
  Model and solve binary set cover problems with linear costs using either a direct matrix formulation or a sparse coverage mapping, and implement robust solving with verification.
---

# Workflow 1 (Direct Matrix Formulation with Pyomo)

## Modeling stage

### Strategy Overview
Model the set cover problem using an explicit binary coverage matrix parameter within a Pyomo `ConcreteModel`. This approach is well-suited for structured data and provides a clear mathematical representation of the coverage relationship between items and elements.

### Step 1 - Define Index Sets
- Identify and create Pyomo `Set` objects for the collection of selectable items (e.g., packages) and the elements that require coverage (e.g., zones).
- Use these sets to index all model components, ensuring clean and scalable constraint generation.

### Step 2 - Define Parameters
- Define a `Param` for item costs, indexed by the item set.
- Define a binary `Param` for the coverage matrix, indexed by (element, item). This parameter should be 1 if the item covers the element, and 0 otherwise. Use a rule for efficient sparse initialization.

### Step 3 - Define Decision Variables
- Create a binary decision variable `x[i]` for each item `i`, where `x[i] = 1` indicates the item is selected.

### Step 4 - Formulate Objective and Constraints
- Formulate the objective to minimize the total cost: `min sum(cost[i] * x[i] for i in items)`.
- For each element, create a coverage constraint: `sum(coverage_matrix[element, i] * x[i] for i in items) >= 1`. This ensures at least one covering item is selected per element.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items.",
    "S: Set of elements to be covered."
  ],
  "parameters": [
    "cost[i ∈ I]: Cost of selecting item i.",
    "cover[s ∈ S, i ∈ I]: Binary parameter, 1 if item i covers element s."
  ],
  "decision_variables": [
    "x[i ∈ I]: Binary, 1 if item i is selected."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "Coverage[s ∈ S]: sum(cover[s, i] * x[i] for i in I) >= 1"
  ]
}
```

### Common Pitfalls
- Inefficiently initializing a dense coverage matrix for sparse problems, leading to memory overhead.
- Forgetting to verify that the coverage matrix correctly maps to the problem's 1-indexed or 0-indexed data.
- Defining constraints over incorrect index sets, which can silently produce an infeasible or incorrect model.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver (e.g., Gurobi, HiGHS, CBC) with robust error handling. Implement a fallback strategy for solver failures and always verify the feasibility of the returned solution.

### Step 1 - Configure Solver and Solve
- Instantiate the solver via `SolverFactory`.
- Set key parameters: a time limit, optimality gap (e.g., 0.0 for proven optimum), number of threads, and a random seed for reproducibility.
- Solve the model with `load_solutions=False` to first check the termination status without risking a crash on infeasibility.

### Step 2 - Check Solver Status and Load Solution
- Check the solver termination condition. Accept statuses corresponding to `optimal` or `feasible`.
- If the status is acceptable, load the solution into the model instance.
- If the primary solver fails (e.g., `NoFeasibleSolutionError`), log the error and attempt with a secondary, more robust solver (e.g., switch from HiGHS to GLPK).

### Step 3 - Extract and Verify Solution
- Extract selected items by filtering variables where `value(x[i]) > 0.5`.
- Calculate the objective value.
- Implement a verification loop: for each element, check if at least one selected item has `cover[element, item] == 1`. Flag any uncovered elements.

### Step 4 - Structure Output
- Return results in a standardized dictionary or JSON format, including solver status, objective value, list of selected items, and a verification success flag.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.S = pyo.Set(initialize=elements)
model.cost = pyo.Param(model.I, initialize=cost_dict)
model.cover = pyo.Param(model.S, model.I, initialize=coverage_rule)
model.x = pyo.Var(model.I, domain=pyo.Binary)
model.obj = pyo.Objective(expr=sum(model.cost[i] * model.x[i] for i in model.I), sense=pyo.minimize)
model.coverage = pyo.Constraint(model.S, rule=lambda m, s: sum(m.cover[s, i] * m.x[i] for i in m.I) >= 1)

# Solve with status / termination checks
solver_name = 'highs'
solver = pyo.SolverFactory(solver_name)
solver.options['time_limit'] = 30
solver.options['mip_gap'] = 0.0

results = solver.solve(model, load_solutions=False, tee=False)

status = results.solver.termination_condition
acceptable_status = {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}

if status in acceptable_status:
    model.solutions.load_from(results)
    # Extract solution...
else:
    # Fallback to another solver, e.g., 'glpk'
    pass
```

### Common Pitfalls
- Loading solutions without checking status first, which can cause exceptions on infeasible models.
- Not implementing a solver fallback, leaving the workflow brittle to specific solver issues.
- Assuming the solver's feasibility report is correct without implementing independent verification.

# Workflow 2 (Sparse Mapping Formulation with OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Model the set cover problem using a sparse representation of coverage relationships, mapping each element to a list of items that cover it. This approach is efficient for problems where the coverage matrix is very sparse and aligns naturally with the OR-Tools CP-SAT API.

### Step 1 - Prepare Sparse Coverage Data
- Represent coverage not as a matrix, but as a dictionary or list-of-lists: `coverage_sets[element_index] = [item_index1, item_index2, ...]`.
- Ensure all indices are converted to 0-based for use in Python/OR-Tools if the source data is 1-based.

### Step 2 - Define Model and Variables
- Instantiate a `cp_model.CpModel()`.
- Create a list of Boolean decision variables `x[i]` for each item `i`, using `model.NewBoolVar()`.

### Step 3 - Formulate Objective and Constraints
- Formulate the linear objective: `min sum(cost[i] * x[i] for i in items)`. In CP-SAT, use `AddLinearExpression` with the `Minimize` method.
- For each element, create a coverage constraint: `sum(x[i] for i in coverage_sets[element]) >= 1`. Use `model.Add(sum(element_vars) >= 1)`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (0-indexed).",
    "S: Set of elements to be covered (0-indexed)."
  ],
  "parameters": [
    "cost[i ∈ I]: Integer or linear cost of selecting item i.",
    "covers[s ∈ S]: List of item indices in I that cover element s."
  ],
  "decision_variables": [
    "x[i ∈ I]: Boolean CP-SAT variable."
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i] * x[i] for i in I)"
  },
  "constraints": [
    "Coverage[s ∈ S]: sum(x[i] for i in covers[s]) >= 1"
  ]
}
```

### Common Pitfalls
- Using floating-point costs with CP-SAT, which requires integer or linearized expressions. Scale costs to integers if necessary.
- Incorrectly mapping 1-indexed problem data to 0-indexed Python lists, leading to index errors or wrong coverage.
- Forgetting that CP-SAT's `BoolVar` is not a Python `bool` and must be evaluated with `solver.Value()`.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured parameters for deterministic and efficient search. Extract the solution and perform an independent verification of coverage constraints.

### Step 1 - Configure and Run Solver
- Instantiate `cp_model.CpSolver()`.
- Set key parameters: `max_time_in_seconds`, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit` (e.g., 0.0 for optimality).
- Execute the solver with `solver.Solve(model)` and capture the status code.

### Step 2 - Interpret Status and Extract Solution
- Check if the status is `OPTIMAL` or `FEASIBLE`.
- If acceptable, extract selected items by iterating over variables where `solver.Value(x[i]) == 1`.
- Retrieve the objective value via `solver.ObjectiveValue()`.

### Step 3 - Verify Solution Feasibility
- Perform an independent verification: for each element, check if at least one item in its `coverage_sets` list is selected.
- This step validates the solver's result and catches any potential issues in model formulation or solution extraction.

### Step 4 - Structure Output
- Return a structured result containing the status, objective value, list of selected indices, and a boolean flag indicating verification success.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
n_items = len(costs)
x = [model.NewBoolVar(f"x_{i}") for i in range(n_items)]

# Objective
objective_terms = [costs[i] * x[i] for i in range(n_items)]
model.Minimize(sum(objective_terms))

# Coverage constraints
for element_idx, covering_items in enumerate(coverage_sets):
    element_vars = [x[i] for i in covering_items]
    model.Add(sum(element_vars) >= 1)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in range(n_items) if solver.Value(x[i]) == 1]
    total_cost = solver.ObjectiveValue()
    # Verification loop
    all_covered = True
    for element_idx, covering_items in enumerate(coverage_sets):
        covered = any(solver.Value(x[i]) == 1 for i in covering_items)
        if not covered:
            all_covered = False
            break
else:
    # Handle no solution found
    selected = []
    total_cost = None
    all_covered = False
```

### Common Pitfalls
- Not setting a random seed, leading to non-reproducible results across runs.
- Misinterpreting the solver status codes (e.g., `UNKNOWN` vs. `FEASIBLE`).
- Skipping the verification step, which is crucial for validating that the extracted solution satisfies all original constraints.
