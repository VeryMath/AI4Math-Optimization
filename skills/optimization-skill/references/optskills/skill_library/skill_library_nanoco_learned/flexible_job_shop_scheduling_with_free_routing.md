---
name: Flexible Job Shop Scheduling with Free Routing
description: |
  Model and solve flexible job shop problems where each job must visit all machines in any order, minimizing makespan via CP-SAT or MILP solvers.

---
# Workflow 1 (CP-SAT with Interval Variables)

## Modeling stage

### Strategy Overview
Model the problem using Constraint Programming (CP) via OR-Tools CP-SAT, leveraging high-level interval variables and the `NoOverlap` constraint to encode disjunctive scheduling efficiently. This approach is concise, benefits from built-in propagation, and is well-suited for medium-sized instances.

### Step 1 - Define Core Variables
- Create integer variables `start[j][m]` and `end[j][m]` for each job `j` and machine `m`.
- Create an interval variable `interval[j][m]` for each operation, linking start, end, and the fixed processing duration `p[j][m]` via `NewIntervalVar(start, duration, end, name)`.
- Create an integer variable `makespan` to be minimized.

### Step 2 - Set Upper Bounds
- Calculate a tight upper bound for all time variables and `makespan` as `max(max_machine_load, max_job_load)`, where:
  - `max_machine_load = max_{m in machines} sum_{j in jobs} p[j][m]`
  - `max_job_load = max_{j in jobs} sum_{m in machines} p[j][m]`
- Use this bound to set variable domains, tightening the search space.

### Step 3 - Enforce Job Non-Overlap
- For each job `j`, collect all its interval variables `interval[j][m]` for all machines `m`.
- Add a `NoOverlap` constraint over this list to ensure the job's operations do not overlap in time.

### Step 4 - Enforce Machine Non-Overlap
- For each machine `m`, collect all interval variables `interval[j][m]` for all jobs `j`.
- Add a `NoOverlap` constraint over this list to ensure the machine processes at most one job at a time.

### Step 5 - Define Makespan and Objective
- For each job `j` and machine `m`, add a constraint: `makespan >= end[j][m]`.
- Set the objective to minimize the `makespan` variable.

### Formulation Template
```json
{
  "sets": [
    "jobs",
    "machines"
  ],
  "parameters": [
    "processing_time[job][machine]"
  ],
  "decision_variables": [
    "start[job][machine] (integer)",
    "end[job][machine] (integer)",
    "interval[job][machine] (interval)",
    "makespan (integer)"
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "end[j][m] == start[j][m] + processing_time[j][m]",
    "NoOverlap([interval[j][m] for m in machines]) for each job j",
    "NoOverlap([interval[j][m] for j in jobs]) for each machine m",
    "makespan >= end[j][m] for all j, m"
  ]
}
```

### Common Pitfalls
- Forgetting to define the `interval` variable with the correct start, end, and size, leading to incorrect `NoOverlap` behavior.
- Setting an overly loose upper bound for `makespan` (e.g., sum of all processing times) can slow down search; always use the tighter bound `max(max_machine_load, max_job_load)`.
- Not utilizing solver parallelism; CP-SAT benefits from multiple search workers.

## Solving stage

### Strategy Overview
Solve the CP model using OR-Tools CP-SAT solver with appropriate time limits and parallel search. Extract and validate the schedule from the solution.

### Step 1 - Configure Solver
- Instantiate the `CpSolver` and set key parameters: a time limit (`max_time_in_seconds`), number of parallel workers (`num_search_workers`), and a random seed for reproducibility.
- Optionally, set `relative_gap_limit = 0.0` to aim for proven optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)` and capture the status.
- Check if the status is `OPTIMAL` or `FEASIBLE` before proceeding to extract the solution.

### Step 3 - Extract and Validate Schedule
- For each variable `start[j][m]` and `end[j][m]`, retrieve its value using `solver.Value()`.
- Reconstruct the sequence of operations for each job and each machine by sorting operations by their start times.
- Verify that no overlaps exist in the extracted schedule as a sanity check.
- For verification, calculate the lower bound `max(max_machine_load, max_job_load)`. If the solution value equals this bound, optimality is proven.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
# ... (create variables and constraints as per Modeling Stage)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [NUM_WORKERS]
solver.parameters.random_seed = [SEED]
solver.parameters.relative_gap_limit = 0.0

status = solver.Solve(model)

# Check status and extract solution
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    makespan_value = solver.Value(makespan)
    schedule = {}
    for j in jobs:
        for m in machines:
            schedule[(j, m)] = (solver.Value(start[j][m]), solver.Value(end[j][m]))
    # ... (process schedule)
else:
    print("No solution found.")
```

### Common Pitfalls
- Not checking solver status before accessing variable values, which can cause runtime errors.
- Interpreting `FEASIBLE` status as optimal; if optimality is required, explicitly check for `OPTIMAL`.
- Using default solver parameters for large instances; always set a time limit and consider enabling logging (`solver.parameters.log_search_progress = True`) for debugging.

# Workflow 2 (MILP with Big-M Disjunctions)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using a Big-M formulation with explicit binary sequencing variables. This provides explicit control over precedence relationships and is suitable for solvers like Gurobi or CBC.

