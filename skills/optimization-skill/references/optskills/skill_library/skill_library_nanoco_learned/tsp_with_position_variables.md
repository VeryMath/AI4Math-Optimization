---
name: TSP with Position Variables
description: |
  Model and solve the Traveling Salesperson Problem using binary arc selection and integer position assignment variables, with explicit subtour elimination constraints, to produce a minimal-distance Hamiltonian cycle.
---

# Workflow 1 (MIP with MTZ using Pyomo/Gurobi)

## Modeling stage

### Strategy Overview
This workflow formulates the TSP as a Mixed-Integer Program (MIP) using the Miller-Tucker-Zemlin (MTZ) subtour elimination constraints. It is implemented in Pyomo and solved with the Gurobi solver, which is well-suited for medium to large-scale routing problems.

### Step 1 - Define Sets and Parameters
- Define a set `CITIES` representing all locations to be visited.
- Define a parameter `distance[i][j]` representing the travel cost from city `i` to city `j`. Ensure `distance[i][i]` is set to a large value or zero, as self-loops are prohibited.

### Step 2 - Create Decision Variables
- Create binary variable `x[i][j]` for all `i, j` in `CITIES`. `x[i][j] = 1` indicates the arc from city `i` to city `j` is selected in the tour.
- Create integer variable `u[i]` for all `i` in `CITIES`. `u[i]` represents the position of city `i` in the tour sequence, starting from 1.

### Step 3 - Formulate Degree and Assignment Constraints
- Add constraints to ensure each city has exactly one outgoing arc: `sum_{j in CITIES, j != i} x[i][j] == 1` for all `i`.
- Add constraints to ensure each city has exactly one incoming arc: `sum_{i in CITIES, i != j} x[i][j] == 1` for all `j`.
- Explicitly forbid self-loops: `x[i][i] == 0` for all `i`.

### Step 4 - Implement Subtour Elimination (MTZ)
- For all `i, j` in `CITIES` where `i != 0` and `j != 0` and `i != j`, add the MTZ constraint: `u[i] - u[j] + n * x[i][j] <= n - 1`. Here, `n` is the total number of cities.
- Fix the position of the start city (city `0`) to break symmetry: `u[0] == 1`.
- Set bounds for position variables: `1 <= u[i] <= n` for all `i`.

### Step 5 - Define the Objective
- Minimize the total travel distance: `sum_{i in CITIES} sum_{j in CITIES, j != i} distance[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": [
    {"name": "CITIES", "description": "Set of all cities/nodes to visit."}
  ],
  "parameters": [
    {"name": "distance", "index": ["CITIES", "CITIES"], "description": "Cost matrix for travel between cities."},
    {"name": "n", "value": "len(CITIES)", "description": "Number of cities."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["CITIES", "CITIES"], "type": "binary", "description": "Arc selection variable."},
    {"name": "u", "index": ["CITIES"], "type": "integer", "bounds": "[1, n]", "description": "Position assignment variable."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in CITIES} sum_{j in CITIES, j != i} distance[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "outgoing_arc", "expression": "sum_{j in CITIES, j != i} x[i][j] == 1", "for": "i in CITIES"},
    {"name": "incoming_arc", "expression": "sum_{i in CITIES, i != j} x[i][j] == 1", "for": "j in CITIES"},
    {"name": "no_self_loop", "expression": "x[i][i] == 0", "for": "i in CITIES"},
    {"name": "mtz", "expression": "u[i] - u[j] + n * x[i][j] <= n - 1", "for": "i in CITIES, j in CITIES where i != 0 and j != 0 and i != j"},
    {"name": "fix_start", "expression": "u[0] == 1"}
  ]
}
```

### Common Pitfalls
- Applying MTZ constraints to the start city (`i=0` or `j=0`), which can make the model infeasible. The start city's position is fixed, so these constraints are not needed for arcs involving it.
- Forgetting to exclude self-loops (`i=j`) from the objective summation, which could incorrectly add zero or large penalty costs.
- Using an incorrect coefficient (like `n-1`) in the MTZ constraint, which may not correctly eliminate all subtours. The standard form uses `n` for problems where the start city position is fixed to 1.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Gurobi solver with configured parameters for reproducibility and performance. After solving, rigorously check the status, extract the solution, and reconstruct the tour sequence.

