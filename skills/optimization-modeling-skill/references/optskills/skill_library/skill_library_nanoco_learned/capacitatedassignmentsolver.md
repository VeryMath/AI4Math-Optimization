---
name: CapacitatedAssignmentSolver
description: |
  Solves binary assignment problems with exactly-one assignment and knapsack-style capacity constraints by formulating a Mixed-Integer Linear Program (MILP) and solving it with a configured MILP solver.

---
# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
Model the problem directly using a solver's native Python API (e.g., OR-Tools, PuLP). This approach is procedural, keeps the model close to the solver, and is efficient for straightforward implementations.

### Step 1 - Define Data Structures
- Organize problem data into clear dictionaries or lists for costs, capacities, and requirements. Use descriptive keys like `cost[(i, j)]`, `capacity[j]`, `requirement[(i, j)]`.
- Define sets for assignable items `I` and resources `J` as iterable lists.

### Step 2 - Create Solver and Variables
- Instantiate a MILP solver (e.g., `pywraplp.Solver.CreateSolver('SCIP')`). Check for solver availability.
- Create binary decision variables `x[(i, j)]` for all `i` in `I`, `j` in `J`. Name them clearly, like `assign`.

### Step 3 - Formulate Exactly-One Constraints
- For each item `i`, add a constraint: `sum(x[(i, j)] for j in J) == 1`. This ensures each item is assigned to exactly one resource.

### Step 4 - Formulate Knapsack Capacity Constraints
- For each resource `j`, add a constraint: `sum(requirement[(i, j)] * x[(i, j)] for i in I) <= capacity[j]`. This enforces resource limits.

### Step 5 - Define Linear Objective
- Set the objective to minimize total cost: `solver.Minimize(sum(cost[(i, j)] * x[(i, j)] for i in I for j in J))`.

### Formulation Template
```json
{
  "sets": ["I (items)", "J (resources)"],
  "parameters": ["cost[i][j]", "capacity[j]", "requirement[i][j]"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) == 1, for all i in I",
    "sum(requirement[i][j] * x[i][j] for i in I) <= capacity[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Forgetting to check if the solver instance was created successfully (`if solver is None:`).
- Using incorrect indices when populating parameters, leading to `KeyError`.
- Not setting a time limit for large instances, causing long, unbound runs.

## Solving stage

### Strategy Overview
Solve the model using the configured solver, extract the solution, and verify its correctness and optimality. Handle solver statuses and produce parseable output.

### Step 1 - Configure Solver Parameters
- Set practical solver parameters: `solver.SetTimeLimit(30000)` for a time limit and `solver.SetNumThreads(4)` to utilize multiple cores.

### Step 2 - Invoke Solver and Check Status
- Call `solver.Solve()`.
- Check the result status: `status in (solver.OPTIMAL, solver.FEASIBLE)`. Handle `solver.INFEASIBLE` or `solver.UNBOUNDED` appropriately.

### Step 3 - Extract and Verify Solution
- If optimal or feasible, iterate over variables `x[(i, j)]` and collect assignments where `x[(i, j)].solution_value() > 0.5`.
- Calculate derived metrics like actual resource usage per `j` to verify capacity constraints are satisfied.

### Step 4 - Output Structured Results
- Print the objective value in a consistent, parseable format (e.g., `print(f"RESULT:{solver.Objective().Value()}")`).
- Optionally, output a detailed JSON with assignments and resource usage for debugging.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
if solver is None:
    raise Exception('Solver not available.')
x = {}
for i in I:
    for j in J:
        x[(i, j)] = solver.BoolVar(f'x_{i}_{j}')

# Add constraints
for i in I:
    solver.Add(sum(x[(i, j)] for j in J) == 1)
for j in J:
    solver.Add(sum(requirement[(i, j)] * x[(i, j)] for i in I) <= capacity[j])

# Set objective
objective_terms = []
for i in I:
    for j in J:
        objective_terms.append(cost[(i, j)] * x[(i, j)])
solver.Minimize(sum(objective_terms))

# solve with status / termination checks
solver.SetTimeLimit(30000)
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'RESULT:{solver.Objective().Value()}')
    # Extract assignments...
else:
    print('No feasible solution found.')
```

