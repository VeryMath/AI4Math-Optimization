---
name: Stable Matching Egalitarian Optimizer
description: |
  Builds and solves a one-to-one stable matching problem with no blocking pairs, minimizing the egalitarian score (sum of mutual preference ranks) using either constraint programming or mixed-integer linear programming.

---
# Workflow 1 (CP-SAT Constraint Programming)

## Modeling stage

### Strategy Overview
Model the stable matching problem as a binary assignment problem with explicit no-blocking-pair constraints. Use OR-Tools CP-SAT solver which handles logical constraints and binary variables efficiently for small to medium instances (up to ~7x7).

### Step 1 - Define Preference Rank Maps
- Convert each agent's preference list into zero-indexed rank dictionaries `rank_A[i][j]` and `rank_B[j][i]` for O(1) lookup of preference strength.
- Precompute for each pair `(i, j)` the sets `pref_A[i][j]` (partners `i` prefers over `j`) and `pref_B[i][j]` (partners `j` prefers over `i`).

### Step 2 - Declare Binary Assignment Variables
- Define `x[i, j]` as a `cp_model.NewBoolVar` for each pair `(i, j)` where `i` is from set A and `j` from set B.
- Variable equals 1 if `i` is matched to `j`, 0 otherwise.

### Step 3 - Enforce One-to-One Matching
- Add constraint `sum(x[i, j] for j in set_B) == 1` for each `i` in set A.
- Add constraint `sum(x[i, j] for i in set_A) == 1` for each `j` in set B.

### Step 4 - Add No-Blocking-Pair Constraints
- For each pair `(i, j)`, add the linear inequality:
  `x[i, j] + sum(x[i, jj] for jj in pref_A[i][j]) + sum(x[ii, j] for ii in pref_B[i][j]) >= 1`.
- This ensures if `i` and `j` are not matched, at least one is matched to a partner they prefer over the other.

### Step 5 - Define Egalitarian Objective
- Minimize `sum((rank_A[i][j] + rank_B[j][i]) * x[i, j] for all i, j)`.

### Formulation Template
```json
{
  "sets": ["A: set of agents in first group", "B: set of agents in second group"],
  "parameters": ["rank_A[i][j]: zero-indexed rank of j in i's preference list", "rank_B[j][i]: zero-indexed rank of i in j's preference list"],
  "decision_variables": ["x[i,j] binary: 1 if i matched to j, else 0"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A, j in B} (rank_A[i][j] + rank_B[j][i]) * x[i,j]"
  },
  "constraints": [
    "sum_{j in B} x[i,j] == 1 for all i in A",
    "sum_{i in A} x[i,j] == 1 for all j in B",
    "x[i,j] + sum_{jj in pref_A[i][j]} x[i,jj] + sum_{ii in pref_B[i][j]} x[ii,j] >= 1 for all i in A, j in B"
  ]
}
```

### Common Pitfalls
- Forgetting to zero-index ranks: preference positions must start at 0 for the objective to correctly represent egalitarian cost.
- Using `>=` instead of `==` for one-to-one constraints: each agent must be matched exactly once.
- Not precomputing `pref_A` and `pref_B` sets: computing them inside constraint generation loops causes performance degradation.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with parallel search and time limit. Extract the matching by iterating over all binary variables, then verify stability and compute objective value.

### Step 1 - Initialize Solver and Configure
- Create `cp_model.CpModel()` instance.
- Set solver parameters: `max_time_in_seconds=[TIME_LIMIT]` (e.g., 30), `num_search_workers=8`, `random_seed=42`, `relative_gap_limit=0.0`.

### Step 2 - Build Model and Solve
- Add all variables, constraints, and objective to the model.
- Call `solver.Solve(model)` and check status against `cp_model.OPTIMAL` or `cp_model.FEASIBLE`.

### Step 3 - Extract Matching
- Iterate over all `(i, j)` pairs and collect those where `solver.Value(x[i, j]) == 1`.
- Build a dictionary `matching[i] = j` and a reverse dictionary `reverse_matching[j] = i` for verification.

### Step 4 - Verify Stability
- For each pair `(i, j)` where `matching[i] != j`, check if `rank_A[i][j] < rank_A[i][matching[i]]` and `rank_B[j][i] < rank_B[j][reverse_matching[j]]`.
- If any such blocking pair exists, the solution is invalid; log a warning.

