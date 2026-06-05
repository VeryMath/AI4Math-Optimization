---
name: Discrete Assignment with Min-Max Objective
description: |
  Model and solve problems requiring assignment of discrete choices to entities with exactly-one and conflict-avoidance constraints, minimizing the maximum assigned value.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Use integer variables for each entity's assigned value, with domain restrictions via allowed assignments. Model the min-max objective with an auxiliary variable and inequality constraints. Enforce conflicts with inequality constraints between entity variables.

### Step 1 - Define Entity Assignment Variables
- For each entity, create an integer variable with domain bounds set to the minimum and maximum of its allowed values: `model.NewIntVar(min_val, max_val, name)`.
- Restrict each variable to its specific allowed set using `model.AddAllowedAssignments([var], [[v] for v in allowed_list])`.

### Step 2 - Enforce Conflict Avoidance
- For each pair of entities that cannot share the same value, add a constraint `model.Add(var_i != var_j)`.

### Step 3 - Model Min-Max Objective
- Create an auxiliary integer variable `max_used` with domain from the global minimum possible value to the global maximum possible value.
- Add constraints `model.Add(max_used >= var_i)` for every entity variable.
- Set objective: `model.Minimize(max_used)`.

### Formulation Template
```json
{
  "sets": ["entities", "values"],
  "parameters": ["allowed_values[entity]", "conflict_pairs"],
  "decision_variables": [
    "assignment[entity] (integer, domain=allowed_values[entity])",
    "max_used (integer, domain=[min_value, max_value])"
  ],
  "objective": {
    "sense": "min",
    "expression": "max_used"
  },
  "constraints": [
    "assignment[i] != assignment[j] for each conflict pair (i,j)",
    "max_used >= assignment[entity] for all entities"
  ]
}
```

### Common Pitfalls
- Forgetting to restrict variable domains to allowed values, causing invalid assignments.
- Using `AddAllDifferent` instead of pairwise inequality constraints when conflicts are not all-to-all.
- Setting the auxiliary variable domain too narrow, causing infeasibility.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver with appropriate search parameters. Check solver status and extract assignments with structured output.

### Step 1 - Configure and Solve
- Create solver: `solver = cp_model.CpSolver()`
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = 8`, optionally `solver.parameters.random_seed = 42` for reproducibility.
- Solve: `status = solver.Solve(model)`

### Step 2 - Extract and Verify Results
- Check status: `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`
- Retrieve objective: `solver.ObjectiveValue()`
- Extract assignments: `solver.Value(assignment_var)` for each entity
- Validate that each assignment belongs to the entity's allowed set and that all conflict constraints are satisfied.

### Step 3 - Output Structured Result
- Build dictionary with keys: `status`, `objective`, `assignments`
- Use `json.dumps()` for output

### Code Usage
```python
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# Define variables
assignments = {}
for entity in entities:
    min_val = min(allowed_values[entity])
    max_val = max(allowed_values[entity])
    var = model.NewIntVar(min_val, max_val, f"assign_{entity}")
    model.AddAllowedAssignments([var], [[v] for v in allowed_values[entity]])
    assignments[entity] = var

# Conflict constraints
for (i, j) in conflict_pairs:
    model.Add(assignments[i] != assignments[j])

# Min-max objective
max_used = model.NewIntVar(0, max_value, "max_used")
for var in assignments.values():
    model.Add(max_used >= var)
model.Minimize(max_used)

solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
    result = {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "objective": solver.ObjectiveValue(),
        "assignments": {e: solver.Value(v) for e, v in assignments.items()}
    }
else:
    result = {"status": "failed", "solver_status": status}
