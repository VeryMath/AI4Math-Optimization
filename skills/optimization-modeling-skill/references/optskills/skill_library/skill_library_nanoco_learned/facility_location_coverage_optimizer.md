---
name: Facility Location Coverage Optimizer
description: |
  Models and solves a facility location problem with mandatory coverage and premium service tiers, minimizing net cost using binary activation and coverage variables.
---

# Workflow 1 (OR-Tools MIP Solver)

## Modeling stage

### Strategy Overview
Use Google OR-Tools' linear solver to formulate a mixed-integer program with binary activation variables for facilities and binary premium coverage variables for demand points. Precompute coverage sets to keep constraints sparse and linear.

### Step 1 - Precompute Coverage Sets
- For each demand point `i`, compute `mandatory_cover[i]`: list of candidate facilities within mandatory distance `R1`.
- For each demand point `i`, compute `premium_cover[i]`: list of candidate facilities within premium distance `R2`.
- **Feasibility Check**: Verify `mandatory_cover[i]` is non-empty for all `i`. If empty, the problem is infeasible with the given candidate sites and distance threshold.

### Step 2 - Define Binary Activation Variables
- Create `IntVar(0, 1)` for each candidate facility site `j` to represent activation `x[j]`.
- Use a dictionary indexed by facility IDs for easy access.

### Step 3 - Define Premium Coverage Variables
- Create `IntVar(0, 1)` for each demand point `i` to represent premium coverage `y[i]`.

### Step 4 - Enforce Mandatory Coverage Constraints
- For each demand point `i`, add constraint: `sum(x[j] for j in mandatory_cover[i]) >= 1`.

### Step 5 - Link Premium Coverage to Activation
- For each demand point `i`:
  - If `premium_cover[i]` is non-empty: add constraint `y[i] <= sum(x[j] for j in premium_cover[i])`.
  - If `premium_cover[i]` is empty: fix `y[i] == 0` to prevent solver errors and model infeasibility.

### Step 6 - Define Net Cost Objective
- Set objective to minimize: `sum(construction_cost[j] * x[j]) - sum(benefit[i] * y[i])`.
- Use `objective.SetCoefficient()` for each term and `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": ["I: demand points", "J: candidate facility sites"],
  "parameters": ["construction_cost[j]", "benefit[i]", "mandatory_cover[i]", "premium_cover[i]"],
  "decision_variables": [
    "x[j] ∈ {0,1}: facility activation",
    "y[i] ∈ {0,1}: premium coverage indicator"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{j∈J} construction_cost[j] * x[j] - sum_{i∈I} benefit[i] * y[i]"
  },
  "constraints": [
    "sum_{j∈mandatory_cover[i]} x[j] >= 1, ∀i∈I",
    "y[i] <= sum_{j∈premium_cover[i]} x[j], ∀i∈I where premium_cover[i] ≠ ∅",
    "y[i] == 0, ∀i∈I where premium_cover[i] = ∅"
  ]
}
```

### Common Pitfalls
- Forgetting to fix `y[i] = 0` for demand points with empty premium coverage sets, which can cause solver errors or unintended behavior.
- Using distance calculations inside constraint loops instead of precomputing coverage sets, leading to performance degradation.
- Not verifying mandatory coverage feasibility before solving.

## Solving stage

### Strategy Overview
Use OR-Tools' SCIP solver for mixed-integer problems. Set time limits and thread counts for practical solve times. Parse results with status checks and output structured JSON.

### Step 1 - Configure Solver
- Create solver with `pywraplp.Solver.CreateSolver("SCIP")`.
- Set time limit: `solver.SetTimeLimit([TIME_LIMIT_MS])` (e.g., 60000 for 60 seconds).
- Enable multi-threading: `solver.SetNumThreads([THREAD_COUNT])`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Accept both `pywraplp.Solver.OPTIMAL` and `pywraplp.Solver.FEASIBLE` as valid outcomes.

### Step 3 - Extract Solution
- For binary variables, check `variable.solution_value() > 0.5` to determine activation.
- Collect activated facility IDs and premium-covered demand points.

### Step 4 - Verify and Output
- **Verification Loop**: Independently verify mandatory coverage constraints by checking distances against chosen sites. Verify each premium-covered demand point has at least one activated facility within `R2`.
- Print results as JSON prefixed with `RESULT_JSON:` including status, objective value, and decision summaries.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Precompute coverage sets (Step 1)
mandatory_cover = {i: [j for j in facilities if dist[i][j] <= R1] for i in demands}
premium_cover = {i: [j for j in facilities if dist[i][j] <= R2] for i in demands}

