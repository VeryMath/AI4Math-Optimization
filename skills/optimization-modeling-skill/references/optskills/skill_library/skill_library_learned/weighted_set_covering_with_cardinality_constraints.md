---
name: Weighted Set Covering with Cardinality Constraints
description: |
  Formulate and solve weighted set covering problems where each element must be covered by a minimum required number of selected sets, minimizing total selection cost.

---
# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem as a binary integer program using the OR-Tools CP-SAT solver. This approach is ideal for pure 0-1 problems with linear constraints and objectives, leveraging a dedicated constraint programming solver for efficient search.

### Step 1 - Define Selection Variables
- Create a binary decision variable for each available set. For example, `x[i] = model.NewBoolVar(f"x_{i}")` where `i` is the set identifier.
- These variables indicate whether a set is selected (1) or not (0).

### Step 2 - Structure Coverage Requirements
- For each element `e` that requires coverage, identify the list of sets `cover_sets[e]` that can cover it.
- Add a linear constraint for each element: `model.Add(sum(x[i] for i in cover_sets[e]) >= required_coverage[e])`. This enforces the cardinality requirement.

### Step 3 - Formulate the Objective
- Define the objective to minimize the total cost of selected sets: `model.Minimize(sum(cost[i] * x[i] for i in all_sets))`.

### Formulation Template
```json
{
  "sets": ["S", "E"],
  "parameters": [
    {"name": "cost_s", "domain": "S", "description": "Cost of selecting set s"},
    {"name": "cover_sets_e", "domain": "E", "description": "List of set IDs that cover element e"},
    {"name": "required_coverage_e", "domain": "E", "description": "Minimum number of selected sets required to cover element e"}
  ],
  "decision_variables": [
    {"name": "x_s", "domain": "S", "type": "binary", "description": "1 if set s is selected"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_s * x_s for s in S)"
  },
  "constraints": [
    {"expression": "sum(x_s for s in cover_sets_e) >= required_coverage_e", "for_each": "e in E"}
  ]
}
```

### Common Pitfalls
- Forgetting to ensure `cover_sets_e` lists are non-empty for each element `e`.
- Using integer variables instead of boolean variables for pure selection decisions, which reduces solver efficiency.
- Incorrectly indexing parameters or variables when populating the model from data dictionaries.

## Solving stage

### Strategy Overview
Solve the formulated model using the CP-SAT solver, configuring it for a balance of speed and proof of optimality. Post-solve, rigorously verify that the solution satisfies all coverage requirements.

### Step 1 - Configure the Solver
- Instantiate the solver: `solver = cp_model.CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = 30`, `solver.parameters.num_search_workers = 8` for parallelism, and `solver.parameters.random_seed = 42` for reproducibility.
- For an exact solution, ensure `solver.parameters.relative_gap_limit = 0.0`.

### Step 2 - Solve and Check Status
- Execute the solve: `status = solver.Solve(model)`.
- Check if the status is `cp_model.OPTIMAL` or `cp_model.FEASIBLE`. Handle `cp_model.INFEASIBLE` or `cp_model.MODEL_INVALID` appropriately.

### Step 3 - Extract and Verify Solution
- If a solution was found, extract selected sets: `selected_sets = [i for i in all_sets if solver.Value(x[i]) == 1]`.
- Perform verification: for each element `e`, calculate `sum(solver.Value(x[i]) for i in cover_sets[e])` and assert it is `>= required_coverage[e]`.
- Compute and report the total cost from the solution values.

### Step 4 - Confirm Optimality (Optional)
- To prove optimality, add a constraint forcing a better objective: `model.Add(sum(cost[i] * x[i] for i in all_sets) <= best_cost - 1)`.
- Re-solve. If the status is `INFEASIBLE`, the previous solution is optimal.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
x = {i: model.NewBoolVar(f"x_{i}") for i in all_sets}
# coverage constraints
for e in elements:
    model.Add(sum(x[i] for i in cover_sets[e]) >= required_coverage[e])
# objective
model.Minimize(sum(cost[i] * x[i] for i in all_sets))

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    selected = [i for i in all_sets if solver.Value(x[i]) == 1]
    # verification loop
    for e in elements:
        coverage_count = sum(solver.Value(x[i]) for i in cover_sets[e])
        assert coverage_count >= required_coverage[e]
    print(f"RESULT:{solver.ObjectiveValue()}")
else:
    print("RESULT_JSON:{\"status\": \"infeasible_or_error\"}")
