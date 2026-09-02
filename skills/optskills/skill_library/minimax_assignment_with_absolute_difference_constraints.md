---
name: Minimax Assignment with Absolute Difference Constraints
description: |
  Build and solve optimization models that assign integer values to entities while enforcing minimum absolute differences between pairs and minimizing the maximum assigned value.

---
# Workflow 1 (CP-SAT with Boolean Encoding)

## Modeling stage

### Strategy Overview
Model the problem as a graph labeling problem where vertices represent entities and edges represent separation constraints. Use integer assignment variables with explicit bounds and encode absolute difference constraints via Boolean indicator variables. This approach leverages CP-SAT's native support for logical constraints and avoids big-M formulations.

### Step 1 - Define Assignment Variables
- Create an integer variable `x_i` for each entity `i` with domain `[0, U]`. Set `U` conservatively (e.g., `max_constraint_distance * number_of_entities` or a large constant like `[UPPER_BOUND]`).
- Use `model.NewIntVar(0, U, f"x_{i}")` for each entity index `i`.

### Step 2 - Encode Absolute Difference Constraints
- For each pair `(u, v, d)` requiring `|x_u - x_v| >= d`, introduce a Boolean variable `b` using `model.NewBoolVar(f"b_{u}_{v}")`.
- Add two conditional constraints:
  - `x_u - x_v >= d` enforced only when `b` is true: `model.Add(x_u - x_v >= d).OnlyEnforceIf(b)`
  - `x_v - x_u >= d` enforced only when `b` is false: `model.Add(x_v - x_u >= d).OnlyEnforceIf(b.Not())`

### Step 3 - Minimax Objective
- Create an auxiliary variable `max_x = model.NewIntVar(0, U, "max_x")`.
- Add constraints `model.Add(max_x >= x_i)` for all entities `i`.
- Set objective: `model.Minimize(max_x)`.

### Formulation Template
```json
{
  "sets": ["I: entities"],
  "parameters": ["E: set of (u, v, d) pairs requiring |x_u - x_v| >= d", "U: upper bound for assignment values"],
  "decision_variables": [
    "x_i: integer assignment for entity i, domain [0, U]",
    "b_e: Boolean variable for each edge e in E",
    "max_x: auxiliary variable for maximum assignment"
  ],
  "objective": {
    "sense": "min",
    "expression": "max_x"
  },
  "constraints": [
    "max_x >= x_i for all i in I",
    "For each (u, v, d) in E: x_u - x_v >= d if b_e is true",
    "For each (u, v, d) in E: x_v - x_u >= d if b_e is false"
  ]
}
```

### Common Pitfalls
- Choosing too small an upper bound `U` may make the problem infeasible; set it generously based on problem size.
- Forgetting to enforce both directions of the absolute difference constraint (only one direction is enforced per Boolean state).
- Not using `.OnlyEnforceIf(b.Not())` correctly — ensure the negation is applied to the same Boolean variable.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with parallel search and time limits. Extract results with status checking and output in structured JSON format.

### Step 1 - Configure Solver
- Create solver instance: `solver = cp_model.CpSolver()`
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = [N_WORKERS]`, `solver.parameters.random_seed = [SEED]`.

### Step 2 - Solve and Extract Results
- Call `status = solver.Solve(model)`.
- Check status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`.
- Retrieve values: `solver.Value(x_i)` for each entity, `solver.Value(max_x)` for objective.
- Compute objective as `float(solver.ObjectiveValue())`.

### Step 3 - Verify Solution and Prove Optimality
- **Verify Feasibility**: Explicitly check all absolute difference constraints `|x_u - x_v| >= d` are satisfied by the retrieved assignments.
- **Prove Optimality**: After finding a solution with objective `K`, attempt to find a feasible solution with `max_x <= K-1`. Infeasibility at the lower bound confirms optimality.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model
model = cp_model.CpModel()
x = {i: model.NewIntVar(0, U, f"x_{i}") for i in entities}
max_x = model.NewIntVar(0, U, "max_x")
for i in entities:
    model.Add(max_x >= x[i])

for (u, v, d) in edges:
    b = model.NewBoolVar(f"b_{u}_{v}")
    model.Add(x[u] - x[v] >= d).OnlyEnforceIf(b)
    model.Add(x[v] - x[u] >= d).OnlyEnforceIf(b.Not())

model.Minimize(max_x)

# Solve
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [N_WORKERS]
solver.parameters.random_seed = [SEED]
status = solver.Solve(model)

# Extract results
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = {i: solver.Value(x[i]) for i in entities}
    result = {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "objective": float(solver.ObjectiveValue()),
        "assignments": assignments,
        "max_assigned": solver.Value(max_x)
    }
else:
    result = {"status": "failed", "solver_status_code": status}
