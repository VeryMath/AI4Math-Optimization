---
name: Weighted Set Cover Optimization
description: |
  Model and solve weighted set cover problems using binary selection variables, coverage constraints, and weighted sum minimization, with implementation options for both CP-SAT and MIP solvers.
---

# Workflow 1 (CP-SAT / OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the weighted set cover problem as a binary integer program using the OR-Tools CP-SAT solver interface. This approach is efficient for pure 0-1 problems and leverages the solver's native constraint propagation.

### Step 1 - Define Data Structures
- Represent the problem using two core dictionaries: one mapping each selectable item to its cost, and another mapping each element that must be covered to the list of items that can cover it.
- Use consistent, hashable keys (e.g., integers or strings) for both items and elements.

### Step 2 - Create Binary Variables
- Instantiate a `CpModel`.
- Create one binary (BoolVar) decision variable for each selectable item. A value of 1 indicates the item is selected.

### Step 3 - Formulate the Objective
- Define the objective to minimize the total weighted cost: the sum over all items of `(cost[item] * binary_variable[item])`.

### Step 4 - Add Coverage Constraints
- For each element requiring coverage, add a linear constraint: the sum of the binary variables for all items that cover that element must be greater than or equal to 1.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items (e.g., facilities, crews).",
    "J: Set of elements requiring coverage (e.g., locations, tasks)."
  ],
  "parameters": [
    "c_i: Cost/weight of selecting item i ∈ I.",
    "cover_j: List of item indices i ∈ I that can cover element j ∈ J."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1}: Binary variable indicating if item i is selected."
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_{i ∈ I} c_i * x_i"
  },
  "constraints": [
    "Coverage: For each j ∈ J, Σ_{i ∈ cover_j} x_i ≥ 1."
  ]
}
```

### Common Pitfalls
- Inefficiently iterating over all items for each coverage constraint. Use the precomputed `cover_j` list for direct access.
- Forgetting to set `relative_gap_limit = 0.0` when an exact optimal solution is required, which may allow early termination with a gap.
- Using float costs with CP-SAT; scale to integers if necessary for exact arithmetic.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver with parameters for timelimit, parallelism, and optimality guarantee. Extract the solution, verify its feasibility, and output structured results.

### Step 1 - Configure Solver Parameters
- Set a `max_time_in_seconds` to prevent indefinite runs.
- Specify `num_search_workers` for parallel search (often equal to available CPU cores).
- Set `random_seed` for reproducibility.
- Enforce exact optimization by setting `relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` statuses appropriately.

### Step 3 - Extract and Verify Solution
- Collect all items where the solver's value of the binary variable equals 1.
- Compute the total objective value from selected items.
- Programmatically verify that every element is covered by at least one selected item as a sanity check.

### Step 4 - Output Structured Results
- Package the results (status, objective value, selected items, verification flag) into a JSON object.
- Print the JSON with a consistent prefix (e.g., `RESULT_JSON:`) for automated parsing.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

# --- Data Placeholders ---
# costs = {item_id: cost_value, ...}
# coverage = {element_id: [item_ids], ...}

model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in costs}

# Objective
model.Minimize(sum(costs[i] * x[i] for i in costs))

# Constraints
for elem, covering_items in coverage.items():
    model.Add(sum(x[item] for item in covering_items) >= 1)

# Solver Setup
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

# Solve
status = solver.Solve(model)

# Result Processing
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in costs if solver.Value(x[i]) == 1]
    total_cost = sum(costs[i] for i in selected)
    # Verification
    coverage_ok = all(
        any(solver.Value(x[item]) == 1 for item in coverage[elem])
        for elem in coverage
    )
    result = {
        "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
        "objective": float(total_cost),
        "selected_items": selected,
        "coverage_verified": coverage_ok
    }
else:
    result = {"status": "failed", "reason": "infeasible_or_timeout"}
print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Not checking for both `OPTIMAL` and `FEASIBLE` statuses, potentially discarding good feasible solutions when time limits are hit.
- Assuming variable values are integers; always use `solver.Value()` to query the solution.
- Omitting solution verification, which can mask subtle solver or modeling errors.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract modeling components (Sets, Params, Vars), creating a portable MILP formulation. This decouples the model logic from the solver, allowing easy switching between open-source (HiGHS, CBC) and commercial (Gurobi) solvers.

### Step 1 - Define Pyomo Sets and Parameters
- Create a `ConcreteModel`.
- Define `Set` objects for items and elements.
- Define a `Param` for costs, indexed by the item set.
- Define a binary `Param` for the coverage relationship, indexed by (element, item), initialized via a rule or dictionary.

### Step 2 - Declare Binary Variables
- Create a `Var` indexed by the item set, with `domain=pyo.Binary`.

### Step 3 - Formulate the Objective
- Define an `Objective` to minimize the sum of `cost[item] * variable[item]` over all items.

### Step 4 - Implement Coverage Constraints
- Define a `Constraint` indexed by the element set.
- The rule for each constraint returns the expression: sum over items of `(coverage[element, item] * variable[item]) >= 1`.

### Formulation Template
```json
{
  "sets": [
    "I: Set of selectable items.",
    "J: Set of elements requiring coverage."
  ],
  "parameters": [
    "c_i: Cost of item i ∈ I.",
    "a_ji: Binary parameter, 1 if item i covers element j ∈ J, else 0."
  ],
  "decision_variables": [
    "x_i ∈ {0, 1}: Binary selection variable for item i."
  ],
  "objective": {
    "sense": "min",
    "expression": "Σ_{i ∈ I} c_i * x_i"
  },
  "constraints": [
    "Coverage: For each j ∈ J, Σ_{i ∈ I} a_ji * x_i ≥ 1."
  ]
}
```

### Common Pitfalls
- Initializing the large, sparse coverage parameter `a_ji` inefficiently. Use a rule that checks membership in a precomputed dictionary `cover[j]` to avoid dense storage.
- Using 1-based indexing from the problem data without converting to 0-based for internal use, causing index errors.
- Defining constraints with a `rule` function that has incorrect signature or side effects.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a chosen MIP solver. Configure solver options for time limit and optimality tolerance. Robustly check termination status, extract the solution, and verify feasibility.

### Step 1 - Select and Configure Solver
- Instantiate a solver via `SolverFactory("solver_name")` (e.g., "highs", "cbc", "gurobi").
- Set key options: `time_limit`, `mip_rel_gap` (set to 0.0 for exact optimality), and `threads`.

### Step 2 - Solve and Inspect Termination
- Call `solver.solve(model, tee=False)` (set `tee=True` for log output).
- Check the solver status (`SolverStatus.ok`) and the termination condition (`TerminationCondition.optimal` or `.feasible`).

### Step 3 - Extract Solution Values
- If the solve was successful, iterate over the item set and collect indices where `pyo.value(variable[item]) > 0.5`.
- Compute the objective value using `pyo.value(model.obj)`.

### Step 4 - Verify and Output Results
- Re-evaluate each coverage constraint with the selected solution to ensure numerical feasibility.
- Assemble results into a structured dictionary and output as JSON.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# --- Data Placeholders ---
# items = [item_ids]
# elements = [element_ids]
# cost_dict = {item_id: cost_value}
# coverage_dict = {element_id: [item_ids]}

model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=elements)

model.c = pyo.Param(model.I, initialize=cost_dict)

def coverage_rule(m, j, i):
    return 1 if i in coverage_dict.get(j, []) else 0
model.a = pyo.Param(model.J, model.I, initialize=coverage_rule)

model.x = pyo.Var(model.I, domain=pyo.Binary)

model.obj = pyo.Objective(
    expr=sum(model.c[i] * model.x[i] for i in model.I),
    sense=pyo.minimize
)

def cover_con_rule(m, j):
    return sum(m.a[j, i] * m.x[i] for i in m.I) >= 1
model.cover_con = pyo.Constraint(model.J, rule=cover_con_rule)

# Solve
solver = pyo.SolverFactory("highs")  # or "cbc", "gurobi"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
results = solver.solve(model, tee=False)

# Process Results
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in (TerminationCondition.optimal, TerminationCondition.feasible):
    selected = [i for i in model.I if pyo.value(model.x[i]) > 0.5]
    obj_val = pyo.value(model.obj)
    # Verification
    verified = all(
        sum(pyo.value(model.a[j, i]) * pyo.value(model.x[i]) for i in model.I) >= 0.999
        for j in model.J
    )
    result = {
        "status": "optimal" if term == TerminationCondition.optimal else "feasible",
        "objective": float(obj_val),
        "selected_items": selected,
        "coverage_verified": verified
    }
else:
    result = {"status": "failed", "reason": f"solver_status: {status}, termination: {term}"}
print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of results (e.g., `ok` status with `infeasible` termination).
- Using a loose tolerance (e.g., `> 0.5`) for binary variable value extraction without considering solver integrality tolerances.
- Forgetting to scale objective values if costs were scaled to integers for the solver, resulting in incorrect reported costs.
