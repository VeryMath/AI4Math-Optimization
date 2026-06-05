---
name: TSP-MTZ-MIP
description: |
  Model and solve the Traveling Salesperson Problem (TSP) as a Mixed-Integer Program (MIP) using binary arc selection and Miller-Tucker-Zemlin (MTZ) subtour elimination constraints, with workflows for both commercial and open-source solver backends.

---
# Workflow 1 (Commercial Solver via Pyomo)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a MIP using the MTZ formulation and solves it using a high-performance commercial solver (e.g., Gurobi, CPLEX) via the Pyomo modeling language, prioritizing solution speed and advanced MIP features.

### Step 1 - Define Sets and Parameters
- Define the set of nodes (e.g., cities, locations) as `NODES`.
- Define a cost parameter `cost[i, j]` for the travel distance or expense from node `i` to node `j`. Ensure the cost matrix is complete for all ordered pairs `(i, j)` where `i != j`.

### Step 2 - Create Decision Variables
- Create binary decision variables `x[i, j]` for each ordered pair `(i, j)` where `i != j`. `x[i, j] = 1` indicates the arc from `i` to `j` is included in the tour.
- Create continuous (or integer) position variables `u[i]` for each node `i`. `u[i]` represents the visit order (position) of node `i` in the tour.

### Step 3 - Formulate Degree Constraints
- For each node `j`, enforce exactly one incoming arc: `sum(x[i, j] for i in NODES if i != j) == 1`.
- For each node `i`, enforce exactly one outgoing arc: `sum(x[i, j] for j in NODES if j != i) == 1`.

### Step 4 - Apply MTZ Subtour Elimination
- Fix the position of the starting node (e.g., node 0): `u[0] == 0`.
- For all other nodes `i != 0`, set bounds: `1 <= u[i] <= len(NODES) - 1`.
- For all pairs `i, j` where `i != j` and both are not the starting node, add the MTZ constraint: `u[i] - u[j] + n * x[i, j] <= n - 1`, where `n = len(NODES)`.

### Step 5 - Define the Objective
- Minimize the total travel cost: `sum(cost[i, j] * x[i, j] for all i, j where i != j)`.

### Formulation Template
```json
{
  "sets": [
    "NODES"
  ],
  "parameters": [
    "cost[i, j] for i, j in NODES, i != j"
  ],
  "decision_variables": [
    "x[i, j] ∈ {0, 1} for i, j in NODES, i != j",
    "u[i] ∈ ℝ (or ℤ) for i in NODES"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i, j] * x[i, j])"
  },
  "constraints": [
    "in_degree: sum(x[i, j] for i in NODES if i != j) == 1, for each j in NODES",
    "out_degree: sum(x[i, j] for j in NODES if j != i) == 1, for each i in NODES",
    "mtz: u[i] - u[j] + n * x[i, j] <= n - 1, for i, j in NODES \\ {0}, i != j",
    "u_start: u[0] == 0",
    "u_bounds: 1 <= u[i] <= n - 1, for i in NODES \\ {0}"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude the starting node (`i=0` or `j=0`) in the MTZ constraints, which makes them redundant or incorrect.
- Defining the cost matrix only for `i < j` in an asymmetric TSP, missing the cost for the reverse direction.
- Not fixing `u[0]` or setting its bounds incorrectly, which can lead to symmetric, equivalent solutions and slower solving.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a commercial solver interface, configure it for reproducibility and performance, and rigorously validate the solution by reconstructing and checking the Hamiltonian tour.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object using `SolverFactory('gurobi')` or similar.
- Configure key parameters: set a time limit (`TimeLimit`), optimality gap tolerance (`MIPGap`), number of threads (`Threads`), and a random seed (`Seed`) for deterministic results.

### Step 2 - Solve and Check Status
- Execute the solve command on the model instance.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `TerminationCondition.feasible`) before proceeding to extract the solution.

### Step 3 - Extract and Reconstruct the Tour
- Collect all arcs where the solution value of `x[i, j]` is greater than a tolerance (e.g., 0.5).
- Starting from the designated start node, follow the selected arcs to construct an ordered list of visited nodes, verifying that a single cycle is formed.

### Step 4 - Validate Solution Integrity
- Verify that the reconstructed tour visits each node exactly once.
- Recalculate the total cost by summing `cost[i, j]` for consecutive nodes in the tour (including the return to start). Compare this with the solver's reported objective value to catch discrepancies.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build model (model) from the formulation template above.
# ... (Pyomo model creation code)

# 2. Solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0001
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)  # tee=True for solver log

# Check status
from pyomo.opt import SolverStatus, TerminationCondition
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Proceed to extract solution
    tour = reconstruct_tour(model.x)
    calculated_cost = sum(cost[i, j] for (i, j) in zip(tour, tour[1:] + [tour[0]]))
    # Validate
    if abs(pyo.value(model.obj) - calculated_cost) > 1e-6:
        raise ValueError("Cost mismatch between solver and reconstructed tour.")
else:
    # Handle suboptimal or failed solve
    print(f"Solver did not find a feasible solution. Status: {results.solver.termination_condition}")
```

### Common Pitfalls
- Extracting variable values without checking if the solver found a feasible solution, leading to `None` values or errors.
- Using a loose optimality gap (`MIPGap`) for a problem where the true optimum is required, potentially accepting suboptimal tours.
- Not setting a random seed, causing non-reproducible results across runs due to the solver's internal heuristics.

# Workflow 2 (Open-Source Solver via OR-Tools)

