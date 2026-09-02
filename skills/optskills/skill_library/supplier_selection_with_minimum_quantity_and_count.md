---
name: Supplier Selection with Minimum Quantity and Count
description: |
  Model and solve assignment problems with minimum quantity requirements if selected and minimum supplier count constraints using mixed-integer linear programming.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a MILP with explicit linking constraints between continuous allocation and binary selection variables. It is designed for clarity and solver-agnostic execution, suitable for problems where data is provided via dictionaries.

### Step 1 - Define Data Structures
- Use Python dictionaries to store all input parameters, keyed by producer and contract identifiers.
- Define `cost[(i, j)]` for unit costs, `capacity[i]` for producer limits, `demand[j]` for contract requirements, `min_quantity[i]` for minimum allocation if selected, and `min_suppliers[j]` for the required minimum number of producers per contract.

### Step 2 - Declare Decision Variables
- Create a continuous, non-negative variable `assignment_quantity[i, j]` for the amount allocated from producer `i` to contract `j`.
- Create a binary variable `binary_assignment[i, j]` to indicate if producer `i` is selected for contract `j`.

### Step 3 - Formulate the Objective
- Minimize the total cost: sum of `cost[i, j] * assignment_quantity[i, j]` over all producer-contract pairs.

### Step 4 - Implement Core Constraints
- **Capacity Limit**: For each producer `i`, sum of `assignment_quantity[i, j]` over all contracts `j` must be ≤ `capacity[i]`.
- **Demand Satisfaction**: For each contract `j`, sum of `assignment_quantity[i, j]` over all producers `i` must be ≥ `demand[j]`.
- **Minimum Supplier Count**: For each contract `j`, sum of `binary_assignment[i, j]` over all producers `i` must be ≥ `min_suppliers[j]`.

### Step 5 - Link Continuous and Binary Variables
- **Upper Bound Link**: `assignment_quantity[i, j] ≤ capacity[i] * binary_assignment[i, j]`. This forces allocation to zero if not selected.
- **Lower Bound Link**: `assignment_quantity[i, j] ≥ min_quantity[i] * binary_assignment[i, j]`. This enforces the minimum quantity if selected.

### Formulation Template
```json
{
  "sets": [
    "PRODUCERS",
    "CONTRACTS"
  ],
  "parameters": {
    "cost": {"type": "float", "index": ["PRODUCERS", "CONTRACTS"]},
    "capacity": {"type": "float", "index": ["PRODUCERS"]},
    "demand": {"type": "float", "index": ["CONTRACTS"]},
    "min_quantity": {"type": "float", "index": ["PRODUCERS"]},
    "min_suppliers": {"type": "int", "index": ["CONTRACTS"]}
  },
  "decision_variables": [
    {"name": "assignment_quantity", "type": "continuous", "bounds": [0, null], "index": ["PRODUCERS", "CONTRACTS"]},
    {"name": "binary_assignment", "type": "binary", "index": ["PRODUCERS", "CONTRACTS"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * assignment_quantity[i,j] for i in PRODUCERS for j in CONTRACTS)"
  },
  "constraints": [
    {"name": "capacity_limit", "expression": "sum(assignment_quantity[i,j] for j in CONTRACTS) <= capacity[i] for i in PRODUCERS"},
    {"name": "demand_satisfaction", "expression": "sum(assignment_quantity[i,j] for i in PRODUCERS) >= demand[j] for j in CONTRACTS"},
    {"name": "min_supplier_count", "expression": "sum(binary_assignment[i,j] for i in PRODUCERS) >= min_suppliers[j] for j in CONTRACTS"},
    {"name": "link_upper", "expression": "assignment_quantity[i,j] <= capacity[i] * binary_assignment[i,j] for i in PRODUCERS for j in CONTRACTS"},
    {"name": "link_lower", "expression": "assignment_quantity[i,j] >= min_quantity[i] * binary_assignment[i,j] for i in PRODUCERS for j in CONTRACTS"}
  ]
}
```

### Common Pitfalls
- Using a single, overly large "Big-M" constant for the upper bound link instead of the producer-specific `capacity[i]`, which weakens the formulation.
- Forgetting the lower bound linking constraint, which allows a selected producer to supply less than its minimum required quantity.
- Defining `min_suppliers[j]` as a float parameter instead of an integer, causing type errors in the constraint.

