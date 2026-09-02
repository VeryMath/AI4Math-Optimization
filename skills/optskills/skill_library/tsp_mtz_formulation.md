---
name: TSP_MTZ_Formulation
description: |
  Model and solve the Traveling Salesperson Problem using the Miller-Tucker-Zemlin (MTZ) formulation with binary arc and integer position variables, producing exact or feasible tours via MIP/CP-SAT solvers.
---

# Workflow 1 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the TSP as a Mixed-Integer Program (MIP) using the OR-Tools CP-SAT solver interface. This workflow leverages the solver's native constraint programming strengths for combinatorial problems, using a linearized MTZ formulation suitable for exact solving with parallel search.

### Step 1 - Define Problem Data
- Define the set of nodes `N = {0, 1, ..., n-1}` where `0` is the depot.
- Define a distance matrix `dist[i][j]` for all ordered pairs `(i, j)` where `i != j`.
- Calculate the Big-M parameter as `M = len(N)` (number of nodes).

### Step 2 - Create Decision Variables
- Create binary arc variables `x[i][j]` for all `i, j in N, i != j`. Each variable equals 1 if arc `(i, j)` is in the tour.
- Create integer position variables `u[i]` for all `i in N`, with domain `[0, n-1]`. These represent the visit order.

### Step 3 - Formulate Degree Constraints
- For each node `j` in `N`, enforce exactly one incoming arc: `sum(x[i][j] for i in N if i != j) == 1`.
- For each node `i` in `N`, enforce exactly one outgoing arc: `sum(x[i][j] for j in N if j != i) == 1`.

### Step 4 - Apply MTZ Subtour Elimination
- For all `i, j in N` where `i != j` and `j != depot` (i.e., `j != 0`), add constraint: `u[i] - u[j] + 1 <= M * (1 - x[i][j])`.
- Fix the depot's position to break symmetry: `u[depot] == 0`.

### Step 5 - Define Objective
- Minimize total tour distance: `minimize sum(dist[i][j] * x[i][j] for i in N for j in N if i != j)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes (0 is depot)"
  ],
  "parameters": [
    "dist[i][j]: distance from node i to j, for i, j in N, i != j",
    "M: Big-M constant, M = |N|"
  ],
  "decision_variables": [
    "x[i][j]: binary, 1 if arc (i,j) is selected",
    "u[i]: integer, position of node i in tour, domain [0, |N|-1]"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} dist[i][j] * x[i][j]"
  },
  "constraints": [
    "in_degree: forall j in N: sum_{i in N, i != j} x[i][j] == 1",
    "out_degree: forall i in N: sum_{j in N, j != i} x[i][j] == 1",
    "mtz: forall i in N, j in N, i != j, j != depot: u[i] - u[j] + 1 <= M * (1 - x[i][j])",
    "fix_depot: u[depot] == 0"
  ]
}
```

### Common Pitfalls
- Using a Big-M value that is too small, which can cut off valid solutions. Use `M = n` (number of nodes).
- Forgetting to exclude the depot (`j != depot`) in the MTZ constraints, which would incorrectly prevent the return arc to the start.
- Not adding symmetry-breaking constraints (like fixing `u[depot]`), which can slow down the solver.

## Solving stage

### Strategy Overview
Solve the MIP model using OR-Tools' CP-SAT solver, configured for parallel search and a time limit. Extract and validate the tour from the binary arc variables.

### Step 1 - Configure Solver
- Instantiate the CP-SAT solver.
- Set solver parameters: `num_search_workers` for parallelism, `max_time_in_seconds` for time limit, and `random_seed` for reproducibility.
- Set `relative_gap_limit` to `0.0` to seek an optimal solution.

### Step 2 - Solve and Check Status
- Invoke the solver's `Solve` method.
- Check the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `MODEL_INVALID` with appropriate error messages.

### Step 3 - Extract Solution
- If a feasible solution exists, reconstruct the tour sequence.
- Start at the depot. Iteratively find the next node `j` where `x[current][j]` equals 1 in the solution (check `solver.Value(x[current][j]) > 0.5`).
- Append nodes to the tour until all are visited, verifying the final arc returns to the depot.

### Step 4 - Validate and Report
- Compute the total distance from the extracted tour sequence and compare it to the solver's objective value for consistency.
- Output the tour, total distance, and solver status.

