---
name: Job Shop Scheduling with Disjunctive Constraints
description: |
  Model job shop scheduling problems using binary precedence variables and big-M constraints to sequence operations on shared machines, then solve via MIP with careful numerical tolerance settings and solution verification.
---

# Workflow 1 (Standard MIP with Gurobi)

## Modeling stage

### Strategy Overview
Formulate the job shop problem as a Mixed-Integer Program (MIP) using a disjunctive constraint formulation. Binary variables determine the precedence order between any two operations requiring the same machine. Continuous variables represent operation start times and the overall makespan.

### Step 1 - Define Problem Data Structures
- Define sets for jobs, operations per job, and machines.
- Create a parameter mapping each operation to its required machine.
- Define a parameter for the processing time of each operation.

### Step 2 - Create Decision Variables
- Create a continuous, non-negative variable for the start time of each operation.
- Create a continuous, non-negative variable for the makespan.
- For each unordered pair of operations assigned to the same machine, create a binary variable. A value of 1 indicates the first operation precedes the second.

### Step 3 - Formulate Constraints
- Add precedence constraints within each job: the start time of a successor operation must be at least the start time of its predecessor plus the predecessor's processing time.
- For each pair of operations sharing a machine, add two big-M constraints using the binary precedence variable to enforce sequencing in one direction.
- Link the makespan variable: it must be at least the completion time (start + processing) of every operation.

### Step 4 - Define Objective
- Set the objective to minimize the makespan variable.

### Formulation Template
```json
{
  "sets": [
    {"name": "Jobs", "description": "Set of all jobs"},
    {"name": "Operations", "description": "Set of operations for each job (e.g., (job, op_index))"},
    {"name": "Machines", "description": "Set of all machines"},
    {"name": "MachinePairs", "description": "Set of unordered operation pairs (op1, op2) that require the same machine"}
  ],
  "parameters": [
    {"name": "machine_assignment", "domain": "Operations -> Machines", "description": "Machine required for each operation"},
    {"name": "processing_time", "domain": "Operations -> Real+", "description": "Processing duration for each operation"},
    {"name": "M", "domain": "Real+", "description": "Sufficiently large constant for big-M constraints"}
  ],
  "decision_variables": [
    {"name": "start_time", "domain": "Operations >= 0", "type": "Continuous", "description": "Start time of each operation"},
    {"name": "makespan", "domain": ">= 0", "type": "Continuous", "description": "Maximum completion time"},
    {"name": "precedes", "domain": "MachinePairs in {0,1}", "type": "Binary", "description": "1 if first operation precedes second in the pair"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    {"name": "job_precedence", "expression": "start_time[succ] >= start_time[pred] + processing_time[pred] for all (pred, succ) in job sequences"},
    {"name": "disjunctive_order_1", "expression": "start_time[op2] >= start_time[op1] + processing_time[op1] - M * (1 - precedes[op1, op2]) for all (op1, op2) in MachinePairs"},
    {"name": "disjunctive_order_2", "expression": "start_time[op1] >= start_time[op2] + processing_time[op2] - M * precedes[op1, op2] for all (op1, op2) in MachinePairs"},
    {"name": "makespan_def", "expression": "makespan >= start_time[op] + processing_time[op] for all op in Operations"}
  ]
}
```

### Common Pitfalls
- Assuming or hardcoding machine assignments instead of reading them from a parameter, which solves a different problem.
- Creating duplicate binary variables for both orderings of an operation pair, leading to a redundant and larger model.
- Using a big-M constant that is too small (infeasible) or excessively large (causing numerical instability).
- Omitting validation that all required input parameters (machine assignments, processing times) are provided before building the model.

## Solving stage

### Strategy Overview
Solve the MIP using the Gurobi solver with tightened numerical tolerances to ensure the big-M constraints are respected precisely. After solving, verify the solution status and check the resulting schedule for constraint violations.

