---
name: Flexible Job Shop Scheduling with Arbitrary Routing
description: |
  Model and solve flexible job shop problems where each job must visit all machines exactly once in any order, minimizing makespan using either CP-SAT with permutation variables or MILP with disjunctive constraints.

---

# Workflow 1 (CP-SAT with Permutation Variables)

## Modeling stage

### Strategy Overview
This approach models the problem as a bipartite matching between jobs and machines using permutation variables, enforcing no-overlap via conditional precedence constraints. It is well-suited for CP-SAT solvers which handle `AllDifferent` and `OnlyEnforceIf` efficiently.

### Step 1 - Define Core Variables
- Define integer variables `position[j, m]` representing the sequence order of job `j` on machine `m`. Domain is `[0, n_jobs - 1]`.
- Define integer variables `machine_order[j, m]` representing the processing order of machine `m` for job `j`. Domain is `[0, n_machines - 1]`.
- Define continuous or integer variables `start_time[j, m]` for the start time of each operation.

### Step 2 - Enforce Bijection and Permutation Constraints
- For each job `j`, enforce `AllDifferent` on `position[j, m]` across all machines `m`. This ensures each job has a unique position on each machine.
- For each machine `m`, enforce `AllDifferent` on `position[j, m]` across all jobs `j`. This ensures each position on a machine is occupied by exactly one job.
- For each job `j`, enforce `AllDifferent` on `machine_order[j, m]` across all machines `m`. This defines a total order of machines for the job.

### Step 3 - Model Machine No-Overlap with Conditional Precedence
- For each machine `m` and each unordered pair of distinct jobs `(i, j)`, create a boolean variable `precedes[i, j, m]`.
- Link the boolean variable to the permutation: `position[i, m] < position[j, m]` implies `precedes[i, j, m] = True`. Use `OnlyEnforceIf`.
- Enforce the disjunctive constraint: `start_time[i, m] + processing_time[i, m] <= start_time[j, m]` only if `precedes[i, j, m]` is true.

### Step 4 - Model Job No-Overlap with Machine Order Variables
- For each job `j` and each unordered pair of distinct machines `(a, b)`, create a boolean variable `a_before_b[j, a, b]`.
- Link the boolean variable to the machine order: `machine_order[j, a] < machine_order[j, b]` implies `a_before_b[j, a, b] = True`. Use `OnlyEnforceIf`.
- Enforce the precedence constraint: `start_time[j, a] + processing_time[j, a] <= start_time[j, b]` only if `a_before_b[j, a, b]` is true.

