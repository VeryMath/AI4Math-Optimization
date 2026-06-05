---
name: Binary Selection with Knapsack Constraint
description: |
  Model and solve binary selection problems with a single capacity constraint using either a dedicated knapsack solver or a general-purpose MILP solver, ensuring robust solution extraction and verification.
---

# Workflow 1 (Dedicated Knapsack Solver)

## Modeling stage

### Strategy Overview
Use a specialized knapsack algorithm for efficiency and simplicity. This workflow is ideal for pure 0-1 knapsack problems with a single resource constraint, leveraging optimized solvers that require minimal model setup.

### Step 1 - Recognize the Canonical Pattern
- Identify the problem as a standard 0/1 knapsack: binary selection decisions, a single capacity constraint, and a maximize-total-value objective.

### Step 2 - Structure Problem Data
- Organize item data into parallel lists or arrays: `values` for benefits and `weights` for resource consumption.
- Define a scalar `capacity` representing the resource limit.
- Validate data integrity: check list lengths match and all weights are non-negative.

### Step 3 - Map to Solver Input Format
- Recognize the solver's required input format: `profits` (values), `weights` as a list of lists (even for one dimension), and `capacities` as a list.
- Ensure consistent indexing of values and weights for all items.

### Formulation Template
```json
{
  "sets": [
    {"name": "items", "indices": "range(n_items)"}
  ],
  "parameters": [
    {"name": "value", "indexed_by": "items", "values": "list_of_values"},
    {"name": "weight", "indexed_by": "items", "values": "list_of_weights"},
    {"name": "capacity", "value": "scalar_limit"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indexed_by": "items"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{i in items} value[i] * x[i]"
  },
  "constraints": [
    {"name": "capacity_limit", "expression": "sum_{i in items} weight[i] * x[i] <= capacity"}
  ]
}
```

### Common Pitfalls
- Passing `weights` as a flat list instead of a list of lists to the solver's `init` method.
- Assuming the solver's `solve()` method takes data arguments; it should be called after `init()`.
- Not verifying solution feasibility by recalculating total weight against capacity.

## Solving stage

### Strategy Overview
Instantiate a dedicated knapsack solver, load the pre-structured data, solve, and extract the solution using the solver's specific API. Always implement error handling and solution verification.

### Step 1 - Initialize Solver
- Import the dedicated knapsack module: `from ortools.algorithms.python import knapsack_solver`.
- Create a solver instance with `knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER` for exact solutions to single-dimension problems.

### Step 2 - Load Data and Solve
- Call `solver.init(values, [weights], [capacity])` to load the problem data. Note the nested list structure for weights.
- Execute `solver.solve()` without arguments to compute the solution.
- Wrap the solve call in a try-except block to handle potential API errors gracefully.

### Step 3 - Extract and Verify Solution
- Retrieve the computed objective value from the solver.
- Identify selected items by iterating and checking `solver.best_solution_contains(i)`.
- Manually calculate the total selected weight and verify it does not exceed the capacity.
- Validate optimality: check that no single unselected item can be added without exceeding capacity.

### Step 4 - Perform Post-Solution Analysis
- Calculate remaining capacity.
- Compute value-to-weight ratios to understand the solution structure.
- Cross-verify with an alternative solver (e.g., MILP via Pyomo/CBC) to confirm optimality, ensuring both solvers return the same objective value and a consistent solution set.

### Code Usage
```python
from ortools.algorithms.python import knapsack_solver

# 1. Data Preparation
values = [...]  # List of item values
weights = [...]  # List of item weights
capacity = ...   # Scalar capacity
# Ensure weights is a list of lists for a single dimension
solver_weights = [weights]

# 2. Solver Initialization
solver = knapsack_solver.KnapsackSolver(
    knapsack_solver.SolverType.KNAPSACK_MULTIDIMENSION_BRANCH_AND_BOUND_SOLVER,
    "KnapsackSolver"
)

# 3. Load Data and Solve
solver.init(values, solver_weights, [capacity])
try:
    computed_value = solver.solve()
except Exception as e:
    print(f"Solver error: {e}")
    computed_value = None

# 4. Extract and Verify Solution
if computed_value is not None:
    selected_items = [i for i in range(len(values)) if solver.best_solution_contains(i)]
    total_weight = sum(weights[i] for i in selected_items)
    # Verification
    if total_weight <= capacity:
        status = "optimal_or_best_found"
    else:
        status = "solution_infeasible"
else:
    status = "failed"
    selected_items = []
    total_weight = 0

# 5. Output Structured Results
result = {
    "status": status,
    "objective_value": computed_value,
    "selected_items": selected_items,
    "total_weight_used": total_weight,
    "remaining_capacity": capacity - total_weight
}
# Include diagnostic output for pipeline extraction
print(f"RESULT:{result['objective_value']}")
```

### Common Pitfalls
- Using incorrect import paths for the dedicated solver library.
- Not checking if the solver returned `None` as the objective value, indicating a failure.
- Accepting the solver's solution without manually recalculating constraint satisfaction.

