---
name: Multi-Commodity Flow Allocation
description: |
  Model and solve multi-source, multi-sink, multi-commodity flow problems with linear profit objectives and exact demand satisfaction using linear programming.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling capabilities to define a multi-dimensional linear program. It structures the problem as a multi-commodity flow with explicit sets for sources, sinks, and commodities, enabling clear constraint expression and easy data integration.

### Step 1 - Define Sets and Parameters
- Define three fundamental sets: `sources`, `sinks`, and `commodities`.
- Create parameter dictionaries: `profit[(source, commodity, sink)]` for unit profit and `demand[(sink, commodity)]` for required quantities.
- Use tuple-indexed dictionaries for efficient data lookup during model construction.

### Step 2 - Create Decision Variables
- Instantiate a three-dimensional variable `x[source, commodity, sink]` representing the flow quantity.
- Set the variable domain to `pyo.NonNegativeReals` to enforce non-negativity constraints automatically.

### Step 3 - Formulate the Objective Function
- Define a linear objective to maximize total profit: `sum(profit[s,c,m] * x[s,c,m] for all s,c,m)`.
- Set the objective sense to `pyo.maximize`.

### Step 4 - Implement Demand Satisfaction Constraints
- For each sink-commodity pair, create a linear equality constraint: `sum(x[s,c,m] for s in sources) == demand[m,c]`.
- This ensures the total supply from all sources exactly matches the demand at each sink for each commodity.

### Formulation Template
```json
{
  "sets": ["sources", "sinks", "commodities"],
  "parameters": [
    {"name": "profit", "index": ["source", "commodity", "sink"], "type": "float"},
    {"name": "demand", "index": ["sink", "commodity"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["source", "commodity", "sink"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,c,m] * x[s,c,m] for s in sources for c in commodities for m in sinks)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["sink", "commodity"], "expression": "sum(x[s,c,m] for s in sources) == demand[m,c]"}
  ]
}
```

### Common Pitfalls
- Forgetting to initialize all required indices in parameter dictionaries, leading to KeyError during model building.
- Using inconsistent indexing order (e.g., `profit[source, sink, commodity]`) between parameters and variables, causing incorrect objective coefficients.
- Neglecting to set the variable domain to non-negative, which allows infeasible negative flows.

## Solving stage

### Strategy Overview
This stage solves the Pyomo model using the HiGHS or CBC LP solver, with robust status checking and solution validation. It includes configuration for performance and reliability, and extracts results into a structured format.

### Step 1 - Configure and Execute the Solver
- Instantiate the solver factory (e.g., `SolverFactory("highs")` or `SolverFactory("cbc")`).
- Set practical options: enable presolve, set a time limit, and specify optimality gap target (e.g., `ratio=0.0`).
- Solve the model with `tee=False` for clean output unless debugging.

### Step 2 - Verify Solver Status and Termination
- Check that the solver status is `SolverStatus.ok`.
- Verify the termination condition is `TerminationCondition.optimal` or `.feasible` before extracting results.
- If status is not ok or termination is not acceptable, handle the error and do not proceed to solution extraction.

### Step 3 - Extract and Validate the Solution
- Extract the objective value using `pyo.value(model.obj)`.
- Iterate through all variables to collect values, filtering out near-zero allocations (e.g., `value > 1e-6`) for clarity.
- Programmatically verify that extracted flows satisfy all demand constraints within a small numerical tolerance.

### Step 4 - Structure and Output Results
- Compose a result dictionary containing the status, objective value, and a dictionary of non-zero flows.
- Output the results in a structured format like JSON for easy parsing and integration.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following modeling stage steps)
model = pyo.ConcreteModel()
# ... define sets, parameters, variables, objective, constraints

# Solve with status / termination checks
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["time_limit"] = 30
solver.options["presolve"] = "on"
# For CBC: solver.options["seconds"] = 30; solver.options["ratio"] = 0.0

results = solver.solve(model, tee=False)

status = results.solver.status
termination = results.solver.termination_condition

if status == SolverStatus.ok and termination in {TerminationCondition.optimal, TerminationCondition.feasible}:
    objective_value = float(pyo.value(model.obj))
    solution = {}
    for idx in model.x:
        val = pyo.value(model.x[idx])
        if val > 1e-6:
            solution[idx] = val
    # Verification logic here
    final_result = {"status": "optimal", "objective": objective_value, "solution": solution}
else:
    final_result = {"status": "failed", "message": f"Solver terminated with status: {status}, condition: {termination}"}
