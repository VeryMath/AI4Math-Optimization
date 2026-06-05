---
name: Contiguous Interval Packing with Non-Overlap
description: |
  Model and solve 1D contiguous interval packing problems with fixed lengths and pairwise non-overlap constraints to minimize the maximum used position.
---

# Workflow 1 (CP-SAT with Disjunctive Logic)

## Modeling stage

### Strategy Overview
Formulate the problem using a CP-SAT solver's native integer variables and logical constraints. The core challenge is encoding pairwise non-overlap as a disjunction, which is efficiently handled via auxiliary Boolean variables and implications.

### Step 1 - Define Core Variables and Domains
- Define an integer decision variable `start[i]` for each interval `i`, with a lower bound of `0` and an upper bound `UB` (e.g., sum of all interval lengths).
- Define an integer decision variable `end[i]` for each interval `i`, linked to `start[i]` via a length constraint.
- Define an auxiliary integer variable `max_pos` to capture the objective.

### Step 2 - Enforce Interval Lengths
- For each interval `i`, add the constraint `end[i] == start[i] + length[i]`, where `length[i]` is a fixed parameter.

### Step 3 - Enforce Pairwise Non-Overlap
- For each unordered pair `(i, j)` that must not overlap, create a Boolean variable `precedes_ij`.
- Add the implication: `precedes_ij == True` → `end[i] <= start[j]`.
- Add the implication: `precedes_ij == False` → `end[j] <= start[i]`.

### Step 4 - Define the Objective
- Add constraints `max_pos >= end[i]` for all intervals `i`.
- Set the objective to minimize `max_pos`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of intervals/tasks"},
    {"name": "P", "description": "Set of non-overlap pairs (i,j) where i < j"}
  ],
  "parameters": [
    {"name": "length_i", "for": "i in I", "type": "int", "description": "Fixed length of interval i"}
  ],
  "decision_variables": [
    {"name": "start_i", "for": "i in I", "type": "int", "lb": 0, "ub": "UB"},
    {"name": "end_i", "for": "i in I", "type": "int", "lb": 0, "ub": "UB"},
    {"name": "max_pos", "type": "int", "lb": 0, "ub": "UB"},
    {"name": "precedes_ij", "for": "(i,j) in P", "type": "bool", "description": "True if interval i ends before j starts"}
  ],
  "objective": {
    "sense": "min",
    "expression": "max_pos"
  },
  "constraints": [
    {"name": "interval_length", "for": "i in I", "formula": "end_i == start_i + length_i"},
    {"name": "max_pos_bound", "for": "i in I", "formula": "max_pos >= end_i"},
    {"name": "non_overlap", "for": "(i,j) in P", "formula": "(precedes_ij -> (end_i <= start_j)) AND ((not precedes_ij) -> (end_j <= start_i))"}
  ]
}
```

### Common Pitfalls
- Setting the upper bound `UB` too small, which can make the model infeasible. Use a safe over-estimate like the sum of all lengths.
- Creating duplicate non-overlap constraints for both `(i,j)` and `(j,i)`, which wastes resources. Define the pair set `P` to contain each unordered pair only once.
- Using the same `UB` as the Big-M in logical implications, which can lead to overly loose constraints. For CP-SAT, the `OnlyEnforceIf` pattern does not require a Big-M constant.

## Solving stage

### Strategy Overview
Use a CP-SAT solver (e.g., OR-Tools CP-SAT) to find an optimal assignment. Leverage its native support for integer variables, Boolean logic, and parallel search. Always verify solver status and solution feasibility.

### Step 1 - Solver Configuration
- Instantiate the CP-SAT solver.
- Set a time limit (e.g., `[TIME_LIMIT]` seconds) if needed.
- Configure parallel search (`num_search_workers`) for performance on larger instances.
- Set a `random_seed` for reproducibility.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve` method with the model and objective.
- Check the returned status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.).
- Proceed only if status indicates a feasible solution was found.

### Step 3 - Extract and Validate Solution
- If feasible, retrieve the value of each `start_i` and `end_i` variable.
- Compute `max_pos` from the retrieved `end_i` values to verify it matches the solver's objective value.
- Perform a sanity check: verify all length and non-overlap constraints are satisfied by the extracted values.

### Step 4 - Optimality Verification (Optional)
- To prove optimality, add a constraint `max_pos <= best_found_value - 1` and attempt to solve. Infeasibility confirms the original solution is optimal.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... create variables and constraints as per modeling stage ...

# Solve with status / termination checks
solver = cp_model.CpSolver()
# Set solver parameters
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42

status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    solution = {}
    for i in I:
        solution[i] = {
            'start': solver.Value(start_var[i]),
            'end': solver.Value(end_var[i])
        }
    objective_value = solver.ObjectiveValue()
    # Optional: verify constraints
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, which can cause runtime errors.
- Forgetting to set `num_search_workers` for parallel search, leaving performance on the table.
- Adding optimality verification constraints directly to the model object without using a copy or a separate model, which can corrupt the original model for subsequent use.

# Workflow 2 (MIP with Big-M Disjunction)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using binary variables to activate disjunctive constraints. This approach is solver-agnostic and uses a large constant (Big-M) to enforce conditional logic, suitable for traditional MIP solvers.

