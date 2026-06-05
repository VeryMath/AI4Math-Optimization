---
name: MaximalCoveringLocationProblem
description: |
  A skill for solving maximal covering location problems by selecting a limited number of facilities to maximize weighted coverage of demand points within a specified distance threshold.

---
# Workflow 1 (Explicit Coverage Sets)

## Modeling stage

### Strategy Overview
Explicitly precompute the coverage relationship between demand points and candidate facilities before model construction. This separation of data preparation and modeling leads to cleaner, more readable constraints and can improve solver performance by reducing constraint complexity.

### Step 1 - Define Sets and Parameters
- Define `I` as the set of demand points and `J` as the set of candidate facility sites.
- Define `w_i` as the weight (value) for covering demand point `i`.
- Define `d_{ij}` as the distance between demand point `i` and candidate site `j`.
- Define `R` as the coverage radius (distance threshold).
- Define `k` as the cardinality limit for the number of facilities to select.

### Step 2 - Precompute Coverage Sets
- For each demand point `i`, compute `N(i) = {j in J | d_{ij} <= R}`. This is the set of candidate sites that can cover demand point `i`.
- Identify any demand points where `N(i)` is empty. These points are uncoverable and must be handled separately to avoid infeasible constraints.

### Step 3 - Create Decision Variables
- Create binary variable `x_j` for each candidate site `j` in `J`. `x_j = 1` if site `j` is selected.
- Create binary variable `y_i` for each demand point `i` in `I`. `y_i = 1` if demand point `i` is covered.

### Step 4 - Formulate Constraints
- Add cardinality constraint: `sum_{j in J} x_j = k`.
- For each demand point `i` where `N(i)` is not empty, add coverage activation constraint: `y_i <= sum_{j in N(i)} x_j`.
- For each demand point `i` where `N(i)` is empty, fix `y_i = 0`.

### Step 5 - Define Objective
- Maximize total weighted coverage: `maximize sum_{i in I} w_i * y_i`.

### Formulation Template
```json
{
  "sets": [
    "I: demand_points",
    "J: candidate_sites"
  ],
  "parameters": [
    "w[i in I]: weight of demand point i",
    "d[i in I][j in J]: distance from i to j",
    "R: coverage radius",
    "k: number of facilities to select"
  ],
  "decision_variables": [
    "x[j in J]: binary, 1 if site j selected",
    "y[i in I]: binary, 1 if demand point i covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(i in I) w[i] * y[i]"
  },
  "constraints": [
    "cardinality: sum(j in J) x[j] == k",
    "coverage[i in I where N(i) nonempty]: y[i] <= sum(j in N(i)) x[j]",
    "uncoverable[i in I where N(i) empty]: y[i] == 0"
  ]
}
```

### Common Pitfalls
- Forgetting to handle demand points with empty coverage sets (`N(i) = {}`), which leads to infeasible constraints if `y_i` is forced to be `<= 0`.
- Incorrectly defining the coverage set `N(i)` (e.g., using strict inequality `<` instead of `<=` for the distance threshold).
- Not verifying that the precomputed coverage sets align with the distance matrix and threshold after data loading.

## Solving stage

### Strategy Overview
Use a high-performance MIP solver (e.g., Gurobi, HiGHS) via a modeling framework (e.g., Pyomo, OR-Tools). Focus on configuring the solver for optimality, implementing solution verification, and providing structured output.

### Step 1 - Solver Initialization and Configuration
- Instantiate a solver object suitable for MIP problems.
- Set a time limit (e.g., `SetTimeLimit([TIME_LIMIT])`).
- Set the number of threads for parallel solving (e.g., `SetNumThreads(4)`).
- Set optimality tolerance (e.g., `SetRelativeGapTolerance(0.0)` for an optimality certificate).

### Step 2 - Build Model from Formulation
- Translate the mathematical formulation into solver API calls.
- Add all variables, constraints, and the objective function as defined in the modeling stage.

### Step 3 - Solve and Check Status
- Execute the `Solve()` method.
- Check the solver status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.) and termination condition.
- Proceed only if a feasible or optimal solution is found.

### Step 4 - Extract and Verify Solution
- Extract the values of `x_j` and `y_i` variables. Use a tolerance (e.g., `> 0.5`) to interpret binary values.
- Verify the solution: ensure selected facilities respect the cardinality `k`, and that every demand point with `y_i = 1` is within distance `R` of at least one selected facility.
- Compute the achieved objective value from the extracted solution for cross-checking.

### Step 5 - Output Structured Results
- Output key results: selected facility indices, covered demand point indices, and total covered weight.
- Format output (e.g., JSON) for downstream processing, including solver status and verification flag.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
solver.SetTimeLimit([TIME_LIMIT])
solver.SetNumThreads(4)

# Create variables
x = [solver.IntVar(0, 1, f'x_{j}') for j in range(n_sites)]
y = [solver.IntVar(0, 1, f'y_{i}') for i in range(n_demands)]

# Add cardinality constraint
solver.Add(sum(x) == k)

# Add coverage constraints using precomputed N_i
for i in range(n_demands):
    covering_sites = [x[j] for j in N[i]]
    if covering_sites:
        solver.Add(y[i] <= sum(covering_sites))
    else:
        solver.Add(y[i] == 0)

# Set objective
objective = solver.Objective()
for i in range(n_demands):
    objective.SetCoefficient(y[i], weights[i])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract solution
    selected = [j for j in range(n_sites) if x[j].solution_value() > 0.5]
    covered = [i for i in range(n_demands) if y[i].solution_value() > 0.5]
    # ... verification and output