print(result)
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL` — feasible solutions may be acceptable.
- Forgetting to convert `solver.ObjectiveValue()` to float for JSON serialization.
- Using too few search workers for large instances; increase to match available cores.

# Workflow 2 (MILP with Big-M Disjunction)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program using big-M disjunctions for absolute difference constraints. This approach works with any MILP solver and provides a compact linear formulation.

### Step 1 - Define Assignment Variables
- Create integer variables `x_i` for each entity `i` with explicit bounds: `bounds=(0, U)` where `U` is a generous upper bound.
- Use `pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, U))` for each entity.

### Step 2 - Encode Absolute Difference Constraints with Big-M
- For each pair `(u, v, d)`, introduce a binary variable `y_e` (0 or 1).
- Add two constraints using big-M:
  - `x_u - x_v >= d - M * (1 - y_e)`
  - `x_v - x_u >= d - M * y_e`
- Set `M = U + max(d)` (or larger) to ensure the constraints are redundant when the binary variable is in the wrong state.

### Step 3 - Minimax Objective
- Add a variable `M_max` with domain `NonNegativeIntegers` and bounds `(0, U)`.
- Add constraints `M_max >= x_i` for all entities `i`.
- Set objective: `pyo.Objective(expr=M_max, sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I: entities"],
  "parameters": ["E: set of (u, v, d) pairs", "U: upper bound for assignment values", "M: big-M value, typically U + max(d)"],
  "decision_variables": [
    "x_i: integer assignment for entity i, bounds [0, U]",
    "y_e: binary variable for each edge e in E",
    "M_max: integer variable for maximum assignment, bounds [0, U]"
  ],
  "objective": {
    "sense": "min",
    "expression": "M_max"
  },
  "constraints": [
    "M_max >= x_i for all i in I",
    "For each (u, v, d) in E: x_u - x_v >= d - M * (1 - y_e)",
    "For each (u, v, d) in E: x_v - x_u >= d - M * y_e"
  ]
}
```

### Common Pitfalls
- Choosing too small a big-M value can cut off feasible solutions; ensure `M >= U + max(d)`.
- Not setting explicit bounds on integer variables, leading to unbounded search space.
- Forgetting that both big-M constraints must be added for each pair to enforce the absolute difference.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., HiGHS via Pyomo) with optimality gap set to zero and time limit. Extract results with proper status checking and output in structured format.

### Step 1 - Configure Solver
- Create solver: `solver = pyo.SolverFactory("highs")`
- Set options: `solver.options["time_limit"] = [TIME_LIMIT]`, `solver.options["mip_rel_gap"] = 0.0`, `solver.options["threads"] = [N_THREADS]`.

### Step 2 - Solve and Extract Results
- Call `result = solver.solve(model, tee=False)`.
- Check status: `result.solver.status == pyo.SolverStatus.ok` and `result.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}`.
- Extract values: `int(pyo.value(model.x[i]))` for each entity, `int(pyo.value(model.M_max))` for objective.

### Step 3 - Verify Solution and Prove Optimality
- **Verify Feasibility**: Explicitly check all absolute difference constraints `|x_u - x_v| >= d` are satisfied by the extracted assignments.
- **Prove Optimality**: After finding a solution with objective `K`, attempt to find a feasible solution with `M_max <= K-1`. Infeasibility at the lower bound confirms optimality.

### Code Usage
```python
import pyomo.environ as pyo

# Build model
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=entities)
model.E = pyo.Set(initialize=edges, dimen=3)

U = [UPPER_BOUND]  # generous upper bound
M = U + max(d for _, _, d in edges)

model.x = pyo.Var(model.I, domain=pyo.NonNegativeIntegers, bounds=(0, U))
model.y = pyo.Var(model.E, domain=pyo.Binary)
model.M_max = pyo.Var(domain=pyo.NonNegativeIntegers, bounds=(0, U))

# Objective
model.obj = pyo.Objective(expr=model.M_max, sense=pyo.minimize)

# Max constraints
def max_rule(m, i):
    return m.M_max >= m.x[i]
model.max_con = pyo.Constraint(model.I, rule=max_rule)

# Absolute difference constraints
model.abs_con = pyo.ConstraintList()
for u, v, d in edges:
    model.abs_con.add(model.x[u] - model.x[v] >= d - M * (1 - model.y[u, v, d]))
    model.abs_con.add(model.x[v] - model.x[u] >= d - M * model.y[u, v, d])

# Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = [TIME_LIMIT]
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = [N_THREADS]
result = solver.solve(model, tee=False)

# Extract results
if (result.solver.status == pyo.SolverStatus.ok and
    result.solver.termination_condition in {pyo.TerminationCondition.optimal,
                                            pyo.TerminationCondition.feasible}):
    assignments = {i: int(pyo.value(model.x[i])) for i in entities}
    output = {
        "status": "optimal" if result.solver.termination_condition == pyo.TerminationCondition.optimal else "feasible",
        "objective": float(pyo.value(model.M_max)),
        "assignments": assignments
    }
else:
    output = {"status": "failed", "solver_status": str(result.solver.status)}
print(output)
```

### Common Pitfalls
- Not converting Pyomo variable values to native Python types (int/float) before JSON serialization.
- Forgetting to set `mip_rel_gap = 0.0` for exact optimality when required.
- Using `tee=True` in production code — set to `False` to avoid excessive console output.
