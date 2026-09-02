---
name: Permutation Flow Shop Scheduling
description: |
  Model and solve permutation flow shop problems with makespan minimization using either complete enumeration for small instances or MILP/CP-SAT formulations for larger ones, ensuring the same job order across all machines.
---

# Workflow 1 (Exact Enumeration & Dynamic Programming)

## Modeling stage

### Strategy Overview
For small problem instances (typically ≤ 6 jobs), the optimal permutation can be found by evaluating all possible job sequences. The modeling focuses on efficiently calculating the makespan for any given sequence using dynamic programming, which directly enforces the flow shop precedence and machine capacity constraints inherent to the permutation structure.

### Step 1 - Define Problem Data
- Identify the set of jobs and machines, along with the processing time for each job on each machine.
- Confirm the problem is a permutation flow shop: all jobs must be processed in the same order on every machine.

### Step 2 - Define Makespan Calculation Logic
- Implement a function that, given a job sequence, computes the completion time for each job on each machine using the standard flow shop recurrence.
- This recurrence inherently respects the precedence chain (job must finish on machine m-1 before starting on m) and machine non-overlap (only one job processed at a time per machine).

### Formulation Template
```json
{
  "sets": [
    {"name": "jobs", "description": "Set of all jobs to be scheduled."},
    {"name": "machines", "description": "Set of machines in the flow line, ordered by processing sequence."},
    {"name": "positions", "description": "Set of sequence positions, equal in size to the jobs set."}
  ],
  "parameters": [
    {"name": "processing_time", "set": ["jobs", "machines"], "description": "Time required to process job j on machine m."}
  ],
  "decision_variables": [
    {"name": "sequence", "type": "permutation", "set": ["jobs"], "description": "An ordered list of jobs defining the processing order on all machines."}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan",
    "description": "Minimize the total completion time of the last job on the last machine."
  },
  "constraints": [
    {"name": "makespan_definition", "description": "The makespan is the maximum completion time on the last machine, derived from the dynamic programming calculation."}
  ]
}
```

### Common Pitfalls
- Assuming the recurrence works for any shop configuration; it is valid only for pure flow shops where all jobs visit all machines in the same order.
- Not accounting for zero-indexing in implementation, leading to off-by-one errors in the completion time matrix.
- Forgetting that the dynamic programming table `completion[i][m]` represents the completion time of the job in sequence position `i` on machine `m`.

## Solving stage

### Strategy Overview
The solving stage involves generating all possible job permutations, evaluating the makespan for each using the dynamic programming function, and selecting the sequence with the minimal makespan. This guarantees optimality for exhaustively searchable instances.

### Step 1 - Enumerate Permutations
- Use `itertools.permutations` to generate all possible sequences of jobs.
- For each permutation, calculate its makespan using the predefined DP function.

### Step 2 - Evaluate and Select Optimal Sequence
- Track the best makespan and the corresponding sequence during enumeration.
- After evaluating all permutations, the best sequence is the optimal schedule.

### Step 3 - Extract Detailed Schedule
- Using the optimal sequence, re-run the DP calculation to populate the full `completion[i][m]` matrix.
- Derive start times for each operation as `start[i][m] = completion[i][m] - processing_time[sequence[i]][m]`.

### Code Usage
```python
import itertools

def calculate_makespan(seq, processing_times):
    """Calculate makespan for a given job sequence in a permutation flow shop."""
    n_jobs = len(seq)
    n_machines = len(processing_times[0])
    completion = [[0] * n_machines for _ in range(n_jobs)]
    for i, job in enumerate(seq):
        for m in range(n_machines):
            if i == 0 and m == 0:
                completion[i][m] = processing_times[job][m]
            elif i == 0:
                completion[i][m] = completion[i][m-1] + processing_times[job][m]
            elif m == 0:
                completion[i][m] = completion[i-1][m] + processing_times[job][m]
            else:
                completion[i][m] = max(completion[i-1][m], completion[i][m-1]) + processing_times[job][m]
    return completion[-1][-1]

# Main solving loop
best_makespan = float('inf')
best_sequence = None
for perm in itertools.permutations(jobs):
    makespan = calculate_makespan(perm, processing_times)
    if makespan < best_makespan:
        best_makespan = makespan
        best_sequence = perm
# best_sequence and best_makespan now hold the optimal solution
```

### Common Pitfalls
- Attempting full enumeration for n! > ~10000 permutations without considering runtime explosion.
- Not verifying the DP calculation with a manual example for a small instance.
- Storing all permutations and makespans in memory instead of tracking only the best during iteration.

# Workflow 2 (MILP with Position-Based Assignment)

## Modeling stage

### Strategy Overview
For larger instances where enumeration is impractical, model the problem as a Mixed-Integer Linear Program (MILP). Use binary assignment variables to assign jobs to sequence positions, and continuous variables to track completion times. This formulation explicitly captures the precedence and disjunctive constraints while maintaining the permutation flow shop structure.

### Step 1 - Define Assignment Variables
- Create binary variable `x[j, k]` which equals 1 if job `j` is assigned to sequence position `k`.
- Add constraints so each job is assigned to exactly one position and each position receives exactly one job.

### Step 2 - Define Completion Time Variables
- Create continuous variable `C[k, m]` representing the completion time of the job in position `k` on machine `m`.
- Link completion times across machines and positions using big-M or direct precedence constraints based on the assignment.