### Step 1 - Configure and Execute the Solver
- Instantiate the Gurobi solver via Pyomo's `SolverFactory`.
- Set key parameters: `TimeLimit=30`, `MIPGap=0.0` (for optimality), `Threads=4`, and `Seed=42` for deterministic behavior.
- Execute the solve with `tee=True` to output the solver log for debugging.

### Step 2 - Validate Solver Status and Termination
- Check the solver status (`solver.status`). It should be `ok`.
- Check the model termination condition (`model.termination_condition`). Accept `optimal` or `feasible` (for early termination). If the status is not acceptable, do not load the solution and report the condition.

### Step 3 - Extract and Verify the Solution
- Load the solution into the model if the status checks pass.
- Extract the selected arcs by finding all `x[i][j]` variables with a value > 0.5.
- Extract the position assignments from the `u[i]` variables.
- Reconstruct the tour by starting at the designated start city (city `0`) and following the selected arcs until returning to the start.
- Optionally, verify the objective value by manually summing the `distance` along the extracted tour sequence.

### Step 4 - Handle Infeasibility or Errors
- If the model is infeasible, inspect the MTZ constraint formulation and the bounds on position variables. A common error is incorrect indexing in the MTZ constraints.
- If the solver hits the time limit, the best solution found can still be used if the termination condition is `feasible`.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model, tee=True)  # tee=True for logs

# Check solver status
if results.solver.status != pyo.SolverStatus.ok:
    raise RuntimeError(f"Solver failed with status: {results.solver.status}")

# Check termination condition
if model.termination_condition not in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    raise RuntimeError(f"No acceptable solution found. Termination: {model.termination_condition}")