### Step 1 - Define Core Variables
- Create continuous variables `start[j][m]` and `completion[j][m]` for each job `j` and machine `m`.
- Create binary variables `prec[j][m1][m2]` for each job `j` and distinct machine pair `(m1, m2)`, where `1` indicates `m1` precedes `m2` for job `j`.
- Create binary variables `seq[i][j][m]` for each machine `m` and distinct job pair `(i, j)`, where `1` indicates job `i` precedes job `j` on machine `m`.
- Create a continuous variable `makespan` to be minimized.

### Step 2 - Link Times and Define Processing
- Add constraints: `completion[j][m] == start[j][m] + processing_time[j][m]` for all `j, m`.

### Step 3 - Enforce Job Non-Overlap via Precedence
- For each job `j` and each distinct machine pair `(m1, m2)`, add a Big-M constraint: `start[j][m2] >= completion[j][m1] - BigM * (1 - prec[j][m1][m2])`.
- Add antisymmetry constraints: `prec[j][m1][m2] + prec[j][m2][m1] == 1` for all `j, m1, m2` where `m1 != m2`.

### Step 4 - Enforce Machine Non-Overlap via Sequencing
- For each machine `m` and each distinct job pair `(i, j)`, add a Big-M constraint: `start[j][m] >= completion[i][m] - BigM * (1 - seq[i][j][m])`.
- Add antisymmetry constraints: `seq[i][j][m] + seq[j][i][m] == 1` for all `i, j, m` where `i != j`.

### Step 5 - Define Makespan and Objective
- Add constraints: `makespan >= completion[j][m]` for all `j, m`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "jobs",
    "machines"
  ],
  "parameters": [
    "processing_time[job][machine]",
    "BigM (large constant)"
  ],
  "decision_variables": [
    "start[job][machine] (continuous)",
    "completion[job][machine] (continuous)",
    "prec[job][machine1][machine2] (binary)",
    "seq[job1][job2][machine] (binary)",
    "makespan (continuous)"
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "completion[j][m] == start[j][m] + processing_time[j][m]",
    "start[j][m2] >= completion[j][m1] - BigM * (1 - prec[j][m1][m2]) for j, m1≠m2",
    "prec[j][m1][m2] + prec[j][m2][m1] == 1 for j, m1≠m2",
    "start[j][m] >= completion[i][m] - BigM * (1 - seq[i][j][m]) for m, i≠j",
    "seq[i][j][m] + seq[j][i][m] == 1 for m, i≠j",
    "makespan >= completion[j][m] for all j, m"
  ]
}
```

### Common Pitfalls
- Choosing a `BigM` value that is too large, leading to numerical instability and weak LP relaxations; use a tight bound like `max(max_machine_load, max_job_load)`.
- Forgetting the antisymmetry constraints for precedence/sequence variables, resulting in incomplete or invalid orders.
- Creating redundant variables or constraints (e.g., `prec[j][m][m]`) which increase model size unnecessarily.

## Solving stage

### Strategy Overview
Solve the MILP model using a MIP solver via a modeling framework like Pyomo. Configure solver parameters for performance, verify termination status, and extract the schedule.

### Step 1 - Build Model and Configure Solver
- Instantiate a concrete model in Pyomo, defining sets, parameters, variables, constraints, and the objective as per the formulation.
- Create a solver object (e.g., for Gurobi, CBC) and set parameters: time limit, MIP gap tolerance (`MIPGap`), number of threads, and a random seed if applicable.

### Step 2 - Solve and Verify Termination
- Call the solver on the model and capture the results.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`) to ensure a valid solution is available.

### Step 3 - Extract and Analyze Solution
- Retrieve variable values using `pyo.value()` for `start`, `completion`, and the binary precedence/sequence variables.
- Reconstruct the operation sequence per job and per machine by inspecting the binary variable values.
- Validate the schedule by checking for constraint violations (e.g., overlaps, precedence satisfaction).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model
model = pyo.ConcreteModel()
# ... (define sets, parameters, variables, constraints, objective as per Modeling Stage)

# Solve
solver = pyo.SolverFactory('[SOLVER_NAME]')  # e.g., 'gurobi' or 'cbc'
solver.options['TimeLimit'] = [TIME_LIMIT]
solver.options['MIPGap'] = [GAP_TOLERANCE]
solver.options['Threads'] = [NUM_THREADS]
results = solver.solve(model, tee=True)  # tee=True prints solver log

# Check status and extract solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                             TerminationCondition.feasible)):
    makespan_value = pyo.value(model.makespan)
    schedule = {}
    for j in model.jobs:
        for m in model.machines:
            schedule[(j, m)] = (pyo.value(model.start[j, m]),
                                pyo.value(model.completion[j, m]))
    # ... (process schedule)
else:
    print("No solution found.")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to extraction attempts from infeasible or error states.
- Using a solver without a proper license or installation (e.g., Gurobi); have a fallback like CBC.
- Ignoring solver logs; setting `tee=True` helps monitor progress and identify early issues like numerical instability.
