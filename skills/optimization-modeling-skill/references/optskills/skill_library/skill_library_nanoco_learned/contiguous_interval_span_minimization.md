---
name: contiguous_interval_span_minimization
description: |
  Models and solves problems requiring assignment of contiguous intervals to entities with non-overlap and adjacency interference constraints, minimizing the overall span using MILP or constraint programming.
---

# Workflow 1 (MILP with Big-M Disjunctive Constraints)

## Modeling stage

### Strategy Overview
Model each entity's interval using a single integer start variable. Enforce pairwise non-overlap via binary variables and big-M disjunctive constraints. Minimize the maximum end index across all intervals.

### Step 1 - Define Interval Variables
- For each entity `i`, define an integer variable `start_index[i]` representing the starting point of its contiguous interval.
- The interval for entity `i` is `[start_index[i], start_index[i] + length[i] - 1]`.

### Step 2 - Introduce Span Objective
- Define a continuous or integer variable `M` representing the maximum end index across all intervals.
- Add constraints `M >= start_index[i] + length[i] - 1` for all `i`.
- Set the objective to minimize `M`.

### Step 3 - Encode Non-Overlap with Binary Variables
- For each pair `(i, j)` that must not overlap, introduce a binary variable `y[i,j]` indicating ordering (i before j if `y[i,j]=1`).
- Apply big-M disjunctive constraints:
  - `start_index[i] + length[i] <= start_index[j] + K * (1 - y[i,j])`
  - `start_index[j] + length[j] <= start_index[i] + K * y[i,j]`
- Choose `K` as a safe upper bound (e.g., sum of all interval lengths or a value larger than any feasible start index).

### Step 4 - Add Adjacency Interference Constraints
- If adjacency interference is required (e.g., intervals cannot be adjacent), modify the non-overlap constraints to enforce a gap:
  - `start_index[i] + length[i] + gap <= start_index[j] + K * (1 - y[i,j])`
  - `start_index[j] + length[j] + gap <= start_index[i] + K * y[i,j]`
- Set `gap` to the minimum separation required (e.g., 1 for no adjacency).

### Formulation Template
```json
{
  "sets": ["I: entities"],
  "parameters": ["length[i]: length of interval for entity i", "K: big-M upper bound", "gap: minimum separation between intervals"],
  "decision_variables": [
    "start_index[i] (integer): start point of interval for entity i",
    "M (continuous): maximum end index",
    "y[i,j] (binary): 1 if interval i is before interval j, for i<j"
  ],
  "objective": {
    "sense": "min",
    "expression": "M"
  },
  "constraints": [
    "M >= start_index[i] + length[i] - 1, for all i in I",
    "start_index[i] + length[i] + gap <= start_index[j] + K * (1 - y[i,j]), for all i<j in I",
    "start_index[j] + length[j] + gap <= start_index[i] + K * y[i,j], for all i<j in I"
  ]
}
```

### Common Pitfalls
- Choosing `K` too small, which can cut off feasible orderings; always set `K` larger than any possible start index (e.g., sum of all lengths).
- Forgetting to enforce `y[i,j]` only for `i<j` to avoid redundant constraints and symmetry.
- Omitting the gap constraint when adjacency interference is required, leading to invalid solutions.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., Gurobi, CPLEX) with explicit parameter settings. After solving, verify feasibility and validate all constraints programmatically.

### Step 1 - Configure Solver
- Set key parameters: `TimeLimit`, `MIPGap` (e.g., 0.0 for optimality), `Threads`, and `Seed` for reproducibility.
- Optionally enable solver-specific features like symmetry breaking or presolve aggressiveness.

### Step 2 - Solve and Check Status
- Solve the model and check `SolverStatus.ok` and `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- For infeasible models, output a JSON payload with status and reason (e.g., `{"status": "infeasible", "reason": "No feasible assignment exists"}`).

### Step 3 - Validate Solution
- After obtaining a solution, compute all intervals `[start_index[i], start_index[i] + length[i] - 1]` and verify pairwise non-overlap and gap constraints.
- Check that `M` equals the maximum end index across all intervals.

### Step 4 - Output Results
- Print the objective value using a consistent format: `RESULT:{float(pyo.value(model.obj))}`.
- For error or infeasible cases, output a JSON payload with status and reason.

### Code Usage
```python
import pyomo.environ as pyo

def build_model(entities, lengths, gap=0):
    model = pyo.ConcreteModel()
    model.I = pyo.Set(initialize=entities)
    model.length = pyo.Param(model.I, initialize=lengths)
    K = sum(lengths.values())  # safe upper bound
    model.K = pyo.Param(initialize=K)
    model.gap = pyo.Param(initialize=gap)

    model.start_index = pyo.Var(model.I, domain=pyo.NonNegativeIntegers)
    model.M = pyo.Var(domain=pyo.NonNegativeReals)
    model.y = pyo.Var(model.I, model.I, domain=pyo.Binary)

    def obj_rule(m):
        return m.M
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    def max_end_rule(m, i):
        return m.M >= m.start_index[i] + m.length[i] - 1
    model.max_end_con = pyo.Constraint(model.I, rule=max_end_rule)

    def non_overlap_rule(m, i, j):
        if i >= j:
            return pyo.Constraint.Skip
        return (m.start_index[i] + m.length[i] + m.gap <= m.start_index[j] + m.K * (1 - m.y[i,j]))
    model.non_overlap_con1 = pyo.Constraint(model.I, model.I, rule=non_overlap_rule)

    def non_overlap_rule2(m, i, j):
        if i >= j:
            return pyo.Constraint.Skip
        return (m.start_index[j] + m.length[j] + m.gap <= m.start_index[i] + m.K * m.y[i,j])
    model.non_overlap_con2 = pyo.Constraint(model.I, model.I, rule=non_overlap_rule2)

    return model

