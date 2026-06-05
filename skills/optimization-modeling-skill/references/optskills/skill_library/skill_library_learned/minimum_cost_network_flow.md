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
- Define a `Set` for arcs as a subset of `model.N × model.N`, populated **only from available cost or capacity data** to ensure sparsity and avoid assuming all possible node pairs exist.
- Create `Param` dictionaries for `cost`, `capacity`, and `supply`. Use a consistent sign convention: **positive supply indicates a source (net outflow), negative supply indicates a sink (net inflow)**.
- **Prerequisite check:** Verify total supply equals total demand (`sum(supply.values()) == 0`) before solving. If not balanced, report the imbalance and abort modeling to prevent guaranteed infeasibility.

### Step 2 - Create Decision Variables
- Define a `Var` for flow on each arc (e.g., `model.x`), with `domain=pyo.NonNegativeReals`.
- Set variable bounds directly using the `bounds` argument or via constraints; for capacity, it's often cleaner to use a separate constraint for clarity and potential dual value access.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `i` in `model.N`, create a constraint: `outflow - inflow == supply[i]`, where supply is positive for sources and negative for sinks.
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
    "A: subset of N × N, directed arcs (populated only from provided data)"
  ],
  "parameters": [
    "supply[i ∈ N]: net supply (positive for source, negative for sink)",
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
    "flow_conservation[i ∈ N]: ∑_{j:(i,j) ∈ A} x[i,j] - ∑_{j:(j,i) ∈ A} x[j,i] = supply[i]",
    "capacity[(i,j) ∈ A]: x[i,j] ≤ capacity[i,j]"
  ]
}
```

### Common Pitfalls
- Using a single sign convention for supply/demand without clear documentation, leading to sign errors in constraints.
- **Creating variables and constraints for all possible node pairs instead of only existing arcs**, resulting in a dense, inefficient model.
- Implementing flow conservation with nested generator expressions that cause `KeyError` by accessing invalid variable indices.
- Redundantly setting `bounds=(0, None)` on variables already declared with `domain=pyo.NonNegativeReals`.
- **Failure guard:** Omitting the supply-demand balance check before solving guarantees infeasibility; always perform this check.
- **Adding constraints not specified in the problem** (e.g., extra node capacity constraints) which may create confusion or incorrect models.

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
- **Failure guard:** If status is not `ok` or termination condition is not `optimal`/`feasible`, do not attempt to load solutions. Analyze and report failure (e.g., `infeasible`, `unbounded`). Do not output pseudo numeric answers.

### Step 3 - Load and Extract Solution
- If status is good, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Retrieve non-zero flows by iterating over `model.x` and filtering with a tolerance (e.g., `if pyo.value(model.x[i,j]) > 1e-6`).

### Step 4 - (Optional) Verify Solution
- Programmatically verify flow conservation at each node by recomputing net flow from the solution.
- Check that all flows respect capacity bounds within a numerical tolerance.
- **This step is for debugging and should be optional in production.** Avoid running multiple solver calls or redundant verification solves once a consistent solution is obtained.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data
nodes = list(range(N))  # N = number of nodes
supply = {i: ...}       # positive for sources, negative for sinks
cost = {(i,j): ...}     # unit cost for each arc
capacity = {(i,j): ...} # capacity for each arc
arcs = list(cost.keys())  # Define arcs only from provided data

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
model.supply = pyo.Param(model.N, initialize=supply)
model.cost = pyo.Param(model.A, initialize=cost)
model.capacity = pyo.Param(model.A, initialize=capacity)
model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals)

def flow_balance_rule(m, i):
    outflow = sum(m.x[i,j] for j in m.N if (i,j) in m.A)
    inflow = sum(m.x[j,i] for j in m.N if (j,i) in m.A)
    return outflow - inflow == m.supply[i]
model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

def capacity_rule(m, i, j):
    return m.x[i,j] <= m.capacity[i,j]
model.capacity_constr = pyo.Constraint(model.A, rule=capacity_rule)

def obj_rule(m):
    return sum(m.cost[i,j] * m.x[i,j] for (i,j) in m.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

solver = pyo.SolverFactory("highs")
solver.options = {"time_limit": 30, "presolve": "on"}
results = solver.solve(model, load_solutions=False, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    print(f"Optimal objective: {obj_val}")
    # Optional verification (for debugging)
    for i in nodes:
        outflow = sum(pyo.value(model.x[i,j]) for j in nodes if (i,j) in arcs)
        inflow = sum(pyo.value(model.x[j,i]) for j in nodes if (j,i) in arcs)
        net = outflow - inflow
        assert abs(net - supply[i]) < 1e-6, f"Balance violation at node {i}"
    for (i,j) in arcs:
        val = pyo.value(model.x[i,j])
        assert val <= capacity[(i,j)] + 1e-6, f"Capacity violation on arc ({i},{j})"
else:
    raise RuntimeError(f"Solver failed: status={results.solver.status}, termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Using `tee=True` in production, generating excessive solver logs.
- Setting solver options not supported by the backend (e.g., `"threads"` for some CBC versions).
- **Failure guard:** Not checking termination condition before loading solutions, risking `NoFeasibleSolutionError` or outputting invalid numeric results.
- **Running excessive verification or multiple solver calls** after obtaining a consistent solution, wasting computational resources.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver API (`pywraplp`) for a more imperative, programmatic model build. It is well-suited for rapid prototyping and problems where the model structure is generated algorithmically. Variable bounds are set directly upon creation, integrating capacity constraints.

### Step 1 - Initialize Solver and Data Structures
- Choose a solver backend: `solver = pywraplp.Solver.CreateSolver('GLOP')` for LP or `'CBC'` for MILP.
- Store problem parameters in nested dictionaries or lists keyed by node indices: `cost`, `capacity`, `supply`.
- Use a consistent sign convention for supply: **positive = source (net outflow), negative = sink (net inflow)**.
- **Prerequisite check:** Verify total supply equals total demand (`sum(supply.values()) == 0`) before building constraints. If not balanced, report the imbalance and abort.

### Step 2 - Create Flow Variables with Integrated Bounds
- For each directed arc `(i, j)` **where capacity data exists**, create a variable: `x[i][j] = solver.NumVar(0, capacity[i][j], f'x_{i}_{j}')`.
- This directly enforces non-negativity and capacity upper bounds. **Create variables only for arcs present in the problem data.**

### Step 3 - Build Flow Conservation Constraints
- For each node `i`, create a constraint object: `constraint = solver.Constraint(supply[i], supply[i])`.
- For each outgoing arc `(i, j)`, add `-1 * x[i][j]` to the constraint (representing outflow).
- For each incoming arc `(j, i)`, add `+1 * x[j][i]` to the constraint (representing inflow).
- This yields: `inflow - outflow = supply[i]`.

### Step 4 - Define Linear Cost Objective
- Create the objective: `objective = solver.Objective()`.
- For each arc `(i, j)`, add term `cost[i][j] * x[i][j]` to the objective.
- Set the objective sense to minimization: `objective.SetMinimization()`.

### Formulation Template
```json
{
  "sets": [
    "N: list of node indices",
    "A: list of (i,j) tuples for existing arcs (from provided data)"
  ],
  "parameters": [
    "supply[i ∈ N]: net supply (positive for source, negative for sink)",
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
    "flow_conservation[i ∈ N]: ∑_{j:(j,i) ∈ A} x[j,i] - ∑_{j:(i,j) ∈ A} x[i,j] = supply[i]"
  ]
}
```

### Common Pitfalls
- Manually managing constraint coefficients with incorrect signs for inflow/outflow.
- **Creating variables for non-existent arcs**, leading to a dense model and potential key errors.
- **Failure guard:** Not verifying total supply/demand balance before solving, which can cause infeasibility; always perform this check.
- **Adding constraints not specified in the problem** (e.g., extra node capacity constraints) which may create confusion or incorrect models.

## Solving stage

### Strategy Overview
Solve using OR-Tools' solver object directly. The focus is on efficient model construction, robust solution status checking, and extracting results into a structured format for downstream use.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `status = solver.Solve()`.
- Interpret status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates success.
- **Failure guard:** For any other status (e.g., `INFEASIBLE`, `UNBOUNDED`), do not attempt to extract solution values. Report the status and abort.

### Step 2 - Extract and Validate Solution
- If optimal/feasible, get objective value: `obj_val = objective.Value()`.
- Retrieve flow values by iterating over arcs: `flow_val = x[i][j].solution_value()`.
- Filter near-zero flows using a tolerance (e.g., `1e-6`) to report only significant flows.
- Optionally, verify solution by recomputing net flow at each node and checking capacity adherence. **Avoid redundant verification solves.**

### Step 3 - Handle Failures and Provide Diagnostics
- For non-optimal statuses, output a structured error message.
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
    # Handle failure
    status_map = {pywraplp.Solver.INFEASIBLE: 'INFEASIBLE', ...}
    raise RuntimeError(f"Solver status: {status_map.get(status, 'UNKNOWN')}")
```

### Common Pitfalls
- Not using a tolerance when checking for non-zero flows, potentially including numerical noise.
- **Running redundant verification solves** instead of analyzing the existing solution.
- Printing extensive debug information (like all flows) in production, cluttering output.
- Hardcoding tolerance values without documentation or consideration for problem scale.
- **Failure guard:** Trusting non-optimal statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) and extracting solution values, which produces invalid numeric results. Always check status before extraction.