## Modeling stage

### Strategy Overview
This workflow models the TSP as a MIP using the MTZ formulation and solves it using the open-source SCIP solver via Google's OR-Tools `pywraplp` interface, providing a free, capable alternative without commercial licenses.

### Step 1 - Define Problem Data
- Define the number of nodes `n` and a list or range of node indices.
- Define the cost matrix as a 2D list or dictionary `cost[i][j]` accessible by node indices.

### Step 2 - Create Solver and Variables
- Instantiate a MIP solver object: `solver = pywraplp.Solver.CreateSolver('SCIP')`.
- Create binary variables `x[i][j]` for all `i != j` using `solver.IntVar(0, 1, '')`.
- Create integer position variables `u[i]` with bounds `0` to `n-1` using `solver.IntVar(0, n-1, '')`.

### Step 3 - Add Degree Constraints
- For each node `j`, create a constraint: `sum(x[i][j] for i in range(n) if i != j) == 1`.
- For each node `i`, create a constraint: `sum(x[i][j] for j in range(n) if j != i) == 1`.

### Step 4 - Add MTZ Subtour Elimination Constraints
- Set the position of the start node: `solver.Add(u[0] == 0)`.
- For all `i` in `1..n-1` and `j` in `1..n-1` where `i != j`, add constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`.

### Step 5 - Set the Objective
- Create the objective expression: `sum(cost[i][j] * x[i][j] for i in range(n) for j in range(n) if i != j)`.
- Set the solver to minimize this expression.

### Formulation Template
```json
{
  "sets": [
    "n (number of nodes)",
    "N = {0, 1, ..., n-1}"
  ],
  "parameters": [
    "cost[i][j] for i, j in N, i != j"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0, 1} for i, j in N, i != j",
    "u[i] ∈ {0, ..., n-1} for i in N"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i][j] * x[i][j])"
  },
  "constraints": [
    "in_degree: sum(x[i][j] for i in N if i != j) == 1, for each j in N",
    "out_degree: sum(x[i][j] for j in N if j != i) == 1, for each i in N",
    "mtz: u[i] - u[j] + n * x[i][j] <= n - 1, for i, j in {1,...,n-1}, i != j",
    "u_start: u[0] == 0"
  ]
}
```

### Common Pitfalls
- Creating variables `x[i][i]` (self-loops), which waste memory and must be excluded from sums.
- Using `solver.NumVar` for binary `x[i][j]` instead of `solver.IntVar(0, 1)`, which is less efficient.
- Adding MTZ constraints for pairs where `i` or `j` is 0, which are unnecessary and increase problem size.

## Solving stage

### Strategy Overview
Solve the model using the OR-Tools wrapper, configure basic solver settings, extract the solution, and implement a robust tour reconstruction algorithm that handles potential numerical tolerances.

### Step 1 - Configure and Execute Solve
- Set solver parameters like time limit (`solver.SetTimeLimit`) and relative gap (`solver.SetRelativeGapTolerance` if supported).
- Call `solver.Solve()` to initiate the optimization.

### Step 2 - Verify Solution Status
- Check the solver result status: `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE`. Handle `pywraplp.Solver.NOT_SOLVED` or other statuses appropriately.

### Step 3 - Extract Arc Selections and Reconstruct Tour
- Build a successor dictionary mapping each node `i` to its unique successor `j` where `x[i][j].solution_value() > 0.5`.
- Starting from node 0, follow the successor chain to build the tour sequence. Use a visited set to detect completion.

### Step 4 - Validate and Output Results
- Verify the tour length equals `n`.
- Recompute the objective from the extracted tour and compare with `solver.Objective().Value()`.
- Package results (status, objective value, tour list) in a structured format (e.g., dictionary, JSON).

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Build model
solver = pywraplp.Solver.CreateSolver('SCIP')
n = len(NODES)
# ... Create variables x, u and add constraints as per modeling stage

# 2. Solve with status / termination checks
solver.SetTimeLimit(60000)  # milliseconds
status = solver.Solve()

# Check status
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    # Build successor dictionary for efficient tour reconstruction
    successor = {}
    for i in range(n):
        for j in range(n):
            if i != j and x[i][j].solution_value() > 0.5:
                successor[i] = j
    # Reconstruct tour
    tour = [0]
    current = 0
    visited = {0}
    while len(tour) < n:
        next_node = successor[current]
        if next_node in visited:
            raise ValueError("Cycle detected before visiting all nodes.")
        tour.append(next_node)
        visited.add(next_node)
        current = next_node
    # Validate
    calculated_obj = sum(cost[tour[i]][tour[i+1]] for i in range(n-1)) + cost[tour[-1]][tour[0]]
    if abs(solver.Objective().Value() - calculated_obj) > 1e-6:
        raise ValueError("Objective value mismatch.")
    result = {
        'status': 'OPTIMAL' if status == pywraplp.Solver.OPTIMAL else 'FEASIBLE',
        'objective': solver.Objective().Value(),
        'tour': tour
    }
else:
    result = {'status': 'NOT_SOLVED', 'objective': None, 'tour': None}
```

### Common Pitfalls
- Using a strict equality (`== 0.5`) to check binary variable values, failing due to floating-point precision. Use a tolerance (e.g., `> 0.5`).
- An inefficient O(n²) tour reconstruction that searches all arcs at each step. A successor dictionary mapping `i` to its unique `j` built once is more efficient.
- Not handling the case where the solver finds a feasible but not optimal solution, potentially leading to incorrect assumptions about solution quality.
