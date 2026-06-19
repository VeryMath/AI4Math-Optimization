---
name: Minimum Cost Network Flow
description: |
  Model and solve capacitated network flow problems with supply/demand nodes and linear transportation costs using structured data and solver-aware implementations.
---

# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling language to define a capacitated network flow problem. It emphasizes clean separation of data and model, using Pyomo's `Set`, `Param`, and `Var` components for a declarative formulation that is easy to modify and scale.

### Step 1 - Define Problem Sets and Parameters
- Define a `Set` for nodes (e.g., `model.N`).
- Define a `Set` for arcs as a subset of `model.N × model.N`, populated from available cost or capacity data to ensure sparsity.
- Create `Param` dictionaries for `cost`, `capacity`, and `demand`. Use a consistent sign convention: positive demand indicates a sink (net inflow), negative demand indicates a source (net outflow).
- **Prerequisite Check**: Verify total supply equals total demand (`sum(demand.values()) == 0`) to ensure feasibility. If not balanced, raise an error before building constraints.

### Step 2 - Create Decision Variables
- Define a `Var` for flow on each arc (e.g., `model.x`), with `domain=pyo.NonNegativeReals`.
- Set variable bounds directly using the `bounds` argument or via constraints; for capacity, it's often cleaner to use a separate constraint for clarity and potential dual value access.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `i` in `model.N`, create a constraint: `sum(model.x[i,j] for j if (i,j) in arcs) - sum(model.x[j,i] for j if (j,i) in arcs) == demand[i]`.
- Implement this rule efficiently by pre-computing incoming/outgoing arc lists or using Pyomo's `Arc` component if available.

### Step 4 - Add Capacity Constraints
- For each arc `(i,j)` in the arc set, add a constraint: `model.x[i,j] <= capacity[i,j]`.
- Use `Constraint.Skip` for arcs without explicit capacity to maintain a sparse model.