# Feasibility check
for i in demands:
    if not mandatory_cover[i]:
        raise ValueError(f"Demand point {i} has no mandatory coverage candidate.")

solver = pywraplp.Solver.CreateSolver("SCIP")
solver.SetTimeLimit([TIME_LIMIT_MS])
solver.SetNumThreads([THREAD_COUNT])

# Decision variables
x = {j: solver.IntVar(0, 1, f"x_{j}") for j in facilities}
y = {i: solver.IntVar(0, 1, f"y_{i}") for i in demands}

# Mandatory coverage constraints
for i in demands:
    solver.Add(sum(x[j] for j in mandatory_cover[i]) >= 1)

# Premium coverage linkage
for i in demands:
    if premium_cover[i]:
        solver.Add(y[i] <= sum(x[j] for j in premium_cover[i]))
    else:
        solver.Add(y[i] == 0)

# Objective
objective = solver.Objective()
for j in facilities:
    objective.SetCoefficient(x[j], construction_cost[j])
for i in demands:
    objective.SetCoefficient(y[i], -benefit[i])  # Negative for benefit
objective.SetMinimization()

status = solver.Solve()
if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
    activated = [j for j in facilities if x[j].solution_value() > 0.5]
    premium_covered = [i for i in demands if y[i].solution_value() > 0.5]
    # Verification
    for i in demands:
        if not any(dist[i][j] <= R1 for j in activated):
            raise RuntimeError(f"Mandatory coverage violated for demand point {i}")
    for i in premium_covered:
        if not any(dist[i][j] <= R2 for j in activated):
            raise RuntimeError(f"Premium coverage violated for demand point {i}")
    result = {
        "status": "OPTIMAL" if status == pywraplp.Solver.OPTIMAL else "FEASIBLE",
        "objective": objective.Value(),
        "activated_facilities": activated,
        "premium_covered": premium_covered
    }
    print(f"RESULT_JSON:{result}")
else:
    print(f'RESULT_JSON:{{"status": "INFEASIBLE", "solver_status": {status}}}')
```

### Common Pitfalls
- Not checking solver status before accessing solution values, causing runtime errors on infeasible models.
- Using `solution_value()` directly for integer comparison without tolerance (e.g., `> 0.5` instead of `== 1.0`).

# Workflow 2 (Pyomo with CBC/HiGHS)

## Modeling stage

### Strategy Overview
Use Pyomo's algebraic modeling language to formulate the facility location problem with binary variables. Leverage constraint rules and precomputed distance sets for clean, maintainable code.

### Step 1 - Precompute Coverage Sets
- Compute `mandatory_cover[i]` and `premium_cover[i]` as immutable data structures (e.g., tuples or frozensets) before model construction.
- Verify mandatory coverage feasibility.

### Step 2 - Define Sets and Parameters
- Create Pyomo `Set` objects for demand points and candidate facilities.
- Define parameters for construction costs, premium benefits, and the precomputed coverage sets.

### Step 3 - Declare Binary Decision Variables
- Use `pyo.Var(domain=pyo.Binary)` for facility activation (`x[j]`).
- Use `pyo.Var(domain=pyo.Binary)` for premium coverage indicators (`y[i]`).

### Step 4 - Implement Mandatory Coverage Rule
- Write a constraint rule that sums activation variables over facilities in the mandatory coverage set for each demand point.
- Enforce the sum to be at least 1.

### Step 5 - Implement Premium Coverage Linkage
- For each demand point, add constraint: `y[i] <= sum(x[j] for j in premium_cover_set[i])` if the set is non-empty.
- For demand points with empty premium coverage sets, fix `y[i] = 0` explicitly.

### Step 6 - Define Net Cost Objective
- Express objective as: `sum(construction_cost[j] * x[j] for j in facilities) - sum(benefit[i] * y[i] for i in demands)`.
- Use `pyo.Objective(sense=pyo.minimize, rule=objective_rule)`.

### Formulation Template
```json
{
  "sets": ["I: demand points", "J: candidate facility sites"],
  "parameters": ["construction_cost[J]", "benefit[I]", "mandatory_cover[I]", "premium_cover[I]"],
  "decision_variables": [
    "x[J] ∈ {0,1}: facility activation",
    "y[I] ∈ {0,1}: premium coverage indicator"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{j∈J} construction_cost[j] * x[j] - sum_{i∈I} benefit[i] * y[i]"
  },
  "constraints": [
    "sum_{j∈mandatory_cover[i]} x[j] >= 1, ∀i∈I",
    "y[i] <= sum_{j∈premium_cover[i]} x[j], ∀i∈I where premium_cover[i] ≠ ∅",
    "y[i] == 0, ∀i∈I where premium_cover[i] = ∅"
  ]
}
```

### Common Pitfalls
- Using mutable lists inside constraint rules that change during construction; always use immutable data or deep copies.
- Forgetting to handle empty premium coverage sets, which can cause Pyomo to generate trivial constraints that break the model.

## Solving stage

### Strategy Overview
Use Pyomo's solver interface with CBC or HiGHS for MILP solving. Configure solver options for time limits and MIP gaps. Parse results with proper status checks and structured output.

### Step 1 - Configure Solver
- Create solver with `pyo.SolverFactory("cbc")` or `pyo.SolverFactory("highs")`.
- Set options: `solver.options["seconds"] = [TIME_LIMIT_S]` (e.g., 60), `solver.options["ratio"] = 0.0` for optimality.

### Step 2 - Solve and Check Status
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`.
- Accept both `TerminationCondition.optimal` and `TerminationCondition.feasible`.