def solve_model(model, time_limit=60):
    solver = pyo.SolverFactory('gurobi')
    solver.options['TimeLimit'] = time_limit
    solver.options['MIPGap'] = 0.0
    solver.options['Threads'] = 4
    result = solver.solve(model, tee=False)
    if (result.solver.status == pyo.SolverStatus.ok and
        result.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
        print(f"RESULT:{float(pyo.value(model.obj))}")
    else:
        print('{"status": "error", "reason": "Solver did not find feasible solution"}')
```

### Common Pitfalls
- Trusting a non-zero return code or infeasible/unknown status; always check solver status explicitly.
- Outputting pseudo numeric answers when execution fails; use JSON error payloads instead.
- Forgetting to validate constraints after solving, which can catch numerical issues with big-M formulations.

# Workflow 2 (Constraint Programming with NoOverlap)

## Modeling stage

### Strategy Overview
Use constraint programming (CP) with interval variables and a built-in `NoOverlap` constraint. Minimize the makespan (maximum end point) using a CP optimizer.

### Step 1 - Define Interval Variables
- For each entity `i`, define an interval variable `interval[i]` with fixed size `length[i]`.
- The interval variable represents the contiguous assignment with start and end points determined by the solver.

### Step 2 - Enforce Non-Overlap
- Use the `NoOverlap` constraint on the set of all interval variables to prevent any two intervals from overlapping.
- For adjacency interference, add a `Distance` constraint between interval ends and starts (e.g., `end_of(interval[i]) + gap <= start_of(interval[j])` for all pairs).

### Step 3 - Minimize Makespan
- Define an integer variable `M` representing the maximum end point across all intervals.
- Add constraints `end_of(interval[i]) <= M` for all `i`.
- Set the objective to minimize `M`.

### Step 4 - Optional Search Phase
- Specify a search phase to guide the solver (e.g., `SearchPhase(interval_vars, FirstFail, SelectSmallestValue)`).
- This can improve performance for large instances.

### Formulation Template
```json
{
  "sets": ["I: entities"],
  "parameters": ["length[i]: size of interval for entity i", "gap: minimum separation between intervals"],
  "decision_variables": [
    "interval[i]: interval variable with size length[i]",
    "M (integer): makespan variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "M"
  },
  "constraints": [
    "NoOverlap(interval[i] for all i in I)",
    "end_of(interval[i]) + gap <= start_of(interval[j]) for all i<j in I (if adjacency interference)",
    "end_of(interval[i]) <= M for all i in I"
  ]
}
```

### Common Pitfalls
- Forgetting to set interval variable domains (start and end bounds) to realistic ranges, which can cause slow solving.
- Using `NoOverlap` without considering adjacency interference; add explicit distance constraints when needed.
- Not specifying a search phase for large instances, leading to poor solver performance.

## Solving stage

### Strategy Overview
Use a CP solver (e.g., CP-SAT from OR-Tools, IBM CP Optimizer) with interval variables. Set a time limit and log search progress.

### Step 1 - Configure Solver
- Set solver parameters: `TimeLimit`, `LogSearchProgress`, and `NumberOfWorkers`.
- For CP-SAT, enable `num_search_workers` and set `log_search_progress=True` for debugging.

### Step 2 - Solve and Check Status
- Solve the model and check the solver status (e.g., `OPTIMAL`, `FEASIBLE`, `INFEASIBLE`).
- For infeasible models, output a JSON payload with status and reason.

### Step 3 - Extract Solution
- Retrieve the start and end values for each interval variable using `solution.Start(interval[i])` and `solution.End(interval[i])`.
- Compute the makespan as the maximum end value.

### Step 4 - Output Results
- Print the objective value using a consistent format: `RESULT:{makespan}`.
- For error or infeasible cases, output a JSON payload with status and reason.

### Code Usage
```python
from ortools.sat.python import cp_model

def build_and_solve(entities, lengths, gap=0, time_limit=60):
    model = cp_model.CpModel()
    horizon = sum(lengths.values())  # safe upper bound for time horizon

    intervals = {}
    for i in entities:
        start_var = model.NewIntVar(0, horizon, f'start_{i}')
        end_var = model.NewIntVar(0, horizon, f'end_{i}')
        interval_var = model.NewIntervalVar(start_var, lengths[i], end_var, f'interval_{i}')
        intervals[i] = interval_var

    # NoOverlap constraint
    model.AddNoOverlap(list(intervals.values()))

    # Adjacency interference (gap)
    if gap > 0:
        for i in entities:
            for j in entities:
                if i < j:
                    model.Add(intervals[i].End + gap <= intervals[j].Start)

    # Makespan objective
    makespan = model.NewIntVar(0, horizon, 'makespan')
    for i in entities:
        model.Add(intervals[i].End <= makespan)
    model.Minimize(makespan)

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 4
    status = solver.Solve(model)

    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        print(f"RESULT:{solver.ObjectiveValue()}")
    else:
        print('{"status": "infeasible", "reason": "No feasible assignment exists"}')
```

### Common Pitfalls
- Not setting a time limit, causing the solver to run indefinitely on large instances.
- Ignoring the solver's log output, which can provide insights into search progress and bottlenecks.
- Assuming optimality without checking the status; always verify `OPTIMAL` or `FEASIBLE` before using results.