### Step 5 - Compute and Output Objective
- Compute `sum(rank_A[i][matching[i]] + rank_B[matching[i]][i] for all i)`.
- On success, output `RESULT:{objective_value}`. On failure, output a JSON error payload.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_stable_matching(A_prefs: dict, B_prefs: dict):
    n = len(A_prefs)
    # Build rank maps
    rank_A = {i: {j: pos for pos, j in enumerate(prefs)} for i, prefs in A_prefs.items()}
    rank_B = {j: {i: pos for pos, i in enumerate(prefs)} for j, prefs in B_prefs.items()}
    # Precompute preference sets for stability constraints
    pref_A = {i: {j: [jj for jj in range(n) if rank_A[i][jj] < rank_A[i][j]] for j in range(n)} for i in range(n)}
    pref_B = {j: {i: [ii for ii in range(n) if rank_B[j][ii] < rank_B[j][i]] for i in range(n)} for j in range(n)}

    model = cp_model.CpModel()
    x = {}
    for i in range(n):
        for j in range(n):
            x[i, j] = model.NewBoolVar(f'x_{i}_{j}')

    # One-to-one constraints
    for i in range(n):
        model.Add(sum(x[i, j] for j in range(n)) == 1)
    for j in range(n):
        model.Add(sum(x[i, j] for i in range(n)) == 1)

    # Stability constraints
    for i in range(n):
        for j in range(n):
            model.Add(x[i, j] +
                      sum(x[i, jj] for jj in pref_A[i][j]) +
                      sum(x[ii, j] for ii in pref_B[j][i]) >= 1)

    # Objective
    model.Minimize(sum((rank_A[i][j] + rank_B[j][i]) * x[i, j] for i in range(n) for j in range(n)))

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0

    status = solver.Solve(model)
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        matching = {i: j for i in range(n) for j in range(n) if solver.Value(x[i, j]) == 1}
        reverse_matching = {j: i for i, j in matching.items()}
        # Verify stability
        stable = True
        for i in range(n):
            for j in range(n):
                if matching[i] != j:
                    if (rank_A[i][j] < rank_A[i][matching[i]] and
                        rank_B[j][i] < rank_B[j][reverse_matching[j]]):
                        stable = False
                        break
            if not stable:
                break
        obj_val = sum(rank_A[i][matching[i]] + rank_B[matching[i]][i] for i in range(n))
        return {"status": "optimal" if status == cp_model.OPTIMAL else "feasible",
                "objective": obj_val,
                "matching": matching,
                "stable": stable}
    else:
        return {"status": "failed", "error": f"Solver status: {solver.StatusName(status)}"}
