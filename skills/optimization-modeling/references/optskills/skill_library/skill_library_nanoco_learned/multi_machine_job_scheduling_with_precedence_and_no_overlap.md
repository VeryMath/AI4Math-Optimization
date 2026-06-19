---
name: Multi-Machine Job Scheduling with Precedence and No-Overlap
description: |
  Model and solve scheduling problems where jobs must be processed on multiple machines in a fixed sequence, with each machine handling only one job at a time, to minimize the overall completion time (makespan).

---
# Workflow 1 (Constraint Programming with Interval Variables)

## Modeling stage

### Strategy Overview
This workflow uses a Constraint Programming (CP) paradigm, leveraging native interval variables and global no-overlap constraints. It is highly effective for pure scheduling problems, offering a declarative and solver-efficient model.

### Step 1 - Define Problem Entities
- Define the set of jobs `J` and the set of machines `M`.
- Define the processing time `p[j][m]` for each job `j` on each machine `m`.
- Define the job routing `route[j]` as an ordered list of machines for each job.
- Calculate a reasonable time horizon `H` (e.g., sum of all processing times) for variable bounds.

### Step 2 - Create Interval Variables
- For each job `j` and each machine `m` in its routing `route[j]`, create an interval variable `interval[j][m]`.
- The interval is defined by its start time, processing duration (`p[j][m]`), and end time.
- This single construct implicitly links start, duration, and end, simplifying constraint writing.

### Step 3 - Enforce Precedence Chain
- For each job `j`, enforce that its operation on machine `m_{k+1}` starts after its operation on machine `m_k` finishes, according to its routing.
- Add constraints: `end_before_start(interval[j][m_k], interval[j][m_{k+1}])` for all consecutive machines in `route[j]`.

### Step 4 - Enforce Machine Capacity
- For each machine `m`, collect all interval variables for that machine into a list `intervals_on_m`.
- Add a single `no_overlap(intervals_on_m)` constraint. This ensures intervals do not overlap in time on the same resource.

### Step 5 - Define Makespan Objective
- Create a single integer or continuous variable `makespan`.
- For each job `j`, constrain `makespan` to be greater than or equal to the end time of its final operation: `makespan >= end_of(interval[j][last_machine])`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "J: Set of jobs.",
    "M: Set of machines.",
    "route[j]: Ordered list of machines for job j."
  ],
  "parameters": [
    "p[j][m]: Processing time of job j on machine m."
  ],
  "decision_variables": [
    "interval[j][m]: Interval variable representing the processing of job j on machine m.",
    "makespan: Variable representing the maximum completion time."
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "Precedence: end_before_start(interval[j][m_k], interval[j][m_{k+1}]) for all j in J, for consecutive machines m_k, m_{k+1} in route[j].",
    "MachineNoOverlap: no_overlap([interval[j][m] for j in J if m in route[j]]) for all m in M.",
    "MakespanDefinition: makespan >= end_of(interval[j][route[j][-1]]) for all j in J."
  ]
}
```

### Common Pitfalls
- Forgetting to bound the start time domains of interval variables, which can lead to inefficient search. Always provide a sensible upper bound (horizon `H`).
- Misindexing the machine sequence in precedence constraints, especially if job routings are not uniform.
- Defining `makespan` as a parameter instead of a variable, preventing its minimization.

## Solving stage

### Strategy Overview
Solve the model using a CP solver (e.g., OR-Tools CP-SAT) that natively supports interval variables and global constraints. Configure search parameters for a balance between solution speed and quality.

### Step 1 - Solver and Model Initialization
- Instantiate the CP model object (e.g., `CpModel`).
- Define the horizon `H` as the sum of all processing times plus a buffer.

### Step 2 - Variable and Constraint Creation
- Create interval variables using the solver's factory method (e.g., `NewIntervalVar`), providing lower/upper bounds for start and end.
- Add precedence and no-overlap constraints using the model's methods.
- Define the `makespan` variable and its linking constraints.

### Step 3 - Solver Configuration
- Set a time limit (e.g., `max_time_in_seconds`) appropriate for the problem size.
- Enable parallel search by setting `num_search_workers` to the number of available CPU cores.
- Optionally set a `random_seed` for reproducible results.

### Step 4 - Execute Solve and Check Status
- Call the solver's `Solve` method on the model.
- Check the returned status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).
- If the status is not `FEASIBLE` or `OPTIMAL`, implement fallback logic (e.g., relax constraints, increase time limit).

### Step 5 - Extract and Validate Solution
- If feasible, extract the start and end times for each interval variable.
- Programmatically verify that all constraints hold: precedence is respected, no intervals on the same machine overlap, and the reported makespan matches the maximum end time.
- Format the schedule into a readable structure (e.g., list of (job, machine, start, end) tuples).

### Code Usage
```python
# Example using OR-Tools CP-SAT
from ortools.sat.python import cp_model