print(json.dumps(result))
```

### Common Pitfalls
- Not checking for `FEASIBLE` status when optimality is not required.
- Forgetting to set a time limit, causing indefinite runtime on large instances.
- Using default solver parameters without tuning for problem size.

# Workflow 2 (MIP Solver)

## Modeling stage

### Strategy Overview
Use binary assignment variables for each entity-value pair. Enforce exactly-one assignment per entity, conflict avoidance with pairwise constraints, and model the min-max objective with a continuous auxiliary variable.

### Step 1 - Define Binary Assignment Variables
- Create binary variable `x[i, f]` for each entity `i` and each value `f` in its allowed set.
- Use `pyo.Var(entities, allowed_values, domain=pyo.Binary)`.

### Step 2 - Enforce Exactly One Assignment
- For each entity `i`, add constraint: `sum(x[i, f] for f in allowed_values[i]) == 1`.

### Step 3 - Restrict to Allowed Values
- For disallowed entity-value pairs, fix variable to 0: either skip creating the variable or add constraint `x[i, f] == 0`.

### Step 4 - Model Conflict Avoidance
- For each conflicting pair `(i, j)` and each value `f`, add constraint: `x[i, f] + x[j, f] <= 1`.

### Step 5 - Model Min-Max Objective
- Create continuous auxiliary variable `z` with domain `pyo.NonNegativeReals`.
- Add constraints: `z >= f * x[i, f]` for all entity-value pairs.
- Set objective: `pyo.Objective(expr=z, sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["entities", "values"],
  "parameters": ["allowed_values[entity]", "conflict_pairs"],
  "decision_variables": [
    "x[entity, value] (binary)",
    "z (continuous, non-negative)"
  ],
  "objective": {
    "sense": "min",
    "expression": "z"
  },
  "constraints": [
    "sum(x[i, f] for f in allowed_values[i]) == 1 for each entity i",
    "x[i, f] + x[j, f] <= 1 for each conflict pair (i,j) and each value f",
    "z >= f * x[i, f] for all entity-value pairs"
  ]
}
```

### Common Pitfalls
- Creating variables for all entity-value pairs instead of only allowed ones, increasing model size unnecessarily.
- Using integer variables instead of binary, which may slow down the MIP solver.
- Forgetting to fix disallowed assignments to 0, leading to invalid solutions.

## Solving stage

### Strategy Overview
Use a MIP solver (CBC, Gurobi, CPLEX) with appropriate options. Check solver status and termination condition before extracting results.

### Step 1 - Configure and Solve
- Instantiate solver: `solver = pyo.SolverFactory("cbc")`
- Set options: `solver.options["seconds"] = [TIME_LIMIT]`, `solver.options["ratio"] = 0.0`
- Solve: `results = solver.solve(model, tee=False)`

### Step 2 - Check Solver Status
- Verify `results.solver.status == pyo.SolverStatus.ok`
- Check termination condition: `results.solver.termination_condition` is `optimal` or `feasible`

### Step 3 - Extract and Validate Results
- Retrieve objective: `pyo.value(model.z)`
- Decode assignments: for each entity, find value where `pyo.value(model.x[i, f]) > 0.5`
- Validate that each assignment belongs to the entity's allowed set and that all conflict constraints are satisfied.

### Step 4 - Output Structured Result
- Output structured JSON with status, objective, and assignments

### Code Usage
```python
import pyomo.environ as pyo
import json

model = pyo.ConcreteModel()
# Define sets
model.entities = pyo.Set(initialize=entity_list)
model.values = pyo.Set(initialize=value_list)

# Binary assignment variables
model.x = pyo.Var(model.entities, model.values, domain=pyo.Binary)

# Exactly one assignment per entity
def exactly_one_rule(m, i):
    return sum(m.x[i, f] for f in m.values if (i, f) in allowed_pairs) == 1
model.exactly_one = pyo.Constraint(model.entities, rule=exactly_one_rule)

# Conflict avoidance
def conflict_rule(m, i, j, f):
    if (i, j) in conflict_pairs:
        return m.x[i, f] + m.x[j, f] <= 1
    return pyo.Constraint.Skip
model.conflict = pyo.Constraint(model.entities, model.entities, model.values, rule=conflict_rule)

# Min-max objective
model.z = pyo.Var(domain=pyo.NonNegativeReals)
def max_rule(m, i, f):
    return m.z >= f * m.x[i, f]
model.max_constraint = pyo.Constraint(model.entities, model.values, rule=max_rule)
model.objective = pyo.Objective(expr=model.z, sense=pyo.minimize)

solver = pyo.SolverFactory("cbc")
solver.options["seconds"] = [TIME_LIMIT]
solver.options["ratio"] = 0.0
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
        assignments = {}
        for i in model.entities:
            for f in model.values:
                if pyo.value(model.x[i, f]) > 0.5:
                    assignments[i] = f
                    break
        result = {
            "status": str(results.solver.termination_condition),
            "objective": float(pyo.value(model.z)),
            "assignments": assignments
        }
    else:
        result = {"status": "failed", "termination": str(results.solver.termination_condition)}
else:
    result = {"status": "failed", "solver_status": str(results.solver.status)}
print(json.dumps(result))
```

### Common Pitfalls
- Not checking both `status` and `termination_condition`, leading to reading invalid results.
- Using `tee=True` in production, which can produce excessive output.
- Forgetting to convert Pyomo values to native Python types before JSON serialization.
