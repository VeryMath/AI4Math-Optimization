---
name: Assignment Problem Solver
description: |
  Models and solves one-to-one assignment problems with binary decision variables, covering both MIP and CP-SAT solver backends.
---

# Workflow 1 (MIP with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the assignment problem as a mixed-integer linear program using binary variables, linear constraints for one-to-one matching, and a linear objective minimizing total cost.

### Step 1 - Define Binary Assignment Variables
- Create a binary integer variable `x[i, j]` for each pair `(i, j)` where `i` indexes the first set (e.g., workers) and `j` indexes the second set (e.g., tasks).
- Use `solver.IntVar(0, 1, f"x_{i}_{j}")` to enforce the binary domain.

### Step 2 - Enforce One-to-One Matching Constraints
- For each element `i` in the first set, add constraint: `sum_j x[i, j] == 1` to ensure exactly one assignment per entity.
- For each element `j` in the second set, add constraint: `sum_i x[i, j] == 1` to ensure exactly one assignment per entity.

### Step 3 - Minimize Total Cost Objective
- Build the objective as `minimize sum_i sum_j cost[i][j] * x[i, j]`.
- Use `objective.SetCoefficient(x[i, j], cost[i][j])` for each variable, then call `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I: first set entities", "J: second set entities"],
  "parameters": ["c[i, j]: cost of assigning i to j"],
  "decision_variables": ["x[i, j] ∈ {0, 1} for all i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} c[i, j] * x[i, j]"
  },
  "constraints": [
    "sum_{j in J} x[i, j] == 1 for all i in I",
    "sum_{i in I} x[i, j] == 1 for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to handle unbalanced instances: if `|I| != |J|`, add dummy entities with zero-cost assignments to create a square matrix.
- Using continuous variables instead of binary, which can lead to fractional assignments.

## Solving stage

### Strategy Overview
Solve the MIP formulation using OR-Tools' SCIP solver with time limits and parallel processing, then extract and validate the solution.

### Step 1 - Initialize Solver and Configure Parameters
- Create solver instance with `pywraplp.Solver.CreateSolver("SCIP")`.
- **Check solver availability:** Verify the returned instance is not `None`.
- Set time limit: `solver.SetTimeLimit([TIME_LIMIT_MS])` (e.g., 30000 for 30 seconds).
- Enable parallelism: `solver.SetNumThreads([NUM_THREADS])` (e.g., 4).

### Step 2 - Build and Solve Model
- Populate the variable dictionary `x = {}` with `solver.IntVar(0, 1, name)` for all `(i, j)` pairs.
- Add constraints using `solver.Add(sum(x[i, j] for j in range(num_tasks)) == 1)` for each worker, and similarly for tasks.
- Build objective with `objective.SetCoefficient()` and call `solver.Solve()`.

### Step 3 - Extract and Validate Results
- Check solver status: `if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]`.
- Extract assignments where `x[i, j].solution_value() > 0.5`.
- **Validate solution feasibility:** Verify the extracted assignment satisfies all one-to-one constraints.
- **Verify objective:** Manually sum costs of assigned pairs and compare to `solver.Objective().Value()` as a sanity check.

### Code Usage
```python
from ortools.linear_solver import pywraplp

def solve_assignment_mip(cost_matrix):
    num_workers = len(cost_matrix)
    num_tasks = len(cost_matrix[0])
    
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return {"status": "failed", "error": "Solver creation failed"}
    
    solver.SetTimeLimit(30000)
    solver.SetNumThreads(4)
    
    # Variables
    x = {}
    for i in range(num_workers):
        for j in range(num_tasks):
            x[i, j] = solver.IntVar(0, 1, f"x_{i}_{j}")
    
    # Constraints
    for i in range(num_workers):
        solver.Add(sum(x[i, j] for j in range(num_tasks)) == 1)
    for j in range(num_tasks):
        solver.Add(sum(x[i, j] for i in range(num_workers)) == 1)
    
    # Objective
    objective = solver.Objective()
    for i in range(num_workers):
        for j in range(num_tasks):
            objective.SetCoefficient(x[i, j], cost_matrix[i][j])
    objective.SetMinimization()
    
    status = solver.Solve()
    
    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        assignments = []
        total_cost = 0
        for i in range(num_workers):
            for j in range(num_tasks):
                if x[i, j].solution_value() > 0.5:
                    assignments.append({"worker": i, "task": j})
                    total_cost += cost_matrix[i][j]
        # Sanity check: verify objective consistency
        if abs(total_cost - solver.Objective().Value()) > 1e-6:
            return {"status": "error", "error": "Objective mismatch"}
        return {
            "status": "optimal" if status == pywraplp.Solver.OPTIMAL else "feasible",
            "objective": total_cost,
            "assignments": assignments
        }
    else:
        return {"status": "failed", "solver_status": status}
