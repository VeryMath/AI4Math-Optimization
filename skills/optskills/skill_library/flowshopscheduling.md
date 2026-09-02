---
name: FlowShopScheduling
description: |
  Model and solve flow shop scheduling problems with disjunctive resources and precedence constraints to minimize makespan using either CP-SAT with interval variables or MIP with big-M disjunctive constraints.

---
# Workflow 1 (CP-SAT with Interval Variables)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools CP-SAT solver, modeling jobs as interval variables on each machine. It leverages native `AddNoOverlap` constraints for disjunctive resources and enforces precedence via linear constraints. The model is concise and benefits from CP-SAT's dedicated scheduling algorithms.

### Step 1 - Define Problem Sets and Horizon
- Define sets for `jobs` and `machines`. The sequence of machines is fixed for all jobs.
- Compute a horizon upper bound as the sum of all processing times across all jobs and machines.
- Create a dictionary `processing_time[j][m]` for the duration of job `j` on machine `m`.

### Step 2 - Create Interval Variables
- For each job `j` and machine `m`, create an interval variable `interval[j][m]`. Its start is `start_var[j][m]`, its size is fixed to `processing_time[j][m]`, and its end is `end_var[j][m]`. All variables are defined within the horizon.

### Step 3 - Enforce Precedence Constraints
- For each job `j` and for each machine `m` (except the last), add a constraint: `end_var[j][m] <= start_var[j][m+1]`. This ensures the job's operation on machine `m` finishes before it starts on machine `m+1`.

### Step 4 - Enforce Disjunctive Resources
- For each machine `m`, add a `AddNoOverlap` constraint over the list of interval variables for all jobs on that machine: `solver.AddNoOverlap([interval[j][m] for j in jobs])`. This ensures no two jobs overlap on the same machine.

### Step 5 - Define Makespan and Objective
- Create a makespan variable. For each job `j`, add a constraint: `makespan >= end_var[j][last_machine]`.
- Set the objective to minimize the makespan variable.

### Formulation Template
```json
{
  "sets": ["jobs", "machines"],
  "parameters": ["processing_time[j][m]"],
  "decision_variables": ["start_var[j][m]", "interval[j][m]", "makespan"],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "precedence: end_var[j][m] <= start_var[j][m+1] for all j, m < last_machine",
    "disjunctive: NoOverlap([interval[j][m] for j in jobs]) for all m",
    "makespan_definition: makespan >= end_var[j][last_machine] for all j"
  ]
}
```

### Common Pitfalls
- Forgetting to set an upper bound for the horizon, which can lead to inefficient solving.
- Misindexing machines when adding precedence constraints, leading to an invalid sequence.
- Using `AddNoOverlap` on the wrong list of intervals (e.g., mixing machines), which does not correctly model machine capacity.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with time and parallel search settings, then solve and extract the schedule. Solution verification includes checking constraint satisfaction and, for small instances, validating optimality via enumeration.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds` to a reasonable limit (e.g., 30).
- Set `solver.parameters.num_search_workers` to the number of CPU cores (e.g., 8).
- Set `solver.parameters.random_seed` for reproducibility (e.g., 42).
- For exact optimization, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Invoke `solver.Solve(model)`.
- Check the status: `OPTIMAL`, `FEASIBLE`, or `INFEASIBLE`. Handle each case appropriately in output.

### Step 3 - Extract and Validate Schedule
- If a solution is found, collect the values of `start_var[j][m]` and `end_var[j][m]`.
- Programmatically verify all constraints: precedence and no-overlap per machine.
- For problems with `n <= 6` jobs, perform an exhaustive permutation check to confirm global optimality.

### Step 4 - Output Schedule and Metrics
- Print the makespan value.
- Output a Gantt chart or a table listing job start/end times per machine.
- Report machine utilization and idle times for analysis.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (create variables, add constraints, set objective)
# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)
# check status and extract solution
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    makespan = solver.Value(makespan_var)
    # ... extract start/end times
```

### Common Pitfalls
- Not checking solver status, leading to errors when trying to access values from an infeasible model.
- Assuming `FEASIBLE` status means optimal; always report the status clearly.
- Forgetting to scale the `max_time_in_seconds` parameter with problem size, potentially cutting off the search too early.

# Workflow 2 (MIP with Big-M Disjunctive Constraints)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Program (MIP), using binary sequencing variables and Big-M constraints to model disjunctive resources. It provides explicit control over the disjunctive logic and is suitable for solvers like Gurobi or CBC.

