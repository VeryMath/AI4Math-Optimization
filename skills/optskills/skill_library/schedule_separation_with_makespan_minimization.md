---
name: Schedule Separation with Makespan Minimization
description: |
  Model and solve scheduling problems with pairwise separation constraints and a makespan objective using integer programming techniques.

---
# Workflow 1 (CP-SAT with Absolute Value Constraints)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, which natively supports integer variables and constraints. It directly models absolute value constraints for pairwise separations, avoiding the need for big-M linearization and binary variables, leading to a concise and efficient formulation.

### Step 1 - Define Core Variables
- Define an integer decision variable for the start time of each entity (e.g., `t[i]`). Use `model.NewIntVar(lb, ub, name)` with appropriate lower and upper bounds.
- Define an auxiliary integer variable for the makespan (`makespan`). This variable will represent the maximum completion time.

### Step 2 - Link Makespan to Schedule
- For each entity `i`, add a constraint: `makespan >= t[i]`. This ensures the makespan variable correctly captures the latest start time.

### Step 3 - Enforce Pairwise Separations
- For each required separation `(u, v, d)`, enforce `|t[u] - t[v]| >= d`.
- Use the CP-SAT pattern `model.AddAbsEquality(abs_diff, diff)` to handle the absolute value, then constrain `abs_diff >= d`.
- Define `diff` as `t[u] - t[v]` and `abs_diff` as a non-negative integer variable.

### Step 4 - Set Objective
- Set the objective to minimize the makespan variable: `model.Minimize(makespan)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "entities", "description": "Set of all entities to be scheduled."},
    {"name": "dependencies", "description": "Set of pairwise separation requirements."}
  ],
  "parameters": [
    {"name": "separation_required", "set": "dependencies", "description": "Minimum required separation distance d for pair (u,v)."}
  ],
  "decision_variables": [
    {"name": "start_time", "set": "entities", "type": "integer", "bounds": "[lower_bound, upper_bound]"},
    {"name": "makespan", "type": "integer", "bounds": "[lower_bound, upper_bound]"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "makespan >= start_time[i] for all i in entities",
    "|start_time[u] - start_time[v]| >= separation_required[k] for all k in dependencies"
  ]
}
```

### Common Pitfalls
- Forgetting to define an upper bound for the `makespan` and `start_time` variables, which is required by CP-SAT.
- Using an insufficiently large range when creating the `abs_diff` variable, which can lead to constraint violations being missed.
- Not verifying the solution against the original separation constraints, especially when bounds are tight.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for a balance of speed and proof of optimality. Use parallel search and a time limit, then carefully extract and verify the solution.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set practical parameters: `solver.parameters.max_time_in_seconds`, `solver.parameters.num_search_workers`, and `solver.parameters.random_seed` for reproducibility.
- For optimality, set `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve(model)`.
- Check the status against `cp_model.OPTIMAL`, `cp_model.FEASIBLE`, or `cp_model.INFEASIBLE`. Handle each case appropriately (e.g., extract solution only if feasible).

### Step 3 - Extract and Verify Solution
- If a solution exists, retrieve variable values using `solver.Value(var)`.
- Programmatically verify all separation constraints by computing `abs(start_time[u] - start_time[v])` and comparing against the required distance `d`. This catches potential modeling or solver issues.

### Step 4 - Report Results
- Output the solver status, the optimal or best-found makespan, and the schedule of start times.
- For programmatic use, structure the output (e.g., as a JSON object containing status, objective value, and variable assignments).

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... define variables, constraints, objective
# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    makespan_value = solver.Value(makespan)
    schedule = {i: solver.Value(t[i]) for i in entities}
    # ... verification and output
else:
    # handle infeasible or unknown status