```

### Common Pitfalls
- Not verifying the solution satisfies all constraints, especially when `status` is `FEASIBLE` but not `OPTIMAL`.
- Misinterpreting the `status` codes; `OPTIMAL` confirms proven optimality, `FEASIBLE` does not.
- Setting an overly restrictive time limit (`max_time_in_seconds`) before a feasible solution is found.

# Workflow 2 (MILP with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
Model the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract or concrete model paradigm. This provides a declarative, solver-agnostic formulation that can interface with various MILP solvers like HiGHS.

### Step 1 - Define Model and Index Sets
- Create a Pyomo `ConcreteModel()`.
- Define index sets `model.S = pyo.Set(initialize=all_sets)` and `model.E = pyo.Set(initialize=all_elements)`.

### Step 2 - Declare Parameters
- Define cost parameter: `model.cost = pyo.Param(model.S, initialize=cost_dict)`.
- Define coverage requirement parameter: `model.req = pyo.Param(model.E, initialize=required_coverage_dict)`.
- Define coverage matrix parameter using a rule: `def cover_rule(m, s, e): return 1 if s in cover_sets_dict[e] else 0`, then `model.cover = pyo.Param(model.S, model.E, initialize=cover_rule)`.

### Step 3 - Define Decision Variables and Constraints
- Create binary variables: `model.x = pyo.Var(model.S, domain=pyo.Binary)`.
- For each element, add a coverage constraint: `def coverage_rule(m, e): return sum(m.cover[s, e] * m.x[s] for s in m.S) >= m.req[e]`, then `model.coverage_con = pyo.Constraint(model.E, rule=coverage_rule)`.

### Step 4 - Formulate the Objective
- Set the objective: `model.obj = pyo.Objective(expr=sum(m.cost[s] * m.x[s] for s in m.S), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["S", "E"],
  "parameters": [
    {"name": "cost_s", "domain": "S", "description": "Cost of selecting set s"},
    {"name": "req_e", "domain": "E", "description": "Required coverage count for element e"},
    {"name": "cover_s_e", "domain": ["S", "E"], "description": "1 if set s covers element e"}
  ],
  "decision_variables": [
    {"name": "x_s", "domain": "S", "type": "binary", "description": "Selection variable for set s"}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost_s * x_s for s in S)"
  },
  "constraints": [
    {"expression": "sum(cover_s_e * x_s for s in S) >= req_e", "for_each": "e in E"}
  ]
}
```

### Common Pitfalls
- Defining the coverage matrix parameter inefficiently for large, sparse problems; use a rule with dictionary lookups.
- Incorrectly specifying set or parameter domains, leading to model construction errors.
- Using `pyo.Param` without a default value for missing indices in sparse data.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS MILP solver via the `appsi_highs` interface or `solverfactory('highs')`. Configure for performance and rigorously check the solution status before extracting results.

### Step 1 - Configure and Execute the Solver
- Instantiate the solver: `solver = pyo.SolverFactory('highs')`.
- Set solver options: `solver.options['time_limit'] = 30`, `solver.options['mip_rel_gap'] = 0.0` for optimality, and `solver.options['threads'] = 4`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=True)`.

### Step 2 - Check Solver Status and Load Solution
- Check termination condition: `if results.solver.termination_condition == pyo.TerminationCondition.optimal:`.
- If optimal or feasible, load the solution: `model.solutions.load_from(results)`.
- If not optimal, inspect `results.solver.status` and `results.solver.termination_condition` for diagnostics.

### Step 3 - Extract and Verify Solution
- Extract selected sets: `selected_sets = [s for s in model.S if pyo.value(model.x[s]) > 0.5]`.
- Verify coverage: for each element `e`, compute `sum(pyo.value(model.cover[s, e]) * pyo.value(model.x[s]) for s in model.S)` and confirm it meets `pyo.value(model.req[e])`.
- Report the objective value: `pyo.value(model.obj)`.

### Step 4 - Confirm Optimality via Bound Analysis
- Solve the LP relaxation (e.g., by temporarily changing variable domains to `pyo.Reals`). Compare its objective value to the MILP solution. If they match, the MILP solution is optimal.
- Alternatively, add an objective cut `sum(model.cost[s] * model.x[s] for s in model.S) <= current_obj - epsilon` and attempt to solve. Infeasibility confirms optimality.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=all_sets)
model.E = pyo.Set(initialize=all_elements)
model.cost = pyo.Param(model.S, initialize=cost_dict)
model.req = pyo.Param(model.E, initialize=required_coverage_dict)
def cover_init(m, s, e):
    return 1 if s in cover_sets_dict.get(e, []) else 0
model.cover = pyo.Param(model.S, model.E, initialize=cover_init)
model.x = pyo.Var(model.S, domain=pyo.Binary)
def coverage_rule(m, e):
    return sum(m.cover[s, e] * m.x[s] for s in m.S) >= m.req[e]
model.coverage_con = pyo.Constraint(model.E, rule=coverage_rule)
model.obj = pyo.Objective(expr=sum(m.cost[s] * m.x[s] for s in m.S), sense=pyo.minimize)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, load_solutions=False)
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    model.solutions.load_from(results)
    selected = [s for s in model.S if pyo.value(model.x[s]) > 0.5]
    # verification
    for e in model.E:
        coverage = sum(pyo.value(model.cover[s, e]) * pyo.value(model.x[s]) for s in model.S)
        assert coverage >= pyo.value(model.req[e])
    print(f"RESULT:{pyo.value(model.obj)}")
else:
    print(f"RESULT_JSON:{'status': 'solver_failed', 'termination_condition': str(results.solver.termination_condition)}")
```

### Common Pitfalls
- Forgetting to set `load_solutions=False` and then trying to access variable values before loading the results.
- Not checking both `solver.status` and `termination_condition`; a status of `ok` does not guarantee optimality.
- Using `pyo.value()` on variables or parameters before a solution has been loaded, resulting in `None` or default values.