```

### Common Pitfalls
- Not checking if `CreateSolver` returns `None`, which indicates the solver backend is unavailable.
- Assuming `OPTIMAL` status when the time limit may cause early termination with `FEASIBLE`.

# Workflow 2 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Model the assignment problem using constraint programming with Boolean variables, leveraging CP-SAT's efficient propagation for one-to-one matching constraints.

### Step 1 - Define Boolean Assignment Variables
- Create a Boolean variable `x[i, j]` for each pair using `model.NewBoolVar(f"x_{i}_{j}")`.
- These variables implicitly enforce binary domain without explicit integer constraints.

### Step 2 - Enforce One-to-One Matching Constraints
- For each entity `i` in the first set: `model.Add(sum(x[i, j] for j in range(num_tasks)) == 1)`.
- For each entity `j` in the second set: `model.Add(sum(x[i, j] for i in range(num_workers)) == 1)`.

### Step 3 - Minimize Total Cost Objective
- Build a list of cost-weighted terms: `[cost_matrix[i][j] * x[i, j] for i in range(num_workers) for j in range(num_tasks)]`.
- Set objective: `model.Minimize(sum(objective_terms))`.
- **Note:** CP-SAT requires all objective coefficients to be integers; scale floating-point costs by a common factor if needed.

### Formulation Template
```json
{
  "sets": ["I: first set entities", "J: second set entities"],
  "parameters": ["c[i, j]: cost of assigning i to j"],
  "decision_variables": ["x[i, j] ∈ {True, False} for all i in I, j in J"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in I} sum_{j in J} c[i, j] * x[i, j]"
  },
  "constraints": [
    "sum_{j in J} x[i, j] == 1 for all i in I",
    "sum_{i in I} x[i, j] == 1 for all j in J"
  ]
}
```

### Common Pitfalls
- Using `model.AddBoolOr()` or other logical constraints instead of linear sums, which can be less efficient for assignment problems.
- Forgetting that CP-SAT requires all coefficients to be integers; scale floating-point costs by a common factor if needed.

## Solving stage

### Strategy Overview
Solve using OR-Tools CP-SAT solver with parallel search and optimality guarantees, then extract assignments with proper status checking.

### Step 1 - Configure CP-SAT Solver
- Instantiate `cp_model.CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]` (e.g., 30), `solver.parameters.num_search_workers = [NUM_WORKERS]` (e.g., 8), `solver.parameters.random_seed = [SEED]` (e.g., 42), `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE)` before extracting values.

### Step 3 - Extract and Validate Solution
- Iterate over all `(i, j)` pairs and collect assignments where `solver.Value(x[i, j]) == 1`.
- **Validate solution feasibility:** Ensure the extracted assignment satisfies all one-to-one constraints.
- **Verify objective:** Manually sum costs of assigned pairs and compare to `solver.ObjectiveValue()` as a sanity check.
- Return structured output with status, objective value, and assignment list.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_assignment_cpsat(cost_matrix):
    num_workers = len(cost_matrix)
    num_tasks = len(cost_matrix[0])
    
    model = cp_model.CpModel()
    
    # Variables
    x = {}
    for i in range(num_workers):
        for j in range(num_tasks):
            x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
    
    # Constraints
    for i in range(num_workers):
        model.Add(sum(x[i, j] for j in range(num_tasks)) == 1)
    for j in range(num_tasks):
        model.Add(sum(x[i, j] for i in range(num_workers)) == 1)
    
    # Objective
    objective_terms = []
    for i in range(num_workers):
        for j in range(num_tasks):
            objective_terms.append(cost_matrix[i][j] * x[i, j])
    model.Minimize(sum(objective_terms))
    
    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0
    
    status = solver.Solve(model)
    
    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments = []
        total_cost = 0
        for i in range(num_workers):
            for j in range(num_tasks):
                if solver.Value(x[i, j]) == 1:
                    assignments.append({"worker": i, "task": j})
                    total_cost += cost_matrix[i][j]
        # Sanity check: verify objective consistency
        if abs(total_cost - solver.ObjectiveValue()) > 1e-6:
            return {"status": "error", "error": "Objective mismatch"}
        return {
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "objective": total_cost,
            "assignments": assignments
        }
    else:
        return {"status": "failed", "solver_status": status}
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0` when proven optimality is required; otherwise CP-SAT may stop early with a feasible solution.
- Using `solver.Value()` without first checking the status, which can raise exceptions on infeasible models.