# Workflow 2 (General-Purpose MILP Solver)

## Modeling stage

### Strategy Overview
Formulate the binary selection problem as a Mixed-Integer Linear Program (MILP) using a modeling library. This approach is flexible, allowing for future extensions (e.g., additional constraints) and leverages widely available open-source solvers.

### Step 1 - Define Model Structure
- Create a model object (e.g., Pyomo `ConcreteModel`).
- Define an index set for all items (e.g., using `pyo.Set` or `pyo.RangeSet`).

### Step 2 - Declare Parameters and Variables
- Declare parameters for `value` and `weight`, indexed by the item set.
- Declare binary decision variables `x[i]` for each item, where `1` indicates selection.

### Step 3 - Formulate Objective and Constraint
- Set the objective to maximize the sum of `value[i] * x[i]`.
- Add a single linear constraint: the sum of `weight[i] * x[i]` must be less than or equal to the `capacity`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "indices": "set_of_item_identifiers"}
  ],
  "parameters": [
    {"name": "value", "indexed_by": "I", "values": "dictionary_or_callable"},
    {"name": "weight", "indexed_by": "I", "values": "dictionary_or_callable"},
    {"name": "capacity", "value": "scalar_limit"}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "indexed_by": "I"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(value[i] * x[i] for i in I)"
  },
  "constraints": [
    {"name": "capacity_constraint", "expression": "sum(weight[i] * x[i] for i in I) <= capacity"}
  ]
}
```

### Common Pitfalls
- Not using consistent indexing between parameters, variables, and data sources.
- Forgetting to set the objective sense to `maximize`.
- Hard-coding data within the model construction, reducing reusability.

## Solving stage

### Strategy Overview
Use a general-purpose MILP solver (e.g., CBC, HiGHS, SCIP) via a modeling library's interface. Configure solver options, solve the model, and rigorously check the solver status before extracting and verifying the solution.

### Step 1 - Configure and Execute Solver
- Instantiate a solver factory (e.g., `SolverFactory("cbc")`).
- Set practical options: time limit (`seconds`), optimality gap tolerance (`ratio` or `mip_rel_gap`), and thread count for parallelism.
- Call the solver with the model. Consider using `load_solutions=False` initially to control solution loading.

### Step 2 - Check Solver Status
- After solving, check `results.solver.status` (should be `SolverStatus.ok`).
- Check `results.solver.termination_condition`. Accept `TerminationCondition.optimal` or `.feasible` as successful outcomes.

### Step 3 - Extract and Validate Solution
- If status is acceptable, load the solution into the model variables.
- Extract selected items by filtering variables where `value(x[i]) > 0.5` (accounting for numerical tolerance).
- Recalculate the total objective value and total weight to verify against the model's reported values and the capacity constraint.
- Package results in a structured format (e.g., JSON) for downstream use.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Build Model
def build_knapsack_model(items, value_dict, weight_dict, capacity):
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=items)
    model.value = pyo.Param(model.I, initialize=value_dict)
    model.weight = pyo.Param(model.I, initialize=weight_dict)
    model.capacity = pyo.Param(initialize=capacity, mutable=True)
    model.x = pyo.Var(model.I, domain=pyo.Binary)
    model.obj = pyo.Objective(
        expr=sum(model.value[i] * model.x[i] for i in model.I),
        sense=pyo.maximize
    )
    model.cap_con = pyo.Constraint(
        expr=sum(model.weight[i] * model.x[i] for i in model.I) <= model.capacity
    )
    return model

# 2. Solve Model
items = [...]  # List of item identifiers
value = {...}  # Dict: item_id -> value
weight = {...} # Dict: item_id -> weight
capacity = ...

model = build_knapsack_model(items, value, weight, capacity)
solver = pyo.SolverFactory("cbc")  # Can substitute "highs" or "scip"
solver.options["seconds"] = [TIME_LIMIT]
solver.options["ratio"] = 0.0

# Solve with controlled solution loading
results = solver.solve(model, load_solutions=False)

# 3. Check Status and Extract
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    model.solutions.load_from(results)
    selected_items = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    total_value = float(pyo.value(model.obj))
    total_weight = sum(weight[i] for i in selected_items)
    # Verification
    if total_weight <= capacity:
        result_status = "optimal" if term == TerminationCondition.optimal else "feasible"
    else:
        result_status = "solution_infeasible"
else:
    result_status = f"failed_{status}_{term}"
    selected_items = []
    total_value = None
    total_weight = 0

# 4. Output Structured Results
result = {
    "status": result_status,
    "objective_value": total_value,
    "selected_items": selected_items,
    "total_weight_used": total_weight,
    "remaining_capacity": capacity - total_weight
}
# Include diagnostic output for pipeline extraction
print(f"RESULT:{result['objective_value']}")
```

### Common Pitfalls
- Assuming solver availability without checking imports or installation.
- Extracting variable values without first checking the solver status and termination condition.
- Not verifying the solution's feasibility by recalculating the constraint satisfaction manually.
- Setting an excessively tight optimality gap or time limit for simple problems, wasting resources.
