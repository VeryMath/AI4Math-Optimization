---
name: Flow Shop Scheduling with Makespan Minimization
description: |
  Model permutation flow shop problems with unary machine resources and precedence chains, then solve using either CP-SAT for exact solutions or MILP with symmetry breaking for heuristic/optimal results.

---
# Workflow 1 (CP-SAT with Sequence Variables)

## Modeling stage

### Strategy Overview
Model the problem using Constraint Programming (CP-SAT) with explicit binary precedence variables for each machine, enforcing disjunctive constraints via big-M and adding transitivity for stronger propagation. This approach directly captures the permutation sequence.

### Step 1 - Define Time and Precedence Variables
- Create integer variables `start[j][m]` and `end[j][m]` for each job `j` and machine `m` within a global horizon.
- Create binary variables `precedes[i][j][m]` for each pair of distinct jobs `i, j` and each machine `m`, where `1` indicates job `i` is processed before job `j` on machine `m`.

### Step 2 - Enforce Job Precedence Chains
- For each job `j` and for each machine `m` except the last, add constraint: `end[j][m] <= start[j][m+1]`. This ensures the operation sequence for each job follows the machine order.

### Step 3 - Enforce Machine Unary Resources
- For each machine `m` and each pair of distinct jobs `i, j`, add a disjunctive constraint using big-M: `start[j][m] >= end[i][m] - M * (1 - precedes[i][j][m])`. Set `M` to a large constant (e.g., sum of all processing times).
- Add mutual exclusivity: `precedes[i][j][m] + precedes[j][i][m] == 1` for all `i < j` and each machine `m`.

### Step 4 - Strengthen with Transitivity (Optional)
- To improve solver performance, add transitivity constraints for each machine `m` and all distinct `i, j, k`: `precedes[i][j][m] + precedes[j][k][m] - precedes[i][k][m] <= 1`.