### Step 3 - Model Machine Precedence and Capacity
- For precedence (job flow): `C[k, m] >= C[k, m-1] + sum( x[j, k] * processing_time[j, m] for j in jobs )` for all k, m>0.
- For machine capacity (non-overlap): `C[k, m] >= C[k-1, m] + sum( x[j, k] * processing_time[j, m] for j in jobs )` for all k>0, m.

### Step 4 - Define Makespan Objective
- Define makespan variable `makespan` with constraints `makespan >= C[k, last_machine]` for all positions `k`.
- Set objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    {"name": "jobs", "description": "Set of all jobs."},
    {"name": "machines", "description": "Ordered set of machines."},
    {"name": "positions", "description": "Set of sequence positions, indexed 0..n-1."}
  ],
  "parameters": [
    {"name": "processing_time", "set": ["jobs", "machines"], "description": "Processing time p_{j,m}."},
    {"name": "M", "description": "Large enough constant for big-M constraints, e.g., sum of all processing times."}
  ],
  "decision_variables": [
    {"name": "x", "type": "binary", "set": ["jobs", "positions"], "description": "1 if job j is assigned to position k."},
    {"name": "C", "type": "continuous", "set": ["positions", "machines"], "description": "Completion time at position k on machine m."},
    {"name": "makespan", "type": "continuous", "description": "Maximum completion time."}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    {"name": "assign_each_job_once", "expression": "sum(x[j, k] for k in positions) == 1 for all j in jobs"},
    {"name": "fill_each_position", "expression": "sum(x[j, k] for j in jobs) == 1 for all k in positions"},
    {"name": "flow_precedence", "expression": "C[k, m] >= C[k, m-1] + sum(x[j, k] * processing_time[j, m] for j in jobs) for all k in positions, m in machines where m>0"},
    {"name": "machine_disjunctive", "expression": "C[k, m] >= C[k-1, m] + sum(x[j, k] * processing_time[j, m] for j in jobs) for all k in positions where k>0, m in machines"},
    {"name": "makespan_definition", "expression": "makespan >= C[k, last_machine] for all k in positions"},
    {"name": "nonnegative_C", "expression": "C[k, m] >= 0 for all k, m"}
  ]
}
```

### Common Pitfalls
- Using an insufficiently large big-M value, weakening the LP relaxation and slowing convergence.
- Incorrectly indexing the `C` variable bounds, leading to infeasibility or incorrect schedules.
- Forgetting to enforce non-negativity for completion time variables.

## Solving stage

### Strategy Overview
Implement the MILP model using a modeling language (e.g., Pyomo) and solve it with a capable MIP solver (e.g., Gurobi, HiGHS). Configure the solver for deterministic performance and optimality, and post-process the solution to extract the job sequence and detailed schedule.

### Step 1 - Model Instantiation
- Define sets, parameters, and variables as per the formulation.
- Add all constraints and the objective to the model.

### Step 2 - Solver Configuration
- Set a reasonable time limit (e.g., `TimeLimit=30`).
- Set optimality tolerance to zero (`MIPGap=0.0`) for an exact solution.
- Fix the random seed and number of threads for reproducibility (e.g., `Seed=42`, `Threads=4`).

### Step 3 - Solve and Check Status
- Invoke the solver and capture its termination status.
- Check if the solution is optimal or feasible. Handle timeouts or infeasibility with appropriate messages.

### Step 4 - Extract and Validate Solution
- Retrieve the values of `x[j, k]` to construct the optimal job sequence.
- Compute the makespan from the `C` variables or the objective value.
- As a sanity check, recalculate the makespan for the extracted sequence using the DP function from Workflow 1 to verify consistency.

### Code Usage
```python
import pyomo.environ as pyo

# Create model
model = pyo.ConcreteModel()
# Define sets
model.J = pyo.Set(initialize=jobs)
model.K = pyo.Set(initialize=positions)
model.M = pyo.Set(initialize=machines)
# Define parameters
model.p = pyo.Param(model.J, model.M, initialize=processing_time)
# Define variables
model.x = pyo.Var(model.J, model.K, domain=pyo.Binary)
model.C = pyo.Var(model.K, model.M, domain=pyo.NonNegativeReals)
model.makespan = pyo.Var(domain=pyo.NonNegativeReals)
# Add constraints (examples)
def assign_each_job_rule(model, j):
    return sum(model.x[j, k] for k in model.K) == 1
model.assign_job = pyo.Constraint(model.J, rule=assign_each_job_rule)
# ... Add other constraints ...
# Define objective
model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)
# Solve
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
results = solver.solve(model, tee=True)
# Check status and extract solution
if pyo.check_optimal_termination(results):
    # Extract sequence
    optimal_sequence = []
    for k in model.K:
        for j in model.J:
            if pyo.value(model.x[j, k]) > 0.5:
                optimal_sequence.append(j)
                break
    makespan_val = pyo.value(model.makespan)
```

### Common Pitfalls
- Not checking solver termination status, leading to errors when trying to extract values from an unsolved model.
- Using default solver parameters which may be non-deterministic or may not prove optimality.
- Misinterpreting the `x` variable matrix; ensure the extracted sequence respects the position ordering.