# 1. Initialize Model
model = cp_model.CpModel()
horizon = sum(p[j][m] for j in J for m in route[j])

# 2. Create Variables
intervals = {}
for j in J:
    for m in route[j]:
        start_var = model.NewIntVar(0, horizon, f'start_{j}_{m}')
        end_var = model.NewIntVar(0, horizon, f'end_{j}_{m}')
        interval_var = model.NewIntervalVar(start_var, p[j][m], end_var, f'interval_{j}_{m}')
        intervals[(j, m)] = (start_var, end_var, interval_var)

makespan = model.NewIntVar(0, horizon, 'makespan')

# 3. Add Constraints
# Precedence
for j in J:
    r = route[j]
    for idx in range(len(r) - 1):
        m1, m2 = r[idx], r[idx+1]
        model.Add(intervals[(j, m2)][0] >= intervals[(j, m1)][1])

# No-overlap per machine
for m in M:
    machine_intervals = [intervals[(j, m)][2] for j in J if m in route[j]]
    if machine_intervals:
        model.AddNoOverlap(machine_intervals)

# Makespan definition
for j in J:
    last_machine = route[j][-1]
    model.Add(makespan >= intervals[(j, last_machine)][1])

# 4. Set Objective
model.Minimize(makespan)

# 5. Configure and Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
# solver.parameters.random_seed = 42 # Optional
status = solver.Solve(model)

# 6. Process Result
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f'Makespan: {solver.Value(makespan)}')
    schedule = []
    for j in J:
        for m in route[j]:
            start = solver.Value(intervals[(j, m)][0])
            end = solver.Value(intervals[(j, m)][1])
            schedule.append((j, m, start, end))
    # ... process schedule
else:
    print('No feasible solution found.')
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to runtime errors.
- Setting an overly restrictive time horizon, which can make the problem infeasible.
- Ignoring solver logs; enabling `log_search_progress` can provide insights into search stagnation.

# Workflow 2 (Mixed-Integer Linear Programming with Disjunctive Constraints)

## Modeling stage

### Strategy Overview
This workflow uses a Mixed-Integer Linear Programming (MILP) formulation with binary sequencing variables and big-M constraints to model disjunctive machine capacity. It is portable across many MILP solvers and allows for integration with other linear constraints.

### Step 1 - Define Problem Entities
- Define the set of jobs `J` and the set of machines `M`.
- Define the processing time `p[j][m]` for each job `j` on each machine `m`.
- Define the job routing `route[j]` as an ordered list of machines for each job.
- Calculate a large constant `BigM` (e.g., sum of all processing times).

### Step 2 - Create Continuous Decision Variables
- Create continuous (or integer) variables `start[j][m]` representing the start time of job `j` on machine `m`.
- Optionally create `completion[j][m]` variables linked by constraint: `completion[j][m] == start[j][m] + p[j][m]`.
- Create a continuous variable `makespan`.

### Step 3 - Enforce Precedence Chain
- For each job `j` and consecutive machines `m_k`, `m_{k+1}` in its routing `route[j]`, add constraint: `start[j][m_{k+1}] >= start[j][m_k] + p[j][m_k]`.

### Step 4 - Model Machine Capacity with Binary Variables
- For each machine `m` and each pair of distinct jobs `j` and `k` that both require machine `m`, create a binary variable `precedes[j][k][m]`.
- `precedes[j][k][m] = 1` indicates job `j` is processed before job `k` on machine `m`.
- Enforce mutual exclusivity: `precedes[j][k][m] + precedes[k][j][m] == 1` for each unordered job pair.