### Step 1 - Define Problem Sets and Parameters
- Define sets for `jobs` and `machines`.
- Define parameter `processing_time[j][m]`.
- Compute a large constant `M` (Big-M), e.g., as the sum of all processing times.

### Step 2 - Create Continuous Decision Variables
- Create continuous variable `start[j][m]` for the start time of job `j` on machine `m`.
- Create variable `makespan` to capture the completion time.

### Step 3 - Enforce Processing and Precedence
- For each job `j` and machine `m`, enforce the processing relation implicitly through precedence: `start[j][m] + processing_time[j][m] <= start[j][m+1]` for `m < last_machine`.
- This ensures the operation on machine `m` finishes before the job starts on `m+1`.

### Step 4 - Model Disjunctive Resources with Sequencing Variables
- For each machine `m` and for each pair of jobs `i, j` where `i < j`, create a binary variable `seq[i][j][m]`.
- If `seq[i][j][m] = 1`, job `i` must finish before job `j` starts on machine `m`. If `0`, job `j` must finish before job `i` starts.
- Add Big-M constraints:
    - `start[j][m] >= start[i][m] + processing_time[i][m] - M * (1 - seq[i][j][m])`
    - `start[i][m] >= start[j][m] + processing_time[j][m] - M * seq[i][j][m]`

### Step 5 - Define Makespan and Objective
- For each job `j`, add constraint: `makespan >= start[j][last_machine] + processing_time[j][last_machine]`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": ["jobs", "machines"],
  "parameters": ["processing_time[j][m]", "M (Big-M constant)"],
  "decision_variables": ["start[j][m]", "seq[i][j][m] (binary, i<j)", "makespan"],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "precedence: start[j][m] + processing_time[j][m] <= start[j][m+1] for all j, m < last_machine",
    "disjunctive_bigM_1: start[j][m] >= start[i][m] + processing_time[i][m] - M*(1 - seq[i][j][m]) for all m, i<j",
    "disjunctive_bigM_2: start[i][m] >= start[j][m] + processing_time[j][m] - M*seq[i][j][m] for all m, i<j",
    "makespan_definition: makespan >= start[j][last_machine] + processing_time[j][last_machine] for all j"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which can cut off valid solutions. It must be larger than the latest possible start time.
- Creating sequencing variables for all job pairs `(i,j)` without enforcing `i<j`, leading to redundant variables and constraints.
- Incorrectly indexing the precedence constraint, which can break the fixed job sequence through machines.

## Solving stage

### Strategy Overview
Configure a MIP solver with appropriate limits and optimality gap. Solve the model, then verify the solution against lower bounds and, for small instances, via complete enumeration to ensure quality.

### Step 1 - Configure MIP Solver
- Set a `TimeLimit` parameter (e.g., 30 seconds).
- Set `MIPGap` to 0.0 to search for proven optimal solutions.
- Set `Threads` for parallel solving (e.g., 4).
- Set a `Seed` for reproducibility (e.g., 42).

### Step 2 - Solve and Retrieve Solution
- Call the solver's `optimize()` method.
- Check the solution status: `Optimal`, `Feasible`, or `Infeasible`.

### Step 3 - Verify Solution and Bounds
- Compute simple lower bounds for validation:
    - LB1: Maximum machine load: `max over m of sum over j processing_time[j][m]`.
    - LB2: Critical path through jobs: minimum total processing time considering precedence.
- Compare the solver's objective value to these bounds.
- For `n <= 6` jobs, enumerate all job permutations to verify global optimality.

### Step 4 - Extract and Report Schedule
- Extract the values of `start[j][m]` and compute `end[j][m] = start[j][m] + processing_time[j][m]`.
- Output a schedule table sorted by start time on each machine.
- Analyze machine utilization and idle periods.

### Code Usage
```python
# build model from formulation
model = gp.Model('FlowShop')
# ... (create variables, add constraints, set objective)
# solve with status / termination checks
model.setParam('TimeLimit', 30)
model.setParam('MIPGap', 0.0)
model.optimize()
# check status and extract solution
if model.status == GRB.OPTIMAL:
    makespan = makespan.X
    # ... extract start times
```

### Common Pitfalls
- Not setting a time limit, which can cause the solver to run indefinitely on large instances.
- Confusing the `MIPGap` parameter (absolute vs. relative); ensure it's set correctly for the solver used.
- Failing to handle non-optimal statuses (e.g., `TimeLimit`), leading to attempts to access solution values that don't exist.