```

### Common Pitfalls
- Assuming `FEASIBLE` status means optimal. Check for `OPTIMAL` if a guaranteed optimum is required.
- Not using `solver.Value()` on variables before the solver is reset or the model goes out of scope.
- Ignoring the verification step, which is crucial for validating that the solver's solution satisfies all absolute difference constraints.

# Workflow 2 (MILP with Big-M Disjunctive Constraints)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Linear Program (MILP), suitable for solvers like Gurobi, CPLEX, or HiGHS. It uses a big-M method to linearize the disjunctive nature of pairwise separation constraints (`|a-b|>=d`), providing explicit control over the linear relaxation.

### Step 1 - Define Variables and Makespan
- Define non-negative integer variables for entity start times.
- Define a makespan variable and add constraints `makespan >= start_time[i]` for all `i`.

### Step 2 - Linearize Pairwise Separation Constraints
- For each separation requirement `(u, v, d)`, the constraint `|t_u - t_v| >= d` is equivalent to `t_u - t_v >= d OR t_v - t_u >= d`.
- Introduce a binary variable `y_k` for each dependency to model this disjunction.
- Use a big-M constant to formulate the linear constraints: `t_u - t_v >= d - M * (1 - y_k)` and `t_v - t_u >= d - M * y_k`.

### Step 3 - Set Objective
- Set the objective to minimize the makespan variable.

### Formulation Template
```json
{
  "sets": [
    {"name": "entities", "description": "Set of all entities to be scheduled."},
    {"name": "dependencies", "description": "Set of pairwise separation requirements."}
  ],
  "parameters": [
    {"name": "separation_required", "set": "dependencies", "description": "Minimum required separation distance d for pair (u,v)."},
    {"name": "big_M", "description": "A sufficiently large constant to deactivate constraints."}
  ],
  "decision_variables": [
    {"name": "start_time", "set": "entities", "type": "integer", "bounds": "[0, None]"},
    {"name": "makespan", "type": "integer", "bounds": "[0, None]"},
    {"name": "disjunction_selector", "set": "dependencies", "type": "binary"}
  ],
  "objective": {
    "sense": "min",
    "expression": "makespan"
  },
  "constraints": [
    "makespan >= start_time[i] for all i in entities",
    "start_time[u] - start_time[v] >= separation_required[k] - big_M * (1 - disjunction_selector[k]) for all k in dependencies",
    "start_time[v] - start_time[u] >= separation_required[k] - big_M * disjunction_selector[k] for all k in dependencies"
  ]
}
```

### Common Pitfalls
- Choosing a `big_M` value that is too small, which can cut off valid solutions.
- Choosing a `big_M` value that is excessively large, which can lead to numerical instability and slow convergence.
- Not declaring start time variables as integer, leading to a relaxed LP that may not satisfy integral separation requirements.

## Solving stage

### Strategy Overview
Configure a MILP solver with emphasis on finding and proving optimality. Use techniques like solving with an objective bound to verify optimality.

### Step 1 - Configure and Solve
- Instantiate the solver (e.g., `solver = pyo.SolverFactory('gurobi')`).
- Set key parameters: `time_limit`, `mipgap` (to 0.0 for optimality), `threads`, and `seed` for reproducibility.
- Solve the model and capture the termination condition.

### Step 2 - Check Solution Status
- Check the solver status (e.g., `ok`, `optimal`, `feasible`, `infeasible`) and the model termination condition (e.g., `optimal`, `maxTimeLimit`, `infeasible`).
- Only extract variable values if a feasible solution is reported.

### Step 3 - Verify Optimality via Bound Testing
- To confirm a candidate makespan `M*` is optimal, add a constraint `makespan <= M* - 1` and resolve.
- If the modified model is infeasible, then `M*` is optimal. This provides a simple proof of optimality.

### Step 4 - Extract and Verify Solution
- Extract the makespan and start time values.
- Perform post-solution verification by checking all separation constraints directly to ensure the big-M formulation behaved correctly.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, constraints, objective
# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs')
solver.options['time_limit'] = 30
solver.options['threads'] = 4
results = solver.solve(model, tee=False)
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    makespan_value = pyo.value(model.makespan)
    schedule = {i: pyo.value(model.start_time[i]) for i in model.entities}
    # ... verification and output
# ... optimality bound test
```

### Common Pitfalls
- Confusing solver status (did it run?) with model termination condition (what did it find?).
- Not setting an appropriate `mipgap` or `time_limit`, leading to excessively long runs or accepting suboptimal solutions.
- Forgetting to remove the optimality-testing constraint (`makespan <= M* - 1`) before proceeding or re-solving the original model.