### Step 5 - Implement Disjunctive Constraints via Big-M
- For each machine `m` and job pair `j, k` that both require `m`, add two conditional constraints using `BigM`:
    - If `precedes[j][k][m] == 1`, then `start[k][m] >= completion[j][m]`.
    - This is enforced as: `start[k][m] >= completion[j][m] - BigM * (1 - precedes[j][k][m])`.
    - The symmetric constraint for the opposite order is also added.

### Step 6 - Define Makespan Objective
- For each job `j`, add constraint: `makespan >= completion[j][last_machine]`.
- Set the objective to minimize `makespan`.

### Formulation Template
```json
{
  "sets": [
    "J: Set of jobs.",
    "M: Set of machines.",
    "route[j]: Ordered list of machines for job j."
  ],
  "parameters": [
    "p[j][m]: Processing time of job j on machine m.",
    "BigM: A sufficiently large number (e.g., sum(p[j][m] for all j, m))."
  ],
  "decision_variables": [
    "start[j][m]: Continuous variable for start time of job j on machine m.",
    "completion[j][m]: Continuous variable for completion time of job j on machine m.",
    "precedes[j][k][m]: Binary variable, 1 if job j precedes job k on machine m (defined only if both jobs require m).",
    "makespan: Continuous variable for the maximum completion time."
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "ProcessingTime: completion[j][m] == start[j][m] + p[j][m] for all j in J, m in route[j].",
    "Precedence: start[j][m_{k+1}] >= completion[j][m_k] for all j in J, for consecutive machines m_k, m_{k+1} in route[j].",
    "MutualExclusion: precedes[j][k][m] + precedes[k][j][m] == 1 for all m in M, j,k in J where j<k and both require m.",
    "Disjunctive1: start[k][m] >= completion[j][m] - BigM * (1 - precedes[j][k][m]) for all m in M, j,k in J, j!=k, where both require m.",
    "Disjunctive2: start[j][m] >= completion[k][m] - BigM * (1 - precedes[k][j][m]) for all m in M, j,k in J, j!=k, where both require m.",
    "MakespanDef: makespan >= completion[j][route[j][-1]] for all j in J."
  ]
}
```

### Common Pitfalls
- Choosing a `BigM` value that is too small, which can cut off valid solutions. Use a safe, large upper bound like the sum of all processing times.
- Choosing a `BigM` value that is excessively large, which weakens the linear relaxation and slows down the solver.
- Forgetting to enforce mutual exclusivity (`precedes[j][k][m] + precedes[k][j][m] == 1`) for all job pairs, leading to incorrect or infeasible models.
- Creating binary variables for job pairs that do not share a machine, unnecessarily increasing model size.

## Solving stage

### Strategy Overview
Solve the MILP model using a standard solver like Gurobi, CPLEX, or CBC. Configure MIP parameters to manage solution time and quality, and implement logic to handle non-optimal terminations.

### Step 1 - Model Building with a Modeling Language
- Use a modeling library (e.g., Pyomo, PuLP) to define sets, parameters, variables, and constraints based on the formulation.
- Ensure all indices and summations are correctly implemented, creating binary variables only for job pairs that share a machine.

### Step 2 - Solver Configuration
- Set a MIP gap tolerance (`MIPGap`) to define acceptable optimality (e.g., `[TARGET_GAP]`).
- Set a time limit (`TimeLimit`) appropriate for the problem size.
- Configure the number of threads (`Threads`) for parallel solving.
- Set a random seed (`Seed`) for reproducibility, if supported.

### Step 3 - Execute Solve and Check Termination
- Invoke the solver on the model instance.
- Check the termination condition (e.g., `optimal`, `feasible`, `timeLimit`).
- If the status is not optimal, assess the best bound and incumbent solution to gauge quality.

### Step 4 - Extract and Interpret Solution
- If a feasible solution exists, retrieve the values of `start[j][m]` and `precedes[j][k][m]` variables.
- Reconstruct the job sequence on each machine from the `precedes` variables.
- Validate the solution by checking all constraints programmatically.

### Step 5 - Analyze and Report
- Calculate the achieved makespan.
- Generate a Gantt chart or schedule table from the start times.
- Report the optimality gap if the solver terminated due to time limits.