## Solving stage

### Strategy Overview
This stage focuses on solving the Pyomo model using the HiGHS or CBC solver via the `pyomo.SolverFactory` interface, with robust status checking and solution validation to ensure reliable results.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `SolverFactory('highs')` or `SolverFactory('cbc')`).
- Set key parameters: `time_limit` for runtime control, `mip_rel_gap` for optimality tolerance, and a `seed` for reproducibility. Avoid setting `threads` if it causes conflicts.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Validate Solver Status
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- If the status is not OK or termination is not optimal/feasible, log the condition and handle the failure (e.g., return empty results, analyze infeasibility).

### Step 3 - Extract and Verify Solution
- Extract the objective value: `total_cost = pyo.value(model.obj)`.
- Iterate through the decision variables to build dictionaries of allocations (`assignment_quantity[i, j]`) and selections (`binary_assignment[i, j]`), applying a small tolerance (e.g., 1e-6) to determine positivity.
- Programmatically verify key constraints: total allocated demand meets requirements, no producer exceeds capacity, and minimum supplier counts are satisfied.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code as per modeling stage)

# Solve
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0001
solver.options['seed'] = 42

results = solver.solve(model, tee=False)

# Validate
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = float(pyo.value(model.obj))
    # Extract variable values into dictionaries
    allocations = {}
    selections = {}
    for i in model.PRODUCERS:
        for j in model.CONTRACTS:
            q_val = pyo.value(model.assignment_quantity[i, j])
            b_val = pyo.value(model.binary_assignment[i, j])
            if q_val > 1e-6:
                allocations[(i, j)] = q_val
            selections[(i, j)] = b_val
    # ... (verification logic)
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
    # Handle failure appropriately