### Step 5 - Define Linear Cost Objective
- Define the objective to minimize: `sum(cost[i,j] * model.x[i,j] for (i,j) in arcs)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: subset of N × N, directed arcs"
  ],
  "parameters": [
    "demand[i ∈ N]: net demand (positive for sink, negative for source)",
    "cost[(i,j) ∈ A]: unit flow cost",
    "capacity[(i,j) ∈ A]: maximum flow"
  ],
  "decision_variables": [
    "x[(i,j) ∈ A]: non-negative flow"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ A} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "flow_conservation[i ∈ N]: ∑_{j:(i,j) ∈ A} x[i,j] - ∑_{j:(j,i) ∈ A} x[j,i] = demand[i]",
    "capacity[(i,j) ∈ A]: x[i,j] ≤ capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Using a single sign convention for demand/supply without clear documentation, leading to sign errors in constraints.
- Creating variables and constraints for all possible node pairs instead of only existing arcs, resulting in a dense, inefficient model.
- Implementing flow conservation with nested generator expressions that cause `KeyError` by accessing invalid variable indices.
- Redundantly setting `bounds=(0, None)` on variables already declared with `domain=pyo.NonNegativeReals`.
- Skipping the supply-demand balance check, which can cause silent infeasibility.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP/MILP solver (HiGHS or CBC) via `SolverFactory`. Focus on robust solution handling, including status checks, graceful failure reporting, and optional solution verification.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set appropriate options: `time_limit`, `threads` (if supported), and `presolve="on"`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `feasible`.
- **Failure Guard**: If status is not acceptable, raise a `RuntimeError` with the solver status and termination condition. Do not attempt to load or output a solution.

### Step 3 - Load and Extract Solution
- If status is good, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Retrieve non-zero flows by iterating over `model.x` and filtering with a tolerance (e.g., `if pyo.value(model.x[i,j]) > 1e-6`).

### Step 4 - (Optional) Verify Solution
- Programmatically verify flow conservation at each node by recomputing net flow from the solution.
- Check that all flows respect capacity bounds within a numerical tolerance.
- This step is for debugging and should be optional in production.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... model construction ...

solver = pyo.SolverFactory("highs")
solver.options = {"time_limit": 30, "presolve": "on"}
results = solver.solve(model, load_solutions=False, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    # Extract flows...
else:
    raise RuntimeError(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Using `tee=True` in production, generating excessive solver logs.
- Setting solver options not supported by the backend (e.g., `"threads"` for some CBC versions).
- Not checking termination condition before loading solutions, risking `NoFeasibleSolutionError`.
- Implementing redundant verification by re-solving the model instead of checking the existing solution.
- Outputting a numeric objective value when the solver has not returned a valid solution.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver API (`pywraplp`) for a more imperative, programmatic model build. It is well-suited for rapid prototyping and problems where the model structure is generated algorithmically. Variable bounds are set directly upon creation, integrating capacity constraints.

### Step 1 - Initialize Solver and Data Structures
- Choose a solver backend: `solver = pywraplp.Solver.CreateSolver('GLOP')` for LP or `'CBC'` for MILP.
- Store problem parameters in nested dictionaries or lists keyed by node indices: `cost`, `capacity`, `demand`.
- Use a consistent sign convention for demand (e.g., positive = sink, negative = source).
- **Prerequisite Check**: Verify total supply equals total demand (`sum(demand.values()) == 0`). If not balanced, raise an error before building constraints.

### Step 2 - Create Flow Variables with Integrated Bounds
- For each directed arc `(i, j)` where capacity data exists, create a variable: `x[i][j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')`.
- This directly enforces non-negativity and capacity upper bounds.

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, create a constraint object: `constraint = solver.Constraint(demand[i], demand[i])`.
- For each outgoing arc `(i, j)`, add `-1 * x[i][j]` to the constraint (representing outflow).
- For each incoming arc `(j, i)`, add `+1 * x[j][i]` to the constraint (representing inflow).
- This yields: `inflow - outflow = demand[i]`.

### Step 4 - Define Linear Cost Objective
- Create the objective: `objective = solver.Objective()`.
- For each arc `(i, j)`, add term `cost[i][j] * x[i][j]` to the objective.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "N: list of node indices",
    "A: list of (i,j) tuples for existing arcs"
  ],
  "parameters": [
    "demand[i ∈ N]: net demand",
    "cost[(i,j) ∈ A]: unit flow cost",
    "capacity[(i,j) ∈ A]: maximum flow"
  ],
  "decision_variables": [
    "x[(i,j) ∈ A]: flow variable with bounds [0, capacity[i,j]]"
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{(i,j) ∈ A} cost[i,j] * x[i,j]"
  },
  "constraints": [
    "flow_conservation[i ∈ N]: ∑_{j:(j,i) ∈ A} x[j,i] - ∑_{j:(i,j) ∈ A} x[i,j] = demand[i]"
  ]
}
```

### Common Pitfalls
- Manually managing constraint coefficients with incorrect signs for inflow/outflow.
- Creating variables for non-existent arcs, leading to a dense model and potential key errors.
- Not verifying total supply/demand balance before solving, which can cause infeasibility.
- Mixing parameter types in a single data structure, reducing clarity.

## Solving stage

### Strategy Overview
Solve using OR-Tools' solver object directly. The focus is on efficient model construction, robust solution status checking, and extracting results into a structured format for downstream use.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `status = solver.Solve()`.
- Interpret status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates success.

### Step 2 - Extract and Validate Solution
- If optimal/feasible, get objective value: `obj_val = objective.Value()`.
- Retrieve flow values by iterating over arcs: `flow_val = x[i][j].solution_value()`.
- Filter near-zero flows using a tolerance (e.g., `1e-6`) to report only significant flows.
- Optionally, verify solution by recomputing net flow at each node and checking capacity adherence.

### Step 3 - Handle Failures and Provide Diagnostics
- **Failure Guard**: For non-optimal statuses (e.g., `INFEASIBLE`, `UNBOUNDED`), raise a `RuntimeError` with the solver status. Do not output a numeric objective value or flow values.
- Include diagnostic information such as total supply/demand imbalance or capacity tightness to aid debugging.

### Step 4 - Structure Output
- Return a consistent output format, e.g., a JSON payload containing solver status, objective value, and a list of non-zero flows with details (from, to, amount, cost, capacity).

### Code Usage
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... build model as described ...

status = solver.Solve()
if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    solution_flows = {}
    for i, j in arcs:
        val = x[i][j].solution_value()
        if val > 1e-6:
            solution_flows[(i,j)] = val
    # Package results...
else:
    status_map = {pywraplp.Solver.INFEASIBLE: 'INFEASIBLE', pywraplp.Solver.UNBOUNDED: 'UNBOUNDED'}
    raise RuntimeError(f"Solver status: {status_map.get(status, 'UNKNOWN')}")
```

### Common Pitfalls
- Not using a tolerance when checking for non-zero flows, potentially including numerical noise.
- Running redundant verification solves instead of analyzing the existing solution.
- Printing extensive debug information (like all flows) in production, cluttering output.
- Hardcoding tolerance values without documentation or consideration for problem scale.
- Outputting a numeric objective value when the solver has not returned a valid solution.