### Code Usage
```python
# build model from formulation
from ortools.sat.python import cp_model

model = cp_model.CpModel()
# ... create variables, add constraints and objective as per modeling stage

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.num_search_workers = 8
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # Extract tour from solver.Value(x[i][j]) variables
    tour = [depot]
    current = depot
    while len(tour) < len(N):
        for j in N:
            if j != current and solver.Value(x[current][j]) > 0.5:
                tour.append(j)
                current = j
                break
    # Validate return to depot
    if solver.Value(x[current][depot]) > 0.5:
        tour.append(depot)
    print(f"Tour: {tour}")
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Assuming `OPTIMAL` status within a time limit; always check for `FEASIBLE` as well.
- Incorrect tour reconstruction due to not checking variable solution values against a tolerance (e.g., `> 0.5`).
- Not verifying the final arc closes the cycle, which can happen if the MTZ constraints are misapplied.

# Workflow 2 (MIP with Pyomo and External Solver)

## Modeling stage

### Strategy Overview
Formulate the TSP as a MIP using the Pyomo modeling language, which provides an abstract, solver-agnostic interface. This workflow is designed for use with high-performance external MIP solvers (e.g., Gurobi, HiGHS, CBC) and emphasizes a clean separation of model and solver.

### Step 1 - Define Abstract Sets and Parameters
- Define a Pyomo `Set` for nodes `model.N`.
- Define a Pyomo `Param` `model.dist` indexed by `(i, j)` for `i != j` to store distances.
- Define parameter `model.M` (Big-M) as the number of nodes.

### Step 2 - Create Decision Variables
- Create binary variables `model.x[i, j]` for all `i, j in model.N, i != j`.
- Create integer variables `model.u[i]` for all `i in model.N` with bounds `(0, len(model.N)-1)`.

### Step 3 - Formulate Degree Constraints
- Add constraints for each node `j`: `sum(model.x[i, j] for i in model.N if i != j) == 1`.
- Add constraints for each node `i`: `sum(model.x[i, j] for j in model.N if j != i) == 1`.

### Step 4 - Apply MTZ Subtour Elimination
- For all `i, j in model.N` where `i != j` and `j != model.depot`, add constraint: `model.u[i] - model.u[j] + 1 <= model.M * (1 - model.x[i, j])`.
- Fix the depot's position: `model.u[model.depot] == 0`.

### Step 5 - Define Objective
- Minimize total distance: `model.obj = Objective(expr=sum(model.dist[i, j] * model.x[i, j] for i in model.N for j in model.N if i != j), sense=minimize)`.

### Formulation Template
```json
{
  "sets": [
    "N: Pyomo Set of nodes"
  ],
  "parameters": [
    "dist[i,j]: Pyomo Param, distance matrix",
    "M: Pyomo Param, Big-M constant, M = |N|"
  ],
  "decision_variables": [
    "x[i,j]: Pyomo Var, domain=Binary",
    "u[i]: Pyomo Var, domain=NonNegativeIntegers, bounds=(0, |N|-1)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in N} sum_{j in N, j != i} dist[i,j] * x[i,j]"
  },
  "constraints": [
    "in_degree: forall j in N: sum_{i in N, i != j} x[i,j] == 1",
    "out_degree: forall i in N: sum_{j in N, j != i} x[i,j] == 1",
    "mtz: forall i in N, j in N, i != j, j != depot: u[i] - u[j] + 1 <= M * (1 - x[i,j])",
    "fix_depot: u[depot] == 0"
  ]
}
```

### Common Pitfalls
- Using `model.N` in list comprehensions inside Pyomo expressions, which can cause errors. Use Pyomo's `model.N` component directly in summations.
- Not setting proper bounds on integer variables `u[i]`, which can lead to unbounded problems.
- Defining the distance parameter for `i == j`, which should be excluded to avoid self-loops.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an external MIP solver via a solver manager (e.g., `SolverFactory`). Configure solver-specific options for time limit and optimality gap, then extract and validate the solution.

### Step 1 - Select and Configure Solver
- Use `SolverFactory('solver_name')` (e.g., `'gurobi'`, `'highs'`, `'cbc'`).
- Pass solver options: `timelimit`, `mipgap` (or `relgap`), `threads`, and `seed` for reproducibility.

### Step 2 - Solve and Check Termination
- Invoke `solver.solve(model, options=...)`.
- Check both the solver status (`solver.status`) and model termination condition (`model.termination_condition`). Accept `optimal` or `feasible` results.

### Step 3 - Extract Solution
- Access variable values using `value(model.x[i, j])` or `model.x[i, j].value`.
- Reconstruct the tour by starting at the depot and following arcs where the variable value is approximately 1 (check `> 0.5`).

### Step 4 - Validate and Report
- Compute the tour's total distance from the sequence and compare to `value(model.obj)`.
- Output the tour, objective value, and solver statistics.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=node_list)
model.depot = node_list[0]
model.dist = pyo.Param(model.N, model.N, initialize=dist_dict, default=0)
model.M = pyo.Param(initialize=len(model.N))
# ... create variables, constraints, and objective as per modeling stage

# solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'gurobi', 'cbc'
results = solver.solve(model, options={'time_limit': 30, 'threads': 4})

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal,
                                             pyo.TerminationCondition.feasible)):
    # Extract tour
    tour = [model.depot]
    current = model.depot
    visited = set(tour)
    while len(visited) < len(model.N):
        for j in model.N:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                visited.add(j)
                break
    # Check return arc
    if pyo.value(model.x[current, model.depot]) > 0.5:
        tour.append(model.depot)
    print(f"Tour: {tour}")
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Confusing Pyomo's `solver.status` (solver process) with `termination_condition` (solution quality). Both must be checked.
- Not using `pyo.value()` to access variable values in the solution object.
- Assuming the solver returns an optimal solution within the time limit; always handle feasible solutions gracefully.