### Step 1 - Configure Solver and Solve
- Instantiate the Gurobi solver via Pyomo's `SolverFactory`.
- Set key options: `MIPGap=0.0` for optimality, `TimeLimit` to a reasonable value, `Threads` for parallelism, and `Seed` for reproducibility.
- Crucially, tighten feasibility and integer tolerances: `FeasibilityTol=1e-9`, `IntFeasTol=1e-9`.
- Call the solver with `tee=False` for clean output.

### Step 2 - Check Solver Status and Load Solution
- Check if the solver status is `ok`.
- Check the termination condition for `optimal` or `feasible`. Proceed only if one is met.
- If the solve was successful, load the solution into the model instance.

### Step 3 - Extract and Verify Schedule
- Extract the values of start time and precedence variables.
- Programmatically verify that all job precedence and machine disjunctive constraints are satisfied.
- Print a human-readable schedule (operation, machine, start, finish).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code based on formulation) ...

# Step 1: Configure and solve
solver = pyo.SolverFactory('gurobi')
solver.options['MIPGap'] = 0.0
solver.options['TimeLimit'] = 30
solver.options['Threads'] = 4
solver.options['Seed'] = 42
solver.options['FeasibilityTol'] = 1e-9
solver.options['IntFeasTol'] = 1e-9

results = solver.solve(model, tee=False)

# Step 2: Check status and load
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal,
                                             TerminationCondition.feasible]):
    model.solutions.load_from(results)
    # Step 3: Extract and verify
    schedule = {}
    for idx in model.Operations:
        schedule[idx] = pyo.value(model.start_time[idx])
    makespan_val = pyo.value(model.makespan)
    # ... Add verification logic ...
    print(f"Makespan: {makespan_val}")
else:
    print("Solve failed or no feasible solution found.")