### Step 3 - Extract Solution
- Read variable values using `pyo.value(model.x[j])` and `pyo.value(model.y[i])`.
- For binary variables, compare with `> 0.5` to determine activation.

### Step 4 - Verify and Output
- **Verification Loop**: Verify mandatory coverage by checking distances against activated facilities. Verify each premium-covered demand point has at least one activated facility within `R2`.
- Print objective value with `print(f"RESULT:{float(pyo.value(model.obj))}")`.
- On failure, print JSON with status, reason, and solver details.

### Code Usage
```python
import pyomo.environ as pyo

# Precompute coverage sets (Step 1)
mandatory_cover = {i: tuple(j for j in facilities if dist[i][j] <= R1) for i in demands}
premium_cover = {i: tuple(j for j in facilities if dist[i][j] <= R2) for i in demands}

# Feasibility check
for i in demands:
    if not mandatory_cover[i]:
        raise ValueError(f"Demand point {i} has no mandatory coverage candidate.")

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=demand_ids)
model.J = pyo.Set(initialize=facility_ids)

model.x = pyo.Var(model.J, domain=pyo.Binary)
model.y = pyo.Var(model.I, domain=pyo.Binary)

def mandatory_rule(m, i):
    return sum(m.x[j] for j in mandatory_cover[i]) >= 1
model.mandatory_con = pyo.Constraint(model.I, rule=mandatory_rule)

def premium_rule(m, i):
    if premium_cover[i]:
        return m.y[i] <= sum(m.x[j] for j in premium_cover[i])
    else:
        return m.y[i] == 0
model.premium_con = pyo.Constraint(model.I, rule=premium_rule)

def obj_rule(m):
    return sum(construction_cost[j] * m.x[j] for j in model.J) - sum(benefit[i] * m.y[i] for i in model.I)
model.obj = pyo.Objective(sense=pyo.minimize, rule=obj_rule)

solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = [TIME_LIMIT_S]
solver.options["ratio"] = 0.0

results = solver.solve(model, tee=False)
if results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
    activated = [j for j in model.J if pyo.value(model.x[j]) > 0.5]
    premium_covered = [i for i in model.I if pyo.value(model.y[i]) > 0.5]
    # Verification
    for i in model.I:
        if not any(dist[i][j] <= R1 for j in activated):
            raise RuntimeError(f"Mandatory coverage violated for demand point {i}")
    for i in premium_covered:
        if not any(dist[i][j] <= R2 for j in activated):
            raise RuntimeError(f"Premium coverage violated for demand point {i}")
    print(f"RESULT:{float(pyo.value(model.obj))}")
    print(f"Activated: {activated}, Premium covered: {premium_covered}")
else:
    print(f'{{"status": "FAIL", "reason": "{results.solver.termination_condition}"}}')
```

### Common Pitfalls
- Not setting `tee=False` in production, which can flood output with solver logs.
- Using `pyo.value()` on variables before solving, which raises an error; always check solver status first.