### Step 5 - Define Makespan Objective
- Create a makespan variable `C_max`.
- For each job `j` and machine `m`, add constraint: `start_time[j, m] + processing_time[j, m] <= C_max`.
- Set the objective to minimize `C_max`.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Machines"
  ],
  "parameters": [
    "processing_time[j in Jobs][m in Machines]"
  ],
  "decision_variables": [
    "position[j in Jobs][m in Machines] ∈ {0, ..., |Jobs|-1}",
    "machine_order[j in Jobs][m in Machines] ∈ {0, ..., |Machines|-1}",
    "start_time[j in Jobs][m in Machines] ≥ 0",
    "precedes[i in Jobs, j in Jobs, m in Machines where i < j] ∈ {0,1}",
    "a_before_b[j in Jobs, a in Machines, b in Machines where a < b] ∈ {0,1}",
    "C_max ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "C_max"
  },
  "constraints": [
    "AllDifferent(position[j, :]) for all j in Jobs",
    "AllDifferent(position[:, m]) for all m in Machines",
    "AllDifferent(machine_order[j, :]) for all j in Jobs",
    "position[i,m] < position[j,m] ↔ precedes[i,j,m] for all i<j, m",
    "start_time[i,m] + processing_time[i,m] ≤ start_time[j,m] if precedes[i,j,m] for all i<j, m",
    "machine_order[j,a] < machine_order[j,b] ↔ a_before_b[j,a,b] for all j, a<b",
    "start_time[j,a] + processing_time[j,a] ≤ start_time[j,b] if a_before_b[j,a,b] for all j, a<b",
    "start_time[j,m] + processing_time[j,m] ≤ C_max for all j, m"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce `AllDifferent` on `machine_order` for each job, leading to invalid job routings.
- Incorrectly linking the boolean precedence variable to the integer comparison; ensure both `OnlyEnforceIf` and its negation are added for the implication.
- Using an insufficient upper bound for `start_time` variables, which can hinder solver performance. Use a calculated upper bound like the sum of all processing times.

## Solving stage

### Strategy Overview
Solve the CP model using OR-Tools CP-SAT with parallel search, verify optimality via an infeasibility check, and extract a validated schedule.

### Step 1 - Configure Solver and Search
- Instantiate the CP-SAT solver.
- Set `num_search_workers` to the number of available CPU cores (e.g., 8) for parallel search.
- Set a reasonable time limit (e.g., `max_time_in_seconds = 30`).
- Set `random_seed` for reproducibility (e.g., 42).
- Set `relative_gap_limit = 0.0` to seek proven optimal solutions.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the status: `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`.
- If `OPTIMAL` or `FEASIBLE`, proceed to extract the solution. If `INFEASIBLE`, review model formulation.

### Step 3 - Verify Optimality via Feasibility Check
- If a solution with makespan `M*` is found, add a new constraint `C_max < M*` to the model.
- Solve the modified model. If the result is `INFEASIBLE`, `M*` is proven optimal.
- This step is crucial when the solver returns `FEASIBLE` within a time limit rather than `OPTIMAL`.

### Step 4 - Extract and Validate Schedule
- Extract the values for `start_time[j, m]`, `position[j, m]`, and `machine_order[j, m]` from the solution.
- Validate constraints manually:
    1. For each machine, sort operations by `start_time` and ensure no overlaps.
    2. For each job, sort operations by `start_time` and ensure the sequence matches `machine_order` with no overlaps.
    3. Verify the computed makespan equals the maximum completion time.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... variable and constraint creation as per modeling stage ...
model.Minimize(C_max)

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    best_makespan = solver.Value(C_max)
    # Optimality check
    model.Add(C_max < best_makespan)
    check_status = solver.Solve(model)
    if check_status == cp_model.INFEASIBLE:
        print(f"Optimal makespan proven: {best_makespan}")
    # ... extract and validate schedule ...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Relying solely on the solver's `OPTIMAL` status; always perform the infeasibility check for proof, especially under time limits.
- Not setting `random_seed`, leading to non-reproducible results.
- Extracting variable values without checking if the variable is defined in the solution (use `solver.Value()` safely).

# Workflow 2 (MILP with Disjunctive Big-M Constraints)

## Modeling stage

### Strategy Overview
This approach formulates the problem as a Mixed-Integer Linear Program (MILP) using binary precedence variables and Big-M constraints to enforce disjunctive (no-overlap) conditions. It is compatible with commercial and open-source MILP solvers.

### Step 1 - Define Decision Variables
- Define continuous variables `S[j, m] ≥ 0` for the start time of job `j` on machine `m`.
- Define binary variables `x[i, j, m]` for all `i < j` and each machine `m`. `x = 1` if job `i` precedes job `j` on machine `m`.
- Define binary variables `y[j, a, b]` for all jobs `j` and machine pairs `a < b`. `y = 1` if machine `a` is processed before machine `b` for job `j`.
- Define continuous variable `C_max ≥ 0` for the makespan.

### Step 2 - Model Machine No-Overlap (Disjunctive Constraints)
- For each machine `m` and each job pair `i < j`, add constraints:
    `S[i, m] + p[i, m] ≤ S[j, m] + M * (1 - x[i, j, m])`
    `S[j, m] + p[j, m] ≤ S[i, m] + M * x[i, j, m]`
- This ensures either job `i` precedes `j` or vice versa. `M` is a sufficiently large constant (Big-M).

### Step 3 - Model Job No-Overlap (Routing Precedence)
- For each job `j` and each machine pair `a < b`, add constraints:
    `S[j, a] + p[j, a] ≤ S[j, b] + M * (1 - y[j, a, b])`
    `S[j, b] + p[j, b] ≤ S[j, a] + M * y[j, a, b]`
- This enforces a total order of machines for each job.

### Step 4 - Define Makespan Objective
- For each job `j` and machine `m`, add constraint: `S[j, m] + p[j, m] ≤ C_max`.
- Set the objective to minimize `C_max`.

### Step 5 - Set Big-M Value
- Calculate `M` as the sum of all processing times: `M = Σ_{j,m} p[j, m]`. This value is guaranteed to be large enough to deactivate constraints when needed.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Machines"
  ],
  "parameters": [
    "p[j in Jobs][m in Machines]"
  ],
  "decision_variables": [
    "S[j in Jobs][m in Machines] ≥ 0",
    "x[i in Jobs, j in Jobs, m in Machines where i < j] ∈ {0,1}",
    "y[j in Jobs, a in Machines, b in Machines where a < b] ∈ {0,1}",
    "C_max ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "C_max"
  },
  "constraints": [
    "S[i,m] + p[i,m] ≤ S[j,m] + M*(1 - x[i,j,m]) for all i<j, m",
    "S[j,m] + p[j,m] ≤ S[i,m] + M*x[i,j,m] for all i<j, m",
    "S[j,a] + p[j,a] ≤ S[j,b] + M*(1 - y[j,a,b]) for all j, a<b",
    "S[j,b] + p[j,b] ≤ S[j,a] + M*y[j,a,b] for all j, a<b",
    "S[j,m] + p[j,m] ≤ C_max for all j, m"
  ]
}
```

### Common Pitfalls
- Choosing a Big-M value that is too small, which can cut off valid solutions. Use the sum of all processing times.
- Choosing a Big-M value that is excessively large, which can lead to numerical instability and weak LP relaxations.
- Forgetting to define the precedence variable for both orders (`i<j`), leading to an incomplete model.

## Solving stage

### Strategy Overview
Solve the MILP using a solver like Gurobi, CPLEX, or CBC with appropriate time and gap limits. Verify optimality via lower bound checks and infeasibility proofs.

### Step 1 - Configure Solver and Solve
- Instantiate the solver (e.g., Gurobi, CBC via Pyomo).
- Set a time limit (e.g., `TimeLimit=30`).
- Set the MIP gap tolerance to zero (`MIPGap=0.0`) to seek optimality.
- Set the number of threads (e.g., `Threads=4`).
- Set a random seed for reproducibility (e.g., `Seed=42`).
- Solve the model.

### Step 2 - Check Solution Status and Quality
- Check the solver status: `Optimal`, `Feasible`, or `NoSolution`.
- If `Optimal`, the solution is proven optimal.
- If `Feasible` (hit time limit), calculate the lower bound from the solver or compute theoretical bounds to assess the gap.

### Step 3 - Compute and Compare Theoretical Lower Bounds
- Calculate the job-based lower bound: `LB_job = max_j ( Σ_m p[j, m] )`.
- Calculate the machine-based lower bound: `LB_machine = max_m ( Σ_j p[j, m] )`.
- The overall lower bound is `LB = max(LB_job, LB_machine, ceil(Σ p[j,m] / |M|))`.
- If the best-found makespan equals `LB`, optimality is proven.

### Step 4 - Verify Optimality via Infeasibility Check
- If a candidate optimal makespan `M*` is found, add the constraint `C_max <= M* - 1` to the model.
- Re-solve. If the model becomes infeasible, `M*` is optimal.
- This step is essential when the solver does not guarantee optimality.

### Step 5 - Extract and Display Schedule
- Extract `S[j, m]` values from the solution.
- Compute completion times `C[j, m] = S[j, m] + p[j, m]`.
- For each machine, sort operations by `S[j, m]` to display the sequence.
- For each job, sort operations by `S[j, m]` to display the routing.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
# ... sets, parameters, variable and constraint creation as per modeling stage ...
model.obj = pyo.Objective(expr=model.C_max, sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')  # or 'cbc'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model, tee=False)

if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    best_makespan = pyo.value(model.C_max)
    # Optimality check via infeasibility
    model.con_infeas_check = pyo.Constraint(expr=model.C_max <= best_makespan - 1)
    check_results = solver.solve(model, tee=False)
    if check_results.solver.termination_condition == pyo.TerminationCondition.infeasible:
        print(f"Optimal makespan proven: {best_makespan}")
    # ... extract and display schedule ...
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print(f"Feasible solution found, but not proven optimal.")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not setting a time limit, potentially causing the solver to run indefinitely on large instances.
- Confusing solver statuses; `feasible` does not imply `optimal`.
- Failing to compute and use theoretical lower bounds to assess solution quality when optimality is not proven.