```

### Common Pitfalls
- Not checking both `SolverStatus` and `TerminationCondition`, leading to misinterpretation of suboptimal or failed solves.
- Extracting variable values without checking if the solve was successful, which may raise errors.
- Using a loose optimality gap (`mip_rel_gap`) when an exact solution is required, potentially missing the true optimum.

# Workflow 2 (OR-Tools with SCIP/CBC Backend)

## Modeling stage

### Strategy Overview
This workflow uses the OR-Tools CP-SAT solver (for MIP) via its Python API, employing a more imperative, constraint-by-constraint building style. It is well-suited for deployment environments where a dedicated algebraic modeling language is not available.

### Step 1 - Initialize Model and Create Index Mappings
- Create a `cp_model.CpModel()` instance.
- Define lists or ranges for producer and contract indices. Optionally, create dictionaries to map these indices to solver variable objects.

### Step 2 - Create Decision Variables
- Create continuous (or integer) variables `assignment_quantity[i][j]` with bounds `[0, capacity[i]]` using `model.NewIntVar` or `model.NewNumVar`.
- Create binary variables `binary_assignment[i][j]` using `model.NewBoolVar()`.

### Step 3 - Define the Objective
- Create a linear expression: `sum(cost[i][j] * assignment_quantity[i][j] for all i, j)`.
- Set the model to minimize this expression using `model.Minimize()`.

### Step 4 - Add Capacity and Demand Constraints
- For each producer `i`, add a linear constraint: `sum(assignment_quantity[i][j] for j in contracts) <= capacity[i]`.
- For each contract `j`, add a linear constraint: `sum(assignment_quantity[i][j] for i in producers) >= demand[j]`.

### Step 5 - Enforce Minimum Supplier Count
- For each contract `j`, add a linear constraint: `sum(binary_assignment[i][j] for i in producers) >= min_suppliers[j]`.

### Step 6 - Link Variables with Conditional Constraints
- For each pair `(i, j)`, add two constraints using the `Add` method:
    1. `assignment_quantity[i][j] >= min_quantity[i] * binary_assignment[i][j]`.
    2. `assignment_quantity[i][j] <= capacity[i] * binary_assignment[i][j]`. This can be implemented by adding an implication: if `binary_assignment[i][j] == 0`, then `assignment_quantity[i][j] == 0`.

### Formulation Template
```json
{
  "sets": [
    "producers_list",
    "contracts_list"
  ],
  "parameters": {
    "cost_matrix": {"type": "list[list[float]]"},
    "capacity_list": {"type": "list[float]"},
    "demand_list": {"type": "list[float]"},
    "min_quantity_list": {"type": "list[float]"},
    "min_suppliers_list": {"type": "list[int]"}
  },
  "decision_variables": [
    {"name": "assignment_quantity", "type": "integer_or_continuous", "bounds": "variable", "index": ["i", "j"]},
    {"name": "binary_assignment", "type": "boolean", "index": ["i", "j"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "LinearExpr.Sum([assignment_quantity[i][j] * cost_matrix[i][j] for i, j in all_pairs])"
  },
  "constraints": [
    {"name": "capacity", "expression": "LinearExpr.Sum([assignment_quantity[i][j] for j in contracts]) <= capacity_list[i] for i in producers"},
    {"name": "demand", "expression": "LinearExpr.Sum([assignment_quantity[i][j] for i in producers]) >= demand_list[j] for j in contracts"},
    {"name": "supplier_count", "expression": "LinearExpr.Sum([binary_assignment[i][j] for i in producers]) >= min_suppliers_list[j] for j in contracts"},
    {"name": "link_lower", "expression": "assignment_quantity[i][j] >= min_quantity_list[i] * binary_assignment[i][j] for i, j in all_pairs"},
    {"name": "link_upper", "expression": "assignment_quantity[i][j] <= capacity_list[i] * binary_assignment[i][j] for i, j in all_pairs"}
  ]
}
```

### Common Pitfalls
- Using `model.NewIntVar` for large allocation quantities, which may cause integer overflow; prefer `model.NewNumVar` for continuous values.
- Incorrectly implementing the upper bound link as a direct multiplication in OR-Tools, which requires using `AddMultiplicationEquality` or an implication constraint for exact linearization.
- Not scaling the objective coefficients (costs) appropriately, which can lead to numerical issues in the solver.

## Solving stage

### Strategy Overview
This stage involves solving the OR-Tools model, configuring solver parameters like time limits and threads, and implementing detailed solution verification to ensure feasibility and optimality.

### Step 1 - Configure Solver Parameters
- Use `solver.parameters.max_time_in_seconds` to set a time limit.
- Set `solver.parameters.num_search_workers` to control parallel threads.
- Configure optimality tolerances if applicable (e.g., `solver.parameters.relative_gap_limit`).

### Step 2 - Execute the Solver
- Create a solver instance (e.g., `cp_model.CpSolver()`).
- Call `solver.Solve(model)` to obtain a status code.

### Step 3 - Check Solution Status
- Check if the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `MODEL_INVALID` statuses with appropriate error messages.
- For `FEASIBLE` solutions, note that optimality is not guaranteed.

### Step 4 - Extract and Validate Results
- If the solve was successful, extract the objective value using `solver.ObjectiveValue()`.
- Iterate through all variable indices, using `solver.Value(variable)` to get the solution for each `assignment_quantity` and `binary_assignment`.
- Store results in dictionaries and perform verification checks: confirm demand satisfaction, capacity adherence, minimum supplier counts, and the linking conditions.

### Code Usage
```python
from ortools.sat.python import cp_model

# ... (model building code as per modeling stage)

# Solve
solver = cp_model.CpSolver()
# Set parameters
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
# solver.parameters.relative_gap_limit = 0.0001 # For optimization problems

status = solver.Solve(model)

# Validate and extract
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    total_cost = solver.ObjectiveValue()
    allocations = {}
    selections = {}
    for i in range(num_producers):
        for j in range(num_contracts):
            q_val = solver.Value(assignment_quantity[i][j])
            b_val = solver.Value(binary_assignment[i][j])
            if q_val > 1e-6:
                allocations[(i, j)] = q_val
            selections[(i, j)] = b_val
    # ... (verification logic)
    print(f"Total cost: {total_cost}")
elif status == cp_model.INFEASIBLE:
    print("Model is infeasible.")
else:
    print(f"Solver returned status: {status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status implies optimality; always check for `OPTIMAL` if a proven optimum is required.
- Not using `solver.Value()` on the correct variable object, leading to extraction errors.
- Setting conflicting solver parameters (e.g., both time limit and iteration limit) without understanding precedence.