### Step 5 - Define Makespan Objective
- Create an integer variable `makespan`.
- For each job `j`, add constraint: `makespan >= end[j][last_machine]`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Machines"
  ],
  "parameters": [
    "processing_time[j][m]",
    "horizon",
    "big_M"
  ],
  "decision_variables": [
    "start[j][m] (integer, [0, horizon])",
    "end[j][m] (integer, [0, horizon])",
    "precedes[i][j][m] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "end[j][m] == start[j][m] + processing_time[j][m]",
    "end[j][m] <= start[j][m+1] for m < last_machine",
    "start[j][m] >= end[i][m] - big_M * (1 - precedes[i][j][m]) for all i != j, m",
    "precedes[i][j][m] + precedes[j][i][m] == 1 for all i < j, m",
    "makespan >= end[j][last_machine] for all j"
  ]
}
```

### Common Pitfalls
- Setting `big_M` too small, which can cut off feasible solutions.
- Forgetting to enforce the precedence chain for all jobs, leading to invalid schedules.
- Omitting transitivity constraints can result in weaker propagation and longer solve times.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver, configured for parallel search and a time limit, to find optimal or feasible solutions. Extract and validate the schedule.

### Step 1 - Solver Configuration
- Instantiate the CP-SAT solver (`cp_model.CpSolver()`).
- Set `solver.parameters.max_time_in_seconds` to a reasonable limit (e.g., `[TIME_LIMIT]`).
- Set `solver.parameters.num_search_workers` to the number of available CPU cores.
- Set `solver.parameters.random_seed` for reproducibility.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- If status is `OPTIMAL`, the solution is proven optimal. If `FEASIBLE`, it is a valid but not necessarily optimal solution. Handle `UNKNOWN` or `INFEASIBLE` status appropriately.

### Step 3 - Solution Extraction
- If a solution was found, use `solver.Value(variable)` to retrieve the value of each `start[j][m]` and `precedes[i][j][m]` variable.
- Compute `end[j][m]` as `start[j][m] + processing_time[j][m]`.
- The makespan is `solver.Value(makespan)`.
- To get the job sequence per machine, sort jobs by their `start` time on that machine.

### Step 4 - Validation for Small Instances
- For problems with a small number of jobs (e.g., <= 8), validate the CP-SAT solution by enumerating all permutations and calculating the makespan via dynamic programming to verify correctness.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... define variables, constraints, objective as per modeling stage

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [NUM_WORKERS]
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    makespan = solver.Value(makespan_var)
    schedule = {(j, m): solver.Value(start_var[j][m]) for j in jobs for m in machines}
    # ... process schedule
else:
    print("No solution found.")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to errors.
- Misinterpreting `FEASIBLE` status as optimal.
- Forgetting to set a time limit for potentially large instances.

# Workflow 2 (MILP with Disjunctive Sequencing)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using disjunctive constraints with big-M and explicit sequencing variables. This approach is suitable for solvers like Gurobi or CBC and benefits from strong symmetry-breaking constraints.

### Step 1 - Define Continuous Start Variables
- Create continuous (or integer) variables `s[j][m]` representing the start time of job `j` on machine `m`.

### Step 2 - Enforce Precedence Chains
- For each job `j` and machine `m` except the last, add constraint: `s[j][m] + p[j][m] <= s[j][m+1]`, where `p` is the processing time.

### Step 3 - Model Machine Disjunctions
- For each machine `m` and each pair of distinct jobs `i, j`, create a binary variable `y[i][j][m]` where `1` means job `i` precedes job `j` on machine `m`.
- Add disjunctive constraints: `s[i][m] + p[i][m] <= s[j][m] + M * (1 - y[i][j][m])` and `s[j][m] + p[j][m] <= s[i][m] + M * y[i][j][m]`. `M` is a large constant.

### Step 4 - Add Symmetry-Breaking Constraints
- For each machine `m` and each pair `i < j`, add constraint: `y[i][j][m] + y[j][i][m] == 1`. This ensures a total order.
- Optionally, add constraints to break symmetry across identical machines or jobs.

### Step 5 - Define Makespan Objective
- Create a continuous variable `C_max`.
- For each job `j`, add constraint: `C_max >= s[j][last_machine] + p[j][last_machine]`.
- Set the objective to minimize `C_max`.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Machines"
  ],
  "parameters": [
    "processing_time[j][m]",
    "big_M"
  ],
  "decision_variables": [
    "s[j][m] (continuous, >=0)",
    "y[i][j][m] (binary)",
    "C_max (continuous)"
  ],
  "objective": {
    "sense": "min",
    "expression": "C_max"
  },
  "constraints": [
    "s[j][m] + processing_time[j][m] <= s[j][m+1] for m < last_machine",
    "s[i][m] + processing_time[i][m] <= s[j][m] + big_M * (1 - y[i][j][m]) for all i != j, m",
    "s[j][m] + processing_time[j][m] <= s[i][m] + big_M * y[i][j][m] for all i != j, m",
    "y[i][j][m] + y[j][i][m] == 1 for all i < j, m",
    "C_max >= s[j][last_machine] + processing_time[j][last_machine] for all j"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large `big_M`, which can make the model infeasible.
- Creating an excessive number of binary variables for large job sets, impacting performance.
- Neglecting symmetry-breaking constraints, leading to a bloated search space.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., Gurobi, CBC) with tuned parameters to find optimal or good feasible solutions within a time limit. Extract and interpret the schedule.

### Step 1 - Solver Configuration and Model Submission
- Instantiate the solver and load the model.
- Set a time limit (e.g., `model.setParam('TimeLimit', [TIME_LIMIT])`).
- Set optimality tolerance (e.g., `model.setParam('MIPGap', [TOLERANCE])`).
- Set the number of threads (e.g., `model.setParam('Threads', [NUM_THREADS])`).
- Set a random seed for reproducibility if supported.

### Step 2 - Solve and Check Termination Status
- Call `model.optimize()`.
- Check the status: `OPTIMAL`, `FEASIBLE`, `TIME_LIMIT`, or `INFEASIBLE`.
- If `OPTIMAL` or `FEASIBLE`, proceed to extract solution. For `TIME_LIMIT`, the best solution found is still valid.

### Step 3 - Extract and Interpret Solution
- Retrieve the objective value `model.objVal` (makespan).
- Get variable values: `s[j][m].X` for start times, `y[i][j][m].X` for sequencing.
- The sequence on each machine is determined by jobs where `y[i][j][m].X` is (approximately) 1.

### Step 4 - Validation and Reporting
- For small instances, validate the MILP solution via full permutation enumeration.
- Generate a human-readable schedule listing job sequences per machine and start/end times.

### Code Usage
```python
# build model from formulation
import gurobipy as gp
model = gp.Model()
# ... define variables, constraints, objective as per modeling stage

# solve with status / termination checks
model.setParam('TimeLimit', [TIME_LIMIT])
model.setParam('MIPGap', [TOLERANCE])
model.setParam('Threads', [NUM_THREADS])
model.optimize()

if model.status in [gp.GRB.OPTIMAL, gp.GRB.TIME_LIMIT, gp.GRB.SUBOPTIMAL]:
    makespan = model.objVal
    schedule = {(j, m): s[j][m].X for j in jobs for m in machines}
    # ... process schedule
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Not handling `TIME_LIMIT` status, which may still provide a useful incumbent solution.
- Assuming binary variables are exactly 0 or 1; use a tolerance (e.g., `if var.X > 0.5`).
- Forgetting to suppress solver log output, cluttering the console.
