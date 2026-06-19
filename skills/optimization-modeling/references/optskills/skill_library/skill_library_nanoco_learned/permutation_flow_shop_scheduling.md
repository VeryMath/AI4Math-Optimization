---
name: Permutation Flow Shop Scheduling
description: |
  Model and solve permutation flow shop problems with makespan minimization using either CP-SAT with interval variables or MILP with position-based formulations.

---
# Workflow 1 (CP-SAT with Interval Variables)

## Modeling stage

### Strategy Overview
Model the problem using Constraint Programming (CP) concepts, specifically interval variables to represent job processing on each machine. This approach directly captures temporal relationships and uses native CP-SAT constraints for sequencing and resource capacity.

### Step 1 - Define Core Variables
- Create an interval variable for each job-machine pair, defined by its start time, processing duration, and end time.
- Define a single makespan variable, constrained to be greater than or equal to the completion time of every job on the last machine.
- Set a global time horizon as an upper bound, typically the sum of all processing times.

### Step 2 - Enforce Machine and Job Constraints
- Add a `NoOverlap` constraint on the interval variables for each machine to ensure only one job is processed at a time.
- For each job, add precedence constraints: the end time on machine `m` must be less than or equal to the start time on machine `m+1`.
- Link the makespan variable to the end times on the final machine.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Machines"
  ],
  "parameters": [
    "processing_time[j][m]"
  ],
  "decision_variables": [
    "interval[j][m] (start, size, end)",
    "makespan"
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "NoOverlap([interval[j][m] for j in Jobs]) for each m in Machines",
    "end_before_start(interval[j][m], interval[j][m+1]) for each j in Jobs, m in Machines except last",
    "makespan >= end(interval[j][last_machine]) for each j in Jobs"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large time horizon, which can make the model infeasible. Use the sum of all processing times.
- Forgetting to enforce the permutation rule (same job order on all machines). The `NoOverlap` constraint on each machine's intervals implicitly creates a sequence, but the job order must be consistent. This is enforced by using the same interval variable list per job across precedence constraints.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver, configured for scheduling problems. The solver natively handles interval and sequence constraints. After solving, extract the job sequence by sorting based on start times.

### Step 1 - Configure and Run Solver
- Instantiate the `CpSolver` and set key parameters: `max_time_in_seconds` for a time limit, `num_search_workers` for parallelism, and `random_seed` for reproducibility.
- For optimality proofs, set `relative_gap_limit = 0.0`.

### Step 2 - Extract and Validate Solution
- Check the solver status (`OPTIMAL` or `FEASIBLE`).
- Extract the start time values for each job on the first machine.
- Infer the job permutation by sorting jobs based on these start times.
- Perform a forward pass calculation using the extracted sequence and the standard flow shop recursion to verify the makespan and schedule consistency.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... (create interval variables, add constraints, set objective)
solver = cp_model.CpSolver()
# set parameters
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [NUM_WORKERS]
solver.parameters.random_seed = [SEED]
# solve with status / termination checks
status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract sequence
    starts_on_m0 = {j: solver.Value(start_var[j][0]) for j in jobs}
    sequence = sorted(jobs, key=lambda j: starts_on_m0[j])
    # Verify via forward pass
    verified_makespan = forward_pass_calc(sequence, processing_times)
else:
    print("No solution found.")
```

### Common Pitfalls
- Not checking solver status before extracting solution values, leading to runtime errors.
- Assuming the solver returns an optimal solution within the time limit; always handle feasible but non-optimal results.
- Incorrectly inferring sequence from unsorted start times that may have identical values; ensure a deterministic tie-breaker.

# Workflow 2 (MILP with Position-Based Formulation)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using binary assignment variables to link jobs to sequence positions. Continuous variables track completion times per position and machine, enabling a linear representation of the flow shop precedence rules.

### Step 1 - Define Assignment and Completion Variables
- Create binary variable `x[j, p]` = 1 if job `j` is assigned to sequence position `p`.
- Create continuous variable `C[p, m]` for the completion time of the job in position `p` on machine `m`.

### Step 2 - Enforce Permutation and Sequencing Logic
- Add constraints so each job is assigned to exactly one position and each position gets exactly one job.
- For the first position and machine, set the completion time based on the assigned job's processing time.
- For subsequent positions and machines, enforce the flow shop relationship using two linear constraints: `C[p, m] >= C[p-1, m] + processing_time` and `C[p, m] >= C[p, m-1] + processing_time`, where `processing_time` is summed over jobs using the `x[j, p]` variables.

### Step 3 - Define the Objective
- Define the makespan as the completion time of the last position on the last machine: `C[last_position, last_machine]`.
- Set the objective to minimize this makespan.

### Formulation Template
```json
{
  "sets": [
    "Jobs",
    "Positions",
    "Machines"
  ],
  "parameters": [
    "processing_time[j][m]"
  ],
  "decision_variables": [
    "x[j][p] ∈ {0,1}",
    "C[p][m] ≥ 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "C[last_position][last_machine]"
  },
  "constraints": [
    "sum(x[j][p] for p in Positions) == 1 for each j in Jobs",
    "sum(x[j][p] for j in Jobs) == 1 for each p in Positions",
    "C[1][1] == sum(processing_time[j][1] * x[j][1] for j in Jobs)",
    "C[p][m] >= C[p-1][m] + sum(processing_time[j][m] * x[j][p] for j in Jobs) for p>1, all m",
    "C[p][m] >= C[p][m-1] + sum(processing_time[j][m] * x[j][p] for j in Jobs) for m>1, all p"
  ]
}
```

### Common Pitfalls
- Using an insufficiently large "Big M" when linearizing disjunctive constraints is not needed in this formulation; the position-based model avoids this.
- Incorrectly indexing the initialization constraint for the first position and machine.
- Not ensuring the `Positions` set has the same cardinality as the `Jobs` set.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., Gurobi, HiGHS) via a modeling framework like Pyomo. Configure for optimality or time-limited search, extract the assignment variables to build the sequence, and validate the schedule.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `SolverFactory('[SOLVER_NAME]')`).
- Set parameters: `TimeLimit`, `MIPGap` (to 0.0 for optimality), `Threads`, and `Seed` for reproducibility.

### Step 2 - Process Solution and Verify
- Check the solver termination condition (`optimal`, `feasible`, or `timeLimit`).
- For each position `p`, find the job `j` where `x[j, p] > 0.5` to construct the sequence.
- Extract the makespan value from `C[last_position, last_machine]`.
- Optionally, verify the makespan by performing a forward pass calculation with the extracted sequence.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective)
solver = pyo.SolverFactory('[SOLVER_NAME]')
# solve with status / termination checks
results = solver.solve(model, options={'TimeLimit': [TIME_LIMIT], 'MIPGap': 0.0})
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract sequence
    sequence = []
    for p in model.Positions:
        for j in model.Jobs:
            if pyo.value(model.x[j, p]) > 0.5:
                sequence.append(j)
                break
    makespan = pyo.value(model.C[len(model.Jobs), len(model.Machines)])
    # Optional verification
    verified_makespan = forward_pass_calc(sequence, processing_times)
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print("Feasible solution found, may not be optimal.")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not verifying the solver status is `ok` before checking termination condition.
- Using a floating-point tolerance (e.g., 0.5) that is too tight for the solver's integrality tolerance when reading binary variables.
- Forgetting that Pyomo solution values are accessed via `pyo.value(var)` or `var.value`.
