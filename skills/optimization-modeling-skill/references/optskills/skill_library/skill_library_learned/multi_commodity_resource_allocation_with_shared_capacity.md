---
name: Multi-Commodity Resource Allocation with Shared Capacity
description: |
  Model and solve integer or linear programs for allocating multiple products across shared, capacity-constrained resources to maximize linear profit, using explicit demand limits and resource usage matrices.
---

# Workflow 1 (Pyomo with HiGHS/CBC for Integer Programming)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's abstract modeling capabilities. This workflow is suited for problems requiring integer solutions (e.g., discrete units) and leverages open-source solvers like HiGHS or CBC for robust solving.

### Step 1 - Define Sets and Parameters
- Define clear sets for commodities (e.g., products, packages) and resources (e.g., routes, machines).
- Store parameters in dictionaries: per-unit revenue, demand limit per commodity, and capacity per resource.
- Define a binary or coefficient matrix mapping each commodity to the resources it consumes.

### Step 2 - Create Bounded Integer Variables
- Instantiate decision variables as `pyo.NonNegativeIntegers` for each commodity.
- Embed demand limits directly as variable upper bounds using the `bounds` argument: `bounds=lambda m, i: (0, demand[i])`.

### Step 3 - Formulate Shared Capacity Constraints
- For each resource, create a linear inequality constraint.
- Sum the consumption across all commodities using the resource, weighted by the usage coefficient.
- Ensure the total does not exceed the resource's capacity.

### Step 4 - Define Linear Profit Objective
- Create an objective to maximize total revenue: the sum of per-unit revenue multiplied by the decision variable for each commodity.

### Formulation Template
```json
{
  "sets": ["commodities", "resources"],
  "parameters": {
    "revenue": {"index": "commodities", "type": "float"},
    "demand_limit": {"index": "commodities", "type": "float"},
    "capacity": {"index": "resources", "type": "float"},
    "usage": {"index": ["commodities", "resources"], "type": "float"}
  },
  "decision_variables": [
    {"name": "x", "index": "commodities", "domain": "NonNegativeIntegers", "bounds": "(0, demand_limit)"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[c] * x[c] for c in commodities)"
  },
  "constraints": [
    {"name": "capacity", "index": "resources", "expression": "sum(usage[c, r] * x[c] for c in commodities) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Assuming missing resource usage data can be guessed; always require a complete usage matrix.
- Creating random or arbitrary constraint coefficients to force feasibility, which changes the fundamental problem.
- Setting an optimality gap (`mip_rel_gap`) to 0.0 for large problems without a time limit, causing excessive solve times.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS or CBC solver via `SolverFactory`. Configure practical limits, verify solution status rigorously, and implement post-solve validation to ensure feasibility and correctness.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` or `solver = pyo.SolverFactory("cbc")`.
- Set options: `time_limit` for runtime control, `mip_rel_gap` (or `ratio`) for optimality tolerance, and `threads` for parallelism.
- Execute the solve with `results = solver.solve(model, tee=False)`.

### Step 2 - Verify Solver Status and Termination
- Check if `results.solver.status` is `SolverStatus.ok`.
- Check if `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If not acceptable, analyze logs or infeasibility; do not proceed to extract a solution.

### Step 3 - Extract and Validate Solution
- Extract the objective value: `obj_val = float(pyo.value(model.obj))`.
- Extract variable values, converting to integers if needed: `sol = {c: int(pyo.value(model.x[c])) for c in model.commodities}`.
- Programmatically verify all constraints: recalculate resource usage and compare against capacities with a small tolerance (e.g., `1e-6`). Also verify each variable is within its demand bound.

### Step 4 - Report Structured Results
- Output key metrics: objective value, solution vector, and resource utilization percentages.
- For binding constraints (usage ≈ capacity), report dual values or shadow prices if available.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (following formulation steps)
model = pyo.ConcreteModel()
# ... [model construction code]

# Solve
solver = pyo.SolverFactory("highs")  # or "cbc"
solver.options["time_limit"] = 30
solver.options["mip_rel_gap"] = 0.0
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# Status / termination checks
status = results.solver.status
term = results.solver.termination_condition
if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_revenue = float(pyo.value(model.obj))
    solution = {c: int(pyo.value(model.x[c])) for c in model.commodities}
    # ... [validation and output]
else:
    # Handle failure, e.g., raise error or return status details
    output = {"status": "failed", "termination_condition": str(term)}
```