```

### Common Pitfalls
- Not checking solver status before extracting values: accessing `solver.Value()` on an unsolved model raises errors.
- Using `solver.Value()` on variables that are not part of the optimal solution: always verify status first.
- Forgetting to set `relative_gap_limit=0.0` for provably optimal solutions: default gap may stop early with a suboptimal result.

# Workflow 2 (MILP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the stable matching problem as a mixed-integer linear program using Pyomo. Use the same binary assignment variables and no-blocking-pair constraints, and leverage a MILP solver (e.g., HiGHS, Gurobi) for the solving stage.

### Step 1 - Build Preference Rank Maps
- Convert preference lists into zero-indexed rank dictionaries `rank_A[i][j]` and `rank_B[j][i]`.
- Precompute for each pair `(i, j)` the sets `pref_A[i][j]` and `pref_B[i][j]`.

### Step 2 - Define Pyomo Sets and Variables
- Create `pyo.Set` objects for sets A and B with integer indices `0..n-1`.
- Declare `pyo.Var(m.A, m.B, domain=pyo.Binary)` for assignment variables `m.x[i,j]`.

### Step 3 - Add One-to-One Matching Constraints
- Add constraint `sum(m.x[i, j] for j in m.B) == 1` for each `i` in `m.A`.
- Add constraint `sum(m.x[i, j] for i in m.A) == 1` for each `j` in `m.B`.

### Step 4 - Add Stability Constraints
- For each pair `(i, j)`, add constraint:
  `m.x[i, j] + sum(m.x[i, jj] for jj in pref_A[i][j]) + sum(m.x[ii, j] for ii in pref_B[i][j]) >= 1`.

### Step 5 - Set Egalitarian Objective
- Minimize `sum((rank_A[i][j] + rank_B[j][i]) * m.x[i, j] for i in m.A for j in m.B)`.

### Formulation Template
```json
{
  "sets": ["A: agents in first group (0..n-1)", "B: agents in second group (0..n-1)"],
  "parameters": ["rank_A[i][j]: zero-indexed rank of j in i's list", "rank_B[j][i]: zero-indexed rank of i in j's list"],
  "decision_variables": ["x[i,j] binary: 1 if i matched to j"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A, j in B} (rank_A[i][j] + rank_B[j][i]) * x[i,j]"
  },
  "constraints": [
    "sum_{j in B} x[i,j] == 1 for all i in A",
    "sum_{i in A} x[i,j] == 1 for all j in B",
    "x[i,j] + sum_{jj in pref_A[i][j]} x[i,jj] + sum_{ii in pref_B[i][j]} x[ii,j] >= 1 for all i in A, j in B"
  ]
}
```

### Common Pitfalls
- Using `pyo.Set(initialize=range(n))` without specifying `dimen`: for 1D sets this is fine, but for 2D parameter indexing ensure correct dimensionality.
- Forgetting to pass `m` as first argument in constraint rule functions: Pyomo rule functions must accept the model as first parameter.
- Not precomputing preference sets inside the rule function: computing them inside the rule causes repeated computation for each constraint evaluation.

## Solving stage

### Strategy Overview
Use a MILP solver (HiGHS recommended for open-source, Gurobi for commercial) via Pyomo's solver interface. Configure optimality gap and time limit, then extract and verify the solution.

### Step 1 - Initialize Solver
- Create solver instance: `solver = pyo.SolverFactory("highs")` or `solver = pyo.SolverFactory("gurobi")`.
- Set options: `solver.options["time_limit"] = [TIME_LIMIT]` (e.g., 60), `solver.options["mip_rel_gap"] = 0.0`.

### Step 2 - Solve Model
- Call `results = solver.solve(m, tee=True)` to see solver log.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract Matching
- Iterate over all `(i, j)` pairs and collect those where `pyo.value(m.x[i, j]) > 0.5`.
- Build matching dictionary `matching[i] = j` and reverse dictionary `reverse_matching[j] = i`.

### Step 4 - Verify Stability
- For each pair `(i, j)` where `matching[i] != j`, check if `rank_A[i][j] < rank_A[i][matching[i]]` and `rank_B[j][i] < rank_B[j][reverse_matching[j]]`.
- Print warning if any blocking pair is found.

### Step 5 - Output Results
- Compute objective value manually from extracted matching.
- Output JSON payload with keys `status`, `objective`, `matching`, and `stable`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_stable_matching_milp(A_prefs: dict, B_prefs: dict):
    n = len(A_prefs)
    # Build rank maps
    rank_A = {i: {j: pos for pos, j in enumerate(prefs)} for i, prefs in A_prefs.items()}
    rank_B = {j: {i: pos for pos, i in enumerate(prefs)} for j, prefs in B_prefs.items()}
    # Precompute preference sets for stability constraints
    pref_A = {i: {j: [jj for jj in range(n) if rank_A[i][jj] < rank_A[i][j]] for j in range(n)} for i in range(n)}
    pref_B = {j: {i: [ii for ii in range(n) if rank_B[j][ii] < rank_B[j][i]] for i in range(n)} for j in range(n)}

    m = pyo.ConcreteModel()
    m.A = pyo.Set(initialize=range(n))
    m.B = pyo.Set(initialize=range(n))
    m.x = pyo.Var(m.A, m.B, domain=pyo.Binary)

    # Objective
    m.obj = pyo.Objective(expr=sum((rank_A[i][j] + rank_B[j][i]) * m.x[i, j] for i in m.A for j in m.B),
                          sense=pyo.minimize)

    # One-to-one constraints
    def one_to_one_A_rule(mm, i):
        return sum(mm.x[i, j] for j in mm.B) == 1
    m.con_one_A = pyo.Constraint(m.A, rule=one_to_one_A_rule)

    def one_to_one_B_rule(mm, j):
        return sum(mm.x[i, j] for i in mm.A) == 1
    m.con_one_B = pyo.Constraint(m.B, rule=one_to_one_B_rule)

    # Stability constraints
    def stability_rule(mm, i, j):
        return (mm.x[i, j] +
                sum(mm.x[i, jj] for jj in pref_A[i][j]) +
                sum(mm.x[ii, j] for ii in pref_B[j][i]) >= 1)
    m.con_stability = pyo.Constraint(m.A, m.B, rule=stability_rule)

    # Solve
    solver = pyo.SolverFactory('highs')
    solver.options['time_limit'] = 60
    solver.options['mip_rel_gap'] = 0.0
    results = solver.solve(m, tee=True)

    if (results.solver.status == SolverStatus.ok and
        results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
        matching = {i: j for i in m.A for j in m.B if pyo.value(m.x[i, j]) > 0.5}
        reverse_matching = {j: i for i, j in matching.items()}
        # Verify stability
        stable = True
        for i in range(n):
            for j in range(n):
                if matching[i] != j:
                    if (rank_A[i][j] < rank_A[i][matching[i]] and
                        rank_B[j][i] < rank_B[j][reverse_matching[j]]):
                        stable = False
                        break
            if not stable:
                break
        obj_val = sum(rank_A[i][matching[i]] + rank_B[matching[i]][i] for i in range(n))
        status = "optimal" if results.solver.termination_condition == TerminationCondition.optimal else "feasible"
        return {"status": status, "objective": obj_val, "matching": matching, "stable": stable}
    else:
        return {"status": "failed",
                "error": f"Solver status: {results.solver.status}, termination: {results.solver.termination_condition}"}
```

### Common Pitfalls
- Not checking `results.solver.status` before accessing variable values: failed solves produce no valid solution.
- Using `pyo.value()` on variables that may not be fixed: always verify solver status first.
- Setting `mip_rel_gap` to 0.0 without a time limit: may cause extremely long solve times for larger instances; always set a time limit as a safety net.