### Code Usage
```python
# Example using Pyomo with Gurobi
import pyomo.environ as pyo

# 1. Create Concrete Model
model = pyo.ConcreteModel()

# 2. Define Sets and Parameters
model.J = pyo.Set(initialize=J) # Set of jobs
model.M = pyo.Set(initialize=M) # Set of machines
# Define processing times and routing
model.p = pyo.Param(model.J, model.M, initialize=p_data, default=0) # default 0 for unused pairs
# Determine which jobs require which machine
def job_requires_m(model, j, m):
    return m in route_data[j]
model.JobsOnMachine = pyo.Set(model.M, initialize=lambda model, m: [j for j in model.J if job_requires_m(model, j, m)])

BigM = sum(p_data[j][m] for j in J for m in route_data[j])

# 3. Define Variables
model.start = pyo.Var(model.J, model.M, domain=pyo.NonNegativeReals)
model.completion = pyo.Var(model.J, model.M, domain=pyo.NonNegativeReals)
model.precedes = pyo.Var(model.J, model.J, model.M, domain=pyo.Binary, initialize=0)
model.makespan = pyo.Var(domain=pyo.NonNegativeReals)

# 4. Define Constraints
# Processing time relation (only for required machines)
def processing_rule(model, j, m):
    if m in route_data[j]:
        return model.completion[j, m] == model.start[j, m] + model.p[j, m]
    return pyo.Constraint.Skip
model.processing = pyo.Constraint(model.J, model.M, rule=processing_rule)

# Precedence chain
def precedence_rule(model, j):
    route = route_data[j]
    constraints = []
    for idx in range(len(route)-1):
        m1, m2 = route[idx], route[idx+1]
        constraints.append(model.start[j, m2] >= model.completion[j, m1])
    return constraints
model.precedence = pyo.Constraint(model.J, rule=precedence_rule)

# Mutual exclusion for sequencing (only for jobs sharing a machine)
def mutual_excl_rule(model, m, j, k):
    if j < k and (j in model.JobsOnMachine[m] and k in model.JobsOnMachine[m]):
        return model.precedes[j, k, m] + model.precedes[k, j, m] == 1
    return pyo.Constraint.Skip
model.mutual_excl = pyo.Constraint(model.M, model.J, model.J, rule=mutual_excl_rule)

# Disjunctive constraints (only for jobs sharing a machine)
def disjunctive1_rule(model, m, j, k):
    if j != k and (j in model.JobsOnMachine[m] and k in model.JobsOnMachine[m]):
        return model.start[k, m] >= model.completion[j, m] - BigM * (1 - model.precedes[j, k, m])
    return pyo.Constraint.Skip
model.disjunctive1 = pyo.Constraint(model.M, model.J, model.J, rule=disjunctive1_rule)

def disjunctive2_rule(model, m, j, k):
    if j != k and (j in model.JobsOnMachine[m] and k in model.JobsOnMachine[m]):
        return model.start[j, m] >= model.completion[k, m] - BigM * (1 - model.precedes[k, j, m])
    return pyo.Constraint.Skip
model.disjunctive2 = pyo.Constraint(model.M, model.J, model.J, rule=disjunctive2_rule)

# Makespan definition
def makespan_rule(model, j):
    last_m = route_data[j][-1]
    return model.makespan >= model.completion[j, last_m]
model.makespan_def = pyo.Constraint(model.J, rule=makespan_rule)

# 5. Define Objective
model.obj = pyo.Objective(expr=model.makespan, sense=pyo.minimize)

# 6. Solve
solver = pyo.SolverFactory('gurobi') # or 'cplex', 'cbc'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0001
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model, tee=True) # tee=True prints solver log

# 7. Process Results
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    print(f'Optimal makespan: {pyo.value(model.makespan):.2f}')
    # Extract schedule from model.start and model.precedes
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    print(f'Feasible solution found. Makespan: {pyo.value(model.makespan):.2f}')
    print(f'Best bound: {results.problem.lower_bound:.2f}')
else:
    print('No feasible solution found.')
```

### Common Pitfalls
- Incorrectly indexing the "next" machine in the precedence constraint for non-consecutive or job-specific machine sequences.
- Creating an excessive number of binary variables (`|J|^2 * |M|`) for large instances, leading to intractable models. The refined code creates variables only for jobs sharing a machine.
- Not using `pyo.Constraint.Skip` correctly in rule-based constraint definitions, leading to errors for invalid index combinations.