```

### Common Pitfalls
- Attempting to access variable values (`pyo.value`) before confirming the solver terminated successfully, which may raise errors.
- Not filtering near-zero values in the solution output, resulting in cluttered, unreadable results.
- Omitting verification of demand constraints, potentially missing numerical inaccuracies that indicate solver issues.

# Workflow 2 (OR-Tools with GLOP)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver wrapper (`pywraplp`) to construct and solve the model imperatively. It is well-suited for rapid prototyping and deployment in environments where Pyomo is not available, offering direct control over variable and constraint creation.

### Step 1 - Initialize Solver and Data Structures
- Create a solver instance using `pywraplp.Solver.CreateSolver('GLOP')`.
- Organize input data as nested lists or dictionaries: `profit[source][commodity][sink]` and `demand[sink][commodity]`.

### Step 2 - Create Variables with Bounds
- Use nested loops over sources, commodities, and sinks to create variables: `x[s][c][m] = solver.NumVar(0, solver.infinity(), name)`.
- Setting the lower bound to 0 and upper bound to infinity enforces non-negativity and lack of capacity limits.

### Step 3 - Build Demand Satisfaction Constraints
- For each sink `m` and commodity `c`, create a constraint object: `constraint = solver.Constraint(demand[m][c], demand[m][c])`.
- This creates a linear equality constraint with both lower and upper bound set to the demand value.
- Add the coefficient from each source's corresponding variable to this constraint.

### Step 4 - Define the Linear Objective
- Initialize the objective: `objective = solver.Objective()`.
- In nested loops, set each variable's coefficient in the objective using `objective.SetCoefficient(x[s][c][m], profit[s][c][m])`.
- Set the optimization sense to maximization: `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["sources", "sinks", "commodities"],
  "parameters": [
    {"name": "profit", "index": ["source", "commodity", "sink"], "type": "float"},
    {"name": "demand", "index": ["sink", "commodity"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["source", "commodity", "sink"], "lower_bound": 0, "upper_bound": "infinity"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][c][m] * x[s][c][m] for s,c,m)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["sink", "commodity"], "expression": "sum(x[s][c][m] for s in sources) == demand[m][c]"}
  ]
}
```

### Common Pitfalls
- Creating constraints in the wrong loop order, leading to missing coefficients or incorrectly defined constraints.
- Using `solver.infinity()` for an upper bound when there are actual capacity limits, which should be modeled explicitly.
- Not using descriptive variable names, making debugging difficult for larger instances.

## Solving stage

### Strategy Overview
This stage solves the model using the GLOP linear programming solver, extracts the solution, and performs validation. It focuses on efficient solution retrieval and provides a simple, functional output structure.

### Step 1 - Solve and Check Basic Status
- Execute the solver with `solver.Solve()`.
- Check the result status: `pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates a successful solve.
- If the status is not acceptable, handle the failure appropriately without attempting to extract variable values.

### Step 2 - Extract Objective and Solution Values
- Retrieve the objective value using `objective.Value()`.
- Iterate through all created variables, using `var.solution_value()` to get the flow quantity.
- Apply a tolerance (e.g., `value > 1e-6`) to filter out effectively zero allocations for a cleaner solution report.

### Step 3 - Validate Solution Correctness
- Recompute the total supply for each sink-commodity pair from the extracted solution.
- Verify that each computed supply equals the corresponding demand within a small numerical tolerance (e.g., `abs(supply - demand) < 1e-5`).
- Recalculate the total profit from the solution and compare it to the reported objective value.

### Step 4 - Format and Return Results
- Package the results into a dictionary containing the status, objective value, and a list or dictionary of non-zero allocations.
- The output should be easily serializable (e.g., to JSON) for downstream use.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
# ... create variables, constraints, and objective as per modeling stage

# Solve with status / termination checks
status = solver.Solve()
result_status = {pywraplp.Solver.OPTIMAL: 'optimal', pywraplp.Solver.FEASIBLE: 'feasible'}.get(status, 'failed')

if result_status in ['optimal', 'feasible']:
    objective_value = solver.Objective().Value()
    solution = {}
    # Assume `variables` is a dict or list storing all created variable objects
    for var_key, var in variables.items():
        val = var.solution_value()
        if val > 1e-6:
            solution[var_key] = val
    # Add verification logic here
    final_result = {"status": result_status, "objective": objective_value, "solution": solution}
else:
    final_result = {"status": "failed", "message": f"Solver returned status code: {status}"}
```

### Common Pitfalls
- Assuming `solver.Solve()` always returns an optimal solution without checking the status code.
- Not using a tolerance when checking variable values, which may include extremely small non-zero values due to numerical precision.
- Failing to verify the solution against the original demand data, missing potential solver inaccuracies or modeling errors.