```

### Common Pitfalls
- Accepting solver results without checking termination condition, potentially using an infeasible or suboptimal solution.
- Not tightening numerical tolerances, allowing the solver to exploit slack in big-M constraints, which can produce infeasible schedules.
- Failing to verify the extracted schedule against the original problem constraints, missing modeling errors.
- Using conflicting solver options or incorrect option names for the chosen solver.

# Workflow 2 (Time-Indexed MIP with HiGHS)

## Modeling stage

### Strategy Overview
Use a time-indexed formulation where binary variables indicate if an operation starts at a specific time period. This avoids big-M constraints but can lead to a larger model. The makespan is implicitly defined by the latest start time plus processing time.

### Step 1 - Define Time Horizon and Sets
- Estimate a reasonable time horizon `T` (e.g., sum of all processing times).
- Define sets for jobs, operations, machines, and discrete time periods `{0,...,T-1}`.
- Define parameters for machine assignment and processing time for each operation.

### Step 2 - Create Binary Decision Variables
- For each operation and each feasible start time `t` (where `t + processing_time <= T`), create a binary variable. It equals 1 if the operation starts at time `t`.
- Optionally, create a continuous makespan variable, or calculate it post-solve from the start times.

### Step 3 - Formulate Assignment and Sequencing Constraints
- Add a constraint that each operation must start exactly once within the time horizon.
- For each machine and each time period `t`, ensure the total "active" work (operations that are processing at time `t`) does not exceed 1. This is a cumulative resource constraint.
- Add job precedence constraints: the start time of a successor operation must be at least the start time of its predecessor plus processing time. This requires linearizing the relationship between the binary start variables.

### Step 4 - Define Objective
- Minimize the makespan. This can be expressed directly by minimizing the maximum completion time, often requiring auxiliary variables and constraints to linearize the `max` function.

### Formulation Template
```json
{
  "sets": [
    {"name": "Jobs", "description": "Set of all jobs"},
    {"name": "Operations", "description": "Set of operations (job, step)"},
    {"name": "Machines", "description": "Set of all machines"},
    {"name": "TimePeriods", "description": "Discrete time periods {0, 1, ..., T-1}"}
  ],
  "parameters": [
    {"name": "machine_assignment", "domain": "Operations -> Machines", "description": "Machine required for each operation"},
    {"name": "processing_time", "domain": "Operations -> Integer+", "description": "Processing duration for each operation"},
    {"name": "T", "domain": "Integer+", "description": "Time horizon upper bound"}
  ],
  "decision_variables": [
    {"name": "x", "domain": "Operations * TimePeriods in {0,1}", "type": "Binary", "description": "1 if operation starts at time t"},
    {"name": "makespan", "domain": ">= 0", "type": "Continuous", "description": "Maximum completion time"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    {"name": "start_exactly_once", "expression": "sum_{t in feasible_start[op]} x[op, t] == 1 for all op in Operations"},
    {"name": "machine_capacity", "expression": "sum_{op in Ops_m} sum_{tau in active_periods(op, t)} x[op, tau] <= 1 for all m in Machines, t in TimePeriods"},
    {"name": "job_precedence", "expression": "sum_{t} t * x[succ, t] >= sum_{t} t * x[pred, t] + processing_time[pred] for all (pred, succ) in job sequences"},
    {"name": "makespan_def", "expression": "makespan >= sum_{t} (t + processing_time[op]) * x[op, t] for all op in Operations"}
  ]
}
```

### Common Pitfalls
- Choosing an overly large time horizon `T`, which unnecessarily blows up the model size and solve time.
- Incorrectly formulating the machine capacity constraint by not correctly summing over the periods where an operation started at `tau` would be active at time `t`.
- Linearizing the job precedence constraint incorrectly, leading to invalid sequencing.
- Forgetting to enforce that operations cannot start at a time that would cause them to finish after `T`.

## Solving stage

### Strategy Overview
Solve the time-indexed MIP using the HiGHS solver. Due to the potentially large number of binary variables, focus on setting appropriate limits for gap and runtime. Handle solution loading carefully as HiGHS may not load solutions automatically on non-optimal terminates.

### Step 1 - Configure HiGHS Solver
- Instantiate the HiGHS solver via Pyomo's `SolverFactory`.
- Set options: `time_limit` for runtime control, `mip_rel_gap` for optimality tolerance.
- Avoid setting options not supported by HiGHS (e.g., `threads` may be managed internally).

### Step 2 - Solve and Check Termination
- Call the solver with `load_solutions=False` to prevent automatic loading of potentially incomplete solutions.
- Check the solver results object for status `ok` and a termination condition of `optimal` or `feasible`.

### Step 3 - Load Solution and Calculate Metrics
- If the termination is acceptable, manually load the solution into the model.
- Extract the start times by finding the time `t` where `x[op, t] == 1` for each operation.
- Compute the makespan from the loaded start times and processing times.

### Step 4 - Validate Schedule
- Reconstruct the schedule from the start times.
- Verify machine capacity constraints for each time period and job precedence constraints.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code for time-indexed formulation) ...

# Step 1 & 2: Configure, solve, and check
solver = pyo.SolverFactory('appsi_highs') # or 'highs' depending on Pyomo version
solver.options['time_limit'] = 60
solver.options['mip_rel_gap'] = 0.01

results = solver.solve(model, load_solutions=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal,
                                             TerminationCondition.feasible]):
    # Step 3: Load solution
    model.solutions.load_from(results)
    # Extract start times
    start_times = {}
    for op in model.Operations:
        for t in model.TimePeriods:
            if pyo.value(model.x[op, t]) > 0.5: # Check binary variable
                start_times[op] = t
                break
    # Calculate makespan
    makespan_calc = max(start_times[op] + model.processing_time[op] for op in model.Operations)
    # Step 4: Add validation logic
    print(f"Calculated Makespan: {makespan_calc}")
else:
    print("HiGHS solve did not return a usable solution.")
```

### Common Pitfalls
- Calling `solve()` without `load_solutions=False` and then trying to load results manually, causing conflicts.
- Not checking termination condition and assuming an optimal solution was found when the solver hit a time limit.
- Using an incorrect method to extract start times from the binary variables (e.g., not accounting for numerical tolerance when checking binary variable values).
- Setting solver options that are not applicable to HiGHS, causing warnings or errors.