### Common Pitfalls
- Assuming the solver always returns an optimal solution without checking the status.
- Extracting variable values without a tolerance check (use `> 0.5` for binary variables).
- Not verifying calculated resource usage against the original capacity constraints.

# Workflow 2 (Pyomo Modeling Framework)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo, an algebraic modeling language in Python. This approach is declarative, separates model from data, and facilitates integration with various solvers.

### Step 1 - Define Abstract Sets and Parameters
- Define Pyomo `Set` objects for items `model.I` and resources `model.J`.
- Define `Param` objects for `model.cost`, `model.capacity`, and `model.requirement`, initialized from dictionaries.

### Step 2 - Declare Decision Variables
- Declare binary variables `model.x` indexed over `model.I` and `model.J` using `pyo.Var(domain=pyo.Binary)`.

### Step 3 - Formulate Exactly-One Constraints
- Add a constraint for each item `i`: `sum(model.x[i, j] for j in model.J) == 1`. Use a Pyomo `Constraint` rule.

### Step 4 - Formulate Knapsack Capacity Constraints
- Add a constraint for each resource `j`: `sum(model.requirement[i, j] * model.x[i, j] for i in model.I) <= model.capacity[j]`.

### Step 5 - Define the Objective
- Set the objective to minimize total cost using `pyo.Objective(expr=sum(model.cost[i, j] * model.x[i, j] for i in model.I for j in model.J), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I (items)", "J (resources)"],
  "parameters": ["cost[i][j]", "capacity[j]", "requirement[i][j]"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j] for i in I for j in J)"
  },
  "constraints": [
    "sum(x[i][j] for j in J) == 1, for all i in I",
    "sum(requirement[i][j] * x[i][j] for i in I) <= capacity[j], for all j in J"
  ]
}
```

### Common Pitfalls
- Incorrectly initializing `Param` objects with missing indices, causing runtime errors.
- Using Python's `sum` inside a Pyomo expression rule instead of the built-in `pyo.summation`.
- Forgetting to deactivate the dual updates if using `solver.options['threads']` with certain solvers.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver like CBC or HiGHS, configured via `SolverFactory`. Robustly handle solver results and extract the solution.

### Step 1 - Configure and Invoke Solver
- Create a solver object: `solver = pyo.SolverFactory('cbc')`.
- Set solver options: `solver.options['seconds'] = 30`, `solver.options['ratio'] = 0.0` (for optimality gap), `solver.options['threads'] = 4`.

### Step 2 - Solve and Check Termination
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` is `SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `...feasible`.

### Step 3 - Extract Solution and Verify
- Use `pyo.value(model.x[i, j])` to get variable values. Collect assignments where the value is `> 0.5`.
- Recalculate resource usage and total cost to verify against the model's constraints and objective.

### Step 4 - Output Results
- Print the objective value from `pyo.value(model.obj)` in a parseable format (e.g., `RESULT:<value>`).
- Optionally, output assignments and verification metrics as structured JSON.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=items)
model.J = pyo.Set(initialize=resources)
model.cost = pyo.Param(model.I, model.J, initialize=cost_dict)
model.capacity = pyo.Param(model.J, initialize=capacity_dict)
model.requirement = pyo.Param(model.I, model.J, initialize=requirement_dict)
model.x = pyo.Var(model.I, model.J, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.cost[i, j] * m.x[i, j] for i in m.I for j in m.J)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def assign_rule(m, i):
    return sum(m.x[i, j] for j in m.J) == 1
model.assign_constr = pyo.Constraint(model.I, rule=assign_rule)

def capacity_rule(m, j):
    return sum(m.requirement[i, j] * m.x[i, j] for i in m.I) <= m.capacity[j]
model.capacity_constr = pyo.Constraint(model.J, rule=capacity_rule)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    print(f'RESULT:{pyo.value(model.obj)}')
    # Extract assignments...
else:
    print('Solver did not find a feasible solution.')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition` after solving.
- Attempting to access `pyo.value` on an undefined variable if the solver failed.
- Misconfiguring solver options for the specific solver backend (e.g., `'ratio'` vs. `'mipgap'`).