# Load and process solution
model.solutions.load_from(results)
# ... (extract x[i][j] and u[i] values, reconstruct tour)
```

### Common Pitfalls
- Trusting a non-zero solver return code or an `unknown` termination condition as a valid solution. Always perform explicit checks.
- Loading solutions before verifying the solver status, which can lead to errors if the solve failed.
- Not verifying the reconstructed tour against the objective value, which might catch extraction errors.

# Workflow 2 (MIP with MTZ using Pyomo/HiGHS)

## Modeling stage

### Strategy Overview
This workflow also uses the MTZ formulation but is designed for use with the open-source HiGHS solver via Pyomo. It emphasizes parameterization for reusability and includes explicit handling for the start city in constraints.

### Step 1 - Parameterize Model Components
- Define `n = len(CITIES)` dynamically. Use this parameter in constraint coefficients and variable bounds to make the model adaptable.
- Define the `distance` matrix, ensuring it is square and `distance[i][i]` is handled appropriately (e.g., set to 0).

### Step 2 - Instantiate Variables with Bounds
- Create binary variable `x[i][j]` for arc selection.
- Create integer variable `u[i]` for position, with explicit lower bound `1` and upper bound `n`.

### Step 3 - Apply Standard TSP Constraints
- Enforce single outgoing and incoming arc per city using summations that exclude the `i=j` case.
- Explicitly set `x[i][i].fix(0)` to prevent self-loops.

### Step 4 - Apply Subtour Elimination with Start City Handling
- For all `i, j` where `i != 0`, `j != 0`, and `i != j`, add the MTZ constraint: `u[i] - u[j] + (n-1) * x[i][j] <= n-2`. This is an equivalent variant that works when `u[0]` is fixed to 1.
- Fix the start city's position: `u[0].fix(1)`.

### Step 5 - Set the Minimization Objective
- Minimize `sum_{i in CITIES} sum_{j in CITIES} distance[i][j] * x[i][j]`, relying on the fixed zero values on the diagonal to ignore self-loops.

### Formulation Template
```json
{
  "sets": [
    {"name": "CITIES", "description": "Set of all cities/nodes."}
  ],
  "parameters": [
    {"name": "distance", "index": ["CITIES", "CITIES"], "description": "Cost matrix. distance[i][i] should be 0."},
    {"name": "n", "value": "len(CITIES)", "description": "Cardinality of CITIES."}
  ],
  "decision_variables": [
    {"name": "x", "index": ["CITIES", "CITIES"], "type": "binary", "description": "1 if arc i->j is in the tour."},
    {"name": "u", "index": ["CITIES"], "type": "integer", "bounds": "[1, n]", "description": "Visit order of city i."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in CITIES} sum_{j in CITIES} distance[i][j] * x[i][j]"
  },
  "constraints": [
    {"name": "flow_out", "expression": "sum_{j in CITIES} x[i][j] == 1", "for": "i in CITIES"},
    {"name": "flow_in", "expression": "sum_{i in CITIES} x[i][j] == 1", "for": "j in CITIES"},
    {"name": "mtz", "expression": "u[i] - u[j] + (n-1) * x[i][j] <= n-2", "for": "i in CITIES, j in CITIES where i != 0 and j != 0 and i != j"},
    {"name": "start_pos", "expression": "u[0] == 1"}
  ]
}
```
*Note: The `flow_out` and `flow_in` constraints sum over all `j` and `i`, respectively, assuming `x[i][i]` is fixed to 0.*

### Common Pitfalls
- Using the `(n-1)` coefficient in the MTZ constraint but not adjusting the right-hand side to `n-2`, leading to an incorrect formulation.
- Omitting the condition `i != j` in the MTZ constraint, which is unnecessary as `x[i][i]` is fixed to 0 but can cause a modeling error if the constraint is evaluated for `i=j`.
- Not fixing `x[i][i]` to 0, which would allow the solver to select self-loops to satisfy degree constraints trivially.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver, focusing on robust solution loading and verification. This workflow includes explicit checks for solver status and uses a verification strategy for small instances.

### Step 1 - Configure HiGHS Solver
- Instantiate the HiGHS solver via `SolverFactory('appsi_highs')` or the appropriate interface.
- Set parameters: `time_limit=30`, `mip_rel_gap=0.0`, `threads=4`, `presolve="on"`.
- Use `load_solutions=False` in the initial solve command to prevent automatic loading before status checks.

### Step 2 - Check Solution Status Systematically
- After solving, check `results.solver.status`. It must be `ok`.
- Check `model.termination_condition`. Accept `optimal` or `feasible`. For other conditions (like `infeasible` or `maxTimeLimit`), handle accordingly without loading the solution.

### Step 3 - Load Results and Reconstruct Tour
- If status checks pass, load the solution using `model.solutions.load_from(results)`.
- Extract the tour by iterating from the start city: `current = 0`, then repeatedly find `next_city` such that `pyo.value(model.x[current, next_city]) > 0.5`.
- Record the sequence to form the Hamiltonian cycle.

### Step 4 - Implement Verification and Error Handling
- For small `n`, implement a brute-force verification to confirm the extracted tour is a valid cycle and its cost matches the solver's objective value. This is a strong sanity check.
- Structure the output (e.g., as a JSON object) to clearly indicate success/failure, the tour, total distance, and solver status details.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... (define sets, params, variables, constraints, objective as per modeling stage)
# Fix self-loops
for i in model.CITIES:
    model.x[i, i].fix(0)

# solve with status / termination checks
solver = pyo.SolverFactory('appsi_highs') # or 'highs'
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0
solver.options['threads'] = 4
solver.options['presolve'] = 'on'

# Solve without auto-loading
results = solver.solve(model, load_solutions=False)

# Status verification
if results.solver.status != pyo.SolverStatus.ok:
    raise RuntimeError(f"Solver failed: {results.solver.status}")

tc = model.termination_condition
if tc not in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Handle non-success, e.g., log and return empty result
    output = {"status": "failure", "termination_condition": str(tc)}
    # return or raise
else:
    # Load and process solution
    model.solutions.load_from(results)
    tour = [0]
    current = 0
    for _ in range(len(model.CITIES)-1):
        for j in model.CITIES:
            if j != current and pyo.value(model.x[current, j]) > 0.5:
                tour.append(j)
                current = j
                break
    # tour should end back at start city 0
    output = {"status": "success", "tour": tour, "distance": pyo.value(model.obj)}
```

### Common Pitfalls
- Assuming `load_solutions=True` (the default) and trying to access variable values after an unsuccessful solve, which may raise exceptions or return stale data.
- Not verifying that the reconstructed tour forms a complete cycle back to the start city, which could indicate an error in extraction logic.
- For HiGHS, using an incorrect solver factory name or not having the appropriate Pyomo extension installed, leading to a `SolverFactory` error.