### Common Pitfalls
- Trusting a non-optimal or unknown solver status and outputting pseudo numeric answers.
- Not verifying integer solution feasibility against constraints due to solver tolerances.
- Using the same solver settings across all problem scales without adjustment.

# Workflow 2 (OR-Tools with SCIP/CBC for Direct API Control)

## Modeling stage

### Strategy Overview
Formulate the problem using Google's OR-Tools linear solver wrapper (`pywraplp`). This workflow provides direct API control, efficient constraint building via coefficient setting, and is well-suited for prototyping or deployment in environments where Pyomo is not available.

### Step 1 - Initialize Solver and Define Data
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver("SCIP")` or `"CBC_MIXED_INTEGER_PROGRAMMING"`.
- Define data arrays/lists for revenue, demand limits, capacities, and a sparse representation of the resource usage matrix.

### Step 2 - Create Bounded Decision Variables
- For each commodity, create an integer variable with explicit lower and upper bounds: `solver.IntVar(0, demand_limit[i], f"x_{i}")`.
- This encodes non-negativity and demand limits directly.

### Step 3 - Build Capacity Constraints Efficiently
- For each resource, create a constraint object with an upper bound: `constraint = solver.Constraint(0, capacity[r])`.
- Iterate through commodities and use the usage matrix to selectively set coefficients: `if usage[r][i] == 1: constraint.SetCoefficient(x[i], 1)`.

### Step 4 - Set Linear Maximization Objective
- Create the objective: `objective = solver.Objective()`.
- Set all coefficients using `objective.SetCoefficient(x[i], revenue[i])`.
- Call `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["commodities", "resources"],
  "parameters": {
    "revenue": {"index": "commodities", "type": "float"},
    "demand_limit": {"index": "commodities", "type": "float"},
    "capacity": {"index": "resources", "type": "float"},
    "usage": {"index": ["resources", "commodities"], "type": "binary"}
  },
  "decision_variables": [
    {"name": "x", "index": "commodities", "type": "IntVar", "bounds": "[0, demand_limit]"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(revenue[i] * x[i] for i in commodities)"
  },
  "constraints": [
    {"name": "capacity", "index": "resources", "expression": "sum(usage[r][i] * x[i] for i in commodities) <= capacity[r]"}
  ]
}
```

### Common Pitfalls
- Modifying the problem structure (e.g., changing binary usage to fractional) to artificially relax constraints.
- Hardcoding random seeds for data generation in production code without validation.
- Iterating over all commodity-resource pairs without using a sparse representation, hurting performance for large problems.

## Solving stage

### Strategy Overview
Solve the model using the configured OR-Tools solver. Set appropriate limits, extract the solution, and perform verification. The direct API allows fine-grained control and immediate access to solution values.

### Step 1 - Configure Solver Parameters
- Set a time limit: `solver.SetTimeLimit(30000)` for 30 seconds.
- Set the number of threads: `solver.SetNumThreads(4)`.
- For optimality gap, use solver-specific parameters: `solver.SetSolverSpecificParametersAsString("limits/gap=0.0001")`.

### Step 2 - Execute Solve and Check Status
- Execute: `status = solver.Solve()`.
- Check for optimal or feasible status: `status == pywraplp.Solver.OPTIMAL` or `status == pywraplp.Solver.FEASIBLE`.
- If status is not acceptable, do not extract variable values.

### Step 3 - Extract Solution and Compute Metrics
- Extract the objective value: `obj_val = objective.Value()`.
- Extract variable values: `sol = [x[i].solution_value() for i in range(num_commodities)]`.
- Compute resource usage for each constraint to verify feasibility within a small tolerance (e.g., `1e-6`). Also verify each variable is within its demand bound.

### Step 4 - Output Structured Results
- Return a dictionary or JSON containing status, objective value, solution vector, and constraint utilization.
- Include verification flags to indicate if all constraints are satisfied within tolerance.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model (following formulation steps)
solver = pywraplp.Solver.CreateSolver("SCIP")
# ... [variable and constraint creation]

# Configure solver
solver.SetTimeLimit(30000)
solver.SetNumThreads(4)

# Solve with status / termination checks
status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    total_revenue = solver.Objective().Value()
    solution = [x[i].solution_value() for i in range(num_commodities)]
    # ... [validation and output]
else:
    # Handle failure
    output = {"status": "failed", "solver_status": status}
```

### Common Pitfalls
- Treating solver infeasibility as a random seed issue rather than analyzing constraint feasibility.
- Not checking solver status before accessing `.solution_value()`, which can cause errors.
- Using the same time limit across all problem instances without considering complexity.