### Step 1 - Define Core Variables
- Define continuous or integer decision variables `start[i]` and `end[i]` for each interval `i`, with bounds `[0, UB]`.
- Define a continuous variable `max_pos` for the objective.

### Step 2 - Enforce Interval Lengths
- For each interval `i`, add the constraint `end[i] == start[i] + length[i]`.

### Step 3 - Enforce Pairwise Non-Overlap via Big-M
- For each non-overlap pair `(i, j)`, create a binary variable `z_ij`.
- Add constraint `end[i] <= start[j] + M * (1 - z_ij)`. When `z_ij = 1`, this enforces `end[i] <= start[j]`.
- Add constraint `end[j] <= start[i] + M * z_ij`. When `z_ij = 0`, this enforces `end[j] <= start[i]`.
- This ensures at least one ordering is active.

### Step 4 - Define the Objective
- Add constraints `max_pos >= end[i]` for all `i`.
- Set the objective to minimize `max_pos`.

### Formulation Template
```json
{
  "sets": [
    {"name": "I", "description": "Set of intervals"},
    {"name": "P", "description": "Set of non-overlap pairs (i,j) where i < j"}
  ],
  "parameters": [
    {"name": "length_i", "for": "i in I", "type": "float", "description": "Fixed length of interval i"},
    {"name": "M", "type": "float", "description": "Sufficiently large constant (Big-M)"}
  ],
  "decision_variables": [
    {"name": "start_i", "for": "i in I", "type": "continuous", "lb": 0, "ub": "UB"},
    {"name": "end_i", "for": "i in I", "type": "continuous", "lb": 0, "ub": "UB"},
    {"name": "max_pos", "type": "continuous", "lb": 0, "ub": "UB"},
    {"name": "z_ij", "for": "(i,j) in P", "type": "binary", "description": "1 if interval i must finish before j starts"}
  ],
  "objective": {
    "sense": "min",
    "expression": "max_pos"
  },
  "constraints": [
    {"name": "interval_length", "for": "i in I", "formula": "end_i == start_i + length_i"},
    {"name": "max_pos_bound", "for": "i in I", "formula": "max_pos >= end_i"},
    {"name": "non_overlap_ij", "for": "(i,j) in P", "formula": "end_i <= start_j + M * (1 - z_ij)"},
    {"name": "non_overlap_ji", "for": "(i,j) in P", "formula": "end_j <= start_i + M * z_ij"}
  ]
}
```

### Common Pitfalls
- Choosing a Big-M value (`M`) that is too small, making feasible solutions infeasible. `M` must be larger than the maximum possible span between any `start` and `end`.
- Choosing a Big-M value that is excessively large, which can cause numerical instability and slow convergence. Use the smallest valid upper bound (e.g., `UB`).
- Defining `z_ij` for both `(i,j)` and `(j,i)`, creating redundant variables and constraints. Define it only for ordered pairs `i < j`.

## Solving stage

### Strategy Overview
Use a traditional MIP solver (e.g., CBC, Gurobi, CPLEX). The Big-M formulation is linear and widely supported. Focus on proper Big-M calibration and solver tuning for performance.

### Step 1 - Solver and Model Setup
- Instantiate the solver and create an empty model.
- Add all variables and constraints as defined.
- Set the objective sense to minimization.

### Step 2 - Configure Solver Parameters
- Set a time limit (e.g., `[TIME_LIMIT]` seconds).
- Set optimality gap tolerance if appropriate.
- Enable presolve and cutting planes for better performance.
- Set thread count for parallel processing.

### Step 3 - Solve and Interpret Status
- Invoke the solver's `optimize` method.
- Check the status: `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.
- If status is not feasible, consider relaxing bounds or increasing `M`.

### Step 4 - Extract and Verify Solution
- Retrieve variable values for `start_i`, `end_i`, and `max_pos`.
- Verify that `max_pos` equals the maximum retrieved `end_i`.
- Manually check a sample of non-overlap constraints using the retrieved values and the binary `z_ij` to ensure the Big-M logic held.

### Code Usage
```python
import pulp  # or gurobipy, ortools.linear_solver

# Build model from formulation
prob = pulp.LpProblem("IntervalPacking", pulp.LpMinimize)
# ... create variables and constraints as per modeling stage ...

# Solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=[TIME_LIMIT], threads=8)
prob.solve(solver)

# Check status and extract solution
status = pulp.LpStatus[prob.status]
if status in ('Optimal', 'Feasible'):
    solution = {}
    for i in I:
        solution[i] = {
            'start': start_var[i].varValue,
            'end': end_var[i].varValue
        }
    objective_value = pulp.value(prob.objective)
    # Optional: verify constraints
else:
    print("No feasible solution found. Status:", status)
```

### Common Pitfalls
- Not verifying the chosen `M` is sufficient for all possible solutions, leading to incorrect infeasibility.
- Adding feasibility-testing constraints (e.g., `max_pos <= bound`) directly to the model object without copying it first, which alters the original model.
- Ignoring numerical tolerances when checking constraint satisfaction, especially with large `M` values. Use a small epsilon for comparisons.
