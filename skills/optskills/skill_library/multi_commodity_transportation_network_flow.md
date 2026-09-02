---
name: Multi-Commodity Transportation Network Flow
description: |
  Model and solve multi-product flow problems on capacitated networks, minimizing total transportation cost while respecting supply limits, demand requirements, and shared arc capacities.
---

# Workflow 1 (LP Solver with pywraplp)

## Modeling stage

### Strategy Overview
Model the problem as a pure Linear Program (LP) using a direct solver API (e.g., OR-Tools' `pywraplp`). This approach is procedural, builds the model coefficient-by-coefficient, and is well-suited for integration into scripts or applications requiring fine-grained control.

### Step 1 - Define Data Structures
- Organize all input data as nested dictionaries or 2D/3D lists for consistent indexing. Use `supply[i][p]`, `demand[j][p]`, `cost[i][j][p]`, and `arc_capacity[i][j]`.
- Pre-validate data by checking total system balance: `sum(supply[i][p]) >= sum(demand[j][p])` for feasibility.

### Step 2 - Create Decision Variables
- Instantiate a three-dimensional array of non-negative continuous variables `x[i][j][p]`. Use `solver.NumVar(0, solver.infinity(), f'x_{i}_{j}_{p}')` to create variables with descriptive names.

### Step 3 - Build Supply and Demand Constraints
- For each origin `i` and product `p`, create a supply constraint: `sum_{j} x[i][j][p] <= supply[i][p]`.
- For each destination `j` and product `p`, create a demand constraint: `sum_{i} x[i][j][p] >= demand[j][p]`.

### Step 4 - Build Arc Capacity Constraints
- For each origin-destination pair `(i, j)`, create a capacity constraint: `sum_{p} x[i][j][p] <= arc_capacity[i][j]`.

### Step 5 - Set Objective Function
- Define the objective to minimize total cost: `sum_{i,j,p} cost[i][j][p] * x[i][j][p]`. Use `solver.Minimize()`.

### Formulation Template
```json
{
  "sets": ["origins", "destinations", "products"],
  "parameters": [
    "supply[origin][product]",
    "demand[destination][product]",
    "cost[origin][destination][product]",
    "arc_capacity[origin][destination]"
  ],
  "decision_variables": ["flow[origin][destination][product] >= 0"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j][p] * flow[i][j][p])"
  },
  "constraints": [
    "sum_j flow[i][j][p] <= supply[i][p] for all i, p",
    "sum_i flow[i][j][p] >= demand[j][p] for all j, p",
    "sum_p flow[i][j][p] <= arc_capacity[i][j] for all i, j"
  ]
}
```

### Common Pitfalls
- Using inconsistent data structures (e.g., lists for supply but dicts for cost) leading to indexing errors.
- Forgetting to aggregate across the correct index in capacity constraints (should sum over products `p`).
- Not including origins with zero supply in the model structure, which can simplify data handling.

## Solving stage

### Strategy Overview
Solve the LP using a high-performance solver like GLOP. Implement robust status checking and post-solution verification to ensure the solution is both optimal and feasible within numerical tolerances.

### Step 1 - Configure Solver
- Instantiate the solver: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Set practical limits: `solver.SetTimeLimit(30000)` for a 30-second timeout.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check for acceptable statuses: `status in (solver.OPTIMAL, solver.FEASIBLE)`. Handle other statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.

### Step 3 - Extract and Validate Solution
- If the status is acceptable, extract variable values: `flow_val = x[i][j][p].solution_value()`.
- Programmatically verify all constraints with a tolerance (e.g., `1e-6`). Calculate total supply used, demand met, and arc flows, comparing against limits.
- Compute and report aggregate statistics (e.g., total cost, supply utilization per product).

### Step 4 - Output Results
- Print the objective value in a parseable format (e.g., `RESULT:{objective_value}`).
- Optionally, output detailed flow values or constraint violation reports for debugging.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (build variables, constraints, objective as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    # Validate solution
    for i in origins:
        for p in products:
            total_shipped = sum(x[i][j][p].solution_value() for j in destinations)
            if total_shipped > supply[i][p] + 1e-6:
                print(f"Supply violation at ({i},{p})")
    print(f'RESULT:{objective_value}')
else:
    print('Solver failed with status:', status)
```

### Common Pitfalls
- Accepting a solution without numerical verification, potentially missing small constraint violations.
- Misinterpreting solver status codes (e.g., treating `FEASIBLE` as an error).
- Not setting a time limit, risking the solver hanging on large or pathological instances.

# Workflow 2 (Modeling Language with Pyomo and HiGHS)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo, separating model definition from solver invocation. This approach enhances readability, maintainability, and leverages automatic presolve reductions from solvers like HiGHS.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo Sets for `origins`, `destinations`, and `products`.
- Define Pyomo Parameters for `supply`, `demand`, `cost`, and `arc_capacity` using nested dictionaries or rule-based initialization.

### Step 2 - Define Decision Variables
- Declare a Pyomo `Var` indexed over the three sets: `model.x = pyo.Var(model.origins, model.destinations, model.products, domain=pyo.NonNegativeReals)`.

### Step 3 - Construct Constraints via Rules
- Create a `ConstraintList` or use `pyo.Constraint` with rule functions for each constraint family.
- Supply rule: `def supply_rule(model, i, p): return sum(model.x[i, j, p] for j in model.destinations) <= model.supply[i, p]`.
- Demand rule: Use `>=` for demand satisfaction.
- Capacity rule: Sum over products `p` for each arc `(i, j)`.

### Step 4 - Define the Objective
- Use `pyo.Objective(expr=sum(model.cost[i,j,p] * model.x[i,j,p] for i,j,p), sense=pyo.minimize)`.

### Formulation Template
```json
{
  "sets": ["I (origins)", "J (destinations)", "P (products)"],
  "parameters": [
    "supply[i,p] for i in I, p in P",
    "demand[j,p] for j in J, p in P",
    "cost[i,j,p] for i in I, j in J, p in P",
    "capacity[i,j] for i in I, j in J"
  ],
  "decision_variables": ["x[i,j,p] >= 0 for i in I, j in J, p in P"],
  "objective": {
    "sense": "min",
    "expression": "sum( cost[i,j,p] * x[i,j,p] )"
  },
  "constraints": [
    "supply_con[i,p]: sum_j x[i,j,p] <= supply[i,p]",
    "demand_con[j,p]: sum_i x[i,j,p] >= demand[j,p]",
    "capacity_con[i,j]: sum_p x[i,j,p] <= capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Defining parameter rules that are overly complex or slow for large datasets; prefer dictionary initialization.
- Mixing up index order in constraint rules (e.g., summing over origins when destinations are required).
- Using equality (`=`) for demand constraints when the problem allows over-satisfaction; `>=` is more flexible.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS LP solver via the `pyo.SolverFactory` interface. Configure solver options for performance and reliability, and implement a structured post-solution analysis.

### Step 1 - Instantiate and Configure Solver
- Create solver object: `solver = pyo.SolverFactory('highs')`.
- Set options: `solver.options['time_limit'] = 30`, `solver.options['threads'] = 4`. For exact solutions, set `'mip_rel_gap' = 0.0` (relevant if extensions introduce integer variables).

### Step 2 - Solve and Inspect Termination
- Execute `results = solver.solve(model, tee=False)`.
- Check termination condition: `results.solver.termination_condition` should be `optimal` or `feasible`. Also verify `results.solver.status` is `ok`.

### Step 3 - Extract and Verify Solution
- Access the objective value: `obj_val = pyo.value(model.obj)`.
- Implement a verification function that iterates over all constraints, computing left-hand side values using `pyo.value(model.x[i,j,p])` and comparing to right-hand side limits with a tolerance.
- Report any violations and compute operational metrics (e.g., capacity utilization rates).

### Step 4 - Output Structured Results
- Print the objective value in a consistent format (e.g., `RESULT:{obj_val}`).
- For non-optimal terminations, log the solver status and termination condition for debugging.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.I = pyo.Set(initialize=origins)
model.J = pyo.Set(initialize=destinations)
model.P = pyo.Set(initialize=products)
# ... (define parameters, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = 30
results = solver.solve(model)

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.obj)
    # Perform verification
    tolerance = 1e-6
    for i in model.I:
        for p in model.P:
            lhs = sum(pyo.value(model.x[i, j, p]) for j in model.J)
            if lhs > model.supply[i, p] + tolerance:
                print(f"Supply violation at ({i},{p})")
    print(f'RESULT:{objective_value}')
else:
    print('Solver failed:', results.solver.termination_condition)
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to acceptance of failed solves.
- Using placeholder or incorrect data during verification (e.g., a different `cost` dictionary); always use the model's own parameters.
- Ignoring the benefits of solver presolve; trust the reduced problem statistics reported by HiGHS.