```

### Common Pitfalls
- Not checking solver status before extracting solution values, which can cause errors.
- Using a loose optimality gap, which may return suboptimal solutions for the weighted coverage objective.
- Failing to verify the solution logic, potentially accepting results that violate the coverage distance constraint due to solver tolerances.

# Workflow 2 (Implicit Coverage Constraints)

## Modeling stage

### Strategy Overview
Embed the coverage condition directly within the model constraints using a binary parameter, avoiding the need for explicit precomputation of sets in the modeling language. This can be more natural in some algebraic modeling systems and keeps the distance logic inside the model.

### Step 1 - Define Sets and Parameters
- Define `I` as the set of demand points and `J` as the set of candidate sites.
- Define `w_i` as the weight for covering demand point `i`.
- Define a binary parameter `a_{ij}` where `a_{ij} = 1` if distance `d_{ij} <= R`, else `0`.
- Define `k` as the cardinality limit for facility selection.

### Step 2 - Create Decision Variables
- Create binary variable `x_j` for each candidate site `j` in `J`. `x_j = 1` if site `j` is selected.
- Create binary variable `y_i` for each demand point `i` in `I`. `y_i = 1` if demand point `i` is covered.

### Step 3 - Formulate Constraints
- Add cardinality constraint: `sum_{j in J} x_j = k`.
- For each demand point `i`, add coverage activation constraint: `y_i <= sum_{j in J} a_{ij} * x_j`. This sums over all sites, but `a_{ij}` filters to only those within range.

### Step 4 - Define Objective
- Maximize total weighted coverage: `maximize sum_{i in I} w_i * y_i`.

### Formulation Template
```json
{
  "sets": [
    "I: demand_points",
    "J: candidate_sites"
  ],
  "parameters": [
    "w[i in I]: weight of demand point i",
    "a[i in I][j in J]: binary, 1 if site j covers point i",
    "k: number of facilities to select"
  ],
  "decision_variables": [
    "x[j in J]: binary, 1 if site j selected",
    "y[i in I]: binary, 1 if demand point i covered"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(i in I) w[i] * y[i]"
  },
  "constraints": [
    "cardinality: sum(j in J) x[j] == k",
    "coverage[i in I]: y[i] <= sum(j in J) a[i][j] * x[j]"
  ]
}
```

### Common Pitfalls
- Creating a dense parameter `a_{ij}` for large problems, which can consume significant memory. Consider using sparse representation if possible.
- The constraint `y_i <= sum_{j in J} a_{ij} * x_j` is correct, but mistakenly writing `y_i == ...` would be incorrect, as coverage can be *activated* by the sum but not *forced*.
- Not recognizing that the parameter `a_{ij}` must be precomputed from distances `d_{ij}` and radius `R` before model instantiation.

## Solving stage

### Strategy Overview
Use a modeling library (e.g., PuLP, OR-Tools) with a focus on clear model definition using implicit summation. Include post-solution validation through brute-force enumeration for small instances to verify optimality and model correctness.

### Step 1 - Model Construction with Implicit Constraints
- Use a modeling library to declare variables, objective, and constraints directly as per the algebraic formulation.
- The coverage constraint `y_i <= sum(a_ij * x_j)` is added in a loop over all demand points `i`.

### Step 2 - Solver Configuration for Exact Solution
- Select a MIP solver (e.g., CBC via PuLP).
- Set emphasis on optimality (e.g., `gapRel=0.0`).
- Set a reasonable time limit.

### Step 3 - Solve and Process Results
- Invoke the solver.
- Check the solution status. If optimal, extract the list of selected facilities and covered demand points.

### Step 4 - Validation and Sanity Checking
- For small-scale problems (e.g., where the number of combinations `choose(|J|, k)` is manageable, e.g., ≤ 1000), implement brute-force enumeration to verify the solver found the true optimum.
- Programmatically verify that each covered demand point has at least one selected facility `j` where `a_{ij} = 1`.
- Report any discrepancies between the solver solution and the validation checks.

### Step 5 - Generate Analysis Output
- Output the optimal facility selection and the corresponding covered demand points with their weights.
- Include validation results and, for small instances, the objective value from exhaustive search.

### Code Usage
```python
# build model from formulation
import pulp
prob = pulp.LpProblem('MCLP', pulp.LpMaximize)

# Variables
x = {j: pulp.LpVariable(f'x_{j}', cat='Binary') for j in J}
y = {i: pulp.LpVariable(f'y_{i}', cat='Binary') for i in I}

# Objective
prob += pulp.lpSum(w[i] * y[i] for i in I)

# Constraints
prob += pulp.lpSum(x[j] for j in J) == k  # Cardinality
for i in I:
    prob += y[i] <= pulp.lpSum(a[i][j] * x[j] for j in J)  # Coverage

# solve with status / termination checks
solver = pulp.PULP_CBC_CMD(timeLimit=[TIME_LIMIT], gapRel=0.0, msg=True)
prob.solve(solver)

status = pulp.LpStatus[prob.status]
if status == 'Optimal':
    selected = [j for j in J if pulp.value(x[j]) > 0.5]
    covered = [i for i in I if pulp.value(y[i]) > 0.5]
    # ... validation and output
```

### Common Pitfalls
- Using `pulp.lpSum` incorrectly inside constraints, leading to silent model building errors.
- Not setting `gapRel=0.0`, which may cause the solver to stop early with a suboptimal solution.
- Assuming the model is correct without validation, especially for the first run with new data. The brute-force check is crucial for debugging.
