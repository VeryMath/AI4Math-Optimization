---
name: Minimum Cost Network Flow
description: |
  Model and solve capacitated network flow problems with supply/demand nodes and linear transportation costs using structured data and solver-aware implementations.

---
# Workflow 1 (Pyomo with HiGHS/CBC)

## Modeling stage

### Strategy Overview
Use Pyomo's abstract modeling language for a declarative formulation that cleanly separates data and model. This approach is easy to modify, scale, and is well-suited for problems where the network structure is defined by explicit sets and parameters.

### Step 1 - Define Problem Sets and Parameters
- Define a `Set` for nodes (`model.N`).
- Define a `Set` for arcs (`model.A`) as a subset of `model.N × model.N`, populated from available cost or capacity data to ensure sparsity.
- Create `Param` dictionaries for `cost`, `capacity`, and `demand`.
- **Adopt a consistent sign convention**: For each node `i`, assign `demand[i] = net inflow - net outflow`. Therefore, supply nodes (net outflow) have negative demand values; demand nodes (net inflow) have positive demand values.
- **Prerequisite check**: Before solving, verify total supply equals total demand (`sum(d for d in demand.values() if d < 0) == sum(d for d in demand.values() if d > 0)`). If not, the problem is infeasible.

### Step 2 - Create Decision Variables
- Define a `Var` for flow on each arc (`model.x`). For standard capacitated flow, use `domain=pyo.NonNegativeReals` and set capacity via a separate constraint or via variable bounds.
- **For circulation problems or problems with lower bounds**: Define variable bounds directly using the `bounds` argument referencing parameters `lower_bound` and `upper_bound`. This integrates capacity constraints efficiently and reduces explicit constraint count.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `i` in `model.N`, create a constraint: `sum(inflow) - sum(outflow) == demand[i]`.
- In code, implement as: `sum(model.x[j,i] for j if (j,i) in model.A) - sum(model.x[i,j] for j if (i,j) in model.A) == model.demand[i]`.
- For circulation problems (net demand zero at all nodes), set `demand[i] = 0` for all `i`.
- Pre-compute incoming/outgoing arc lists for efficiency, or use Pyomo's `Arc` component if available.

### Step 4 - Add Capacity Constraints (if not integrated via bounds)
- For each arc `(i,j)` in the arc set, add a constraint: `model.x[i,j] <= capacity[i,j]`.
- Use `Constraint.Skip` for arcs without an explicit capacity to maintain a sparse model.

### Step 5 - Define Linear Cost Objective
- Define the objective to minimize: `sum(cost[i,j] * model.x[i,j] for (i,j) in model.A)`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: subset of N × N, directed arcs"
  ],
  "parameters": [
    "demand[i ∈ N]: net demand (positive for sink, negative for source; zero for circulation)",
    "cost[(i,j) ∈ A]: unit flow cost",
    "capacity[(i,j) ∈ A]: maximum flow",
    "lower_bound[(i,j) ∈ A]: minimum flow (optional, default 0)"
  ],
  "decision_variables": [
    "x[(i,j) ∈ A]: flow variable with bounds [lower_bound[i,j], capacity[i,j]]"
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
- Using an inconsistent sign convention for demand/supply without clear documentation.
- Creating variables and constraints for all possible node pairs instead of only existing arcs, resulting in a dense, inefficient model.
- Implementing flow conservation with nested generator expressions that cause `KeyError` by accessing invalid variable indices.
- Redundantly setting `bounds=(0, None)` on variables already declared with `domain=pyo.NonNegativeReals`.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP/MILP solver (HiGHS or CBC) via `SolverFactory`. Focus on robust solution handling, including status checks, graceful failure reporting, and optional solution verification.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("highs")` (or `"cbc"`).
- Set appropriate options: `"time_limit": [TIME_LIMIT]`, `"presolve": "on"`.
- Solve with `load_solutions=False`: `results = solver.solve(model, load_solutions=False, tee=False)`.

### Step 2 - Check Solver Status and Termination
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If not acceptable, analyze and report failure (e.g., `infeasible`, `unbounded`).

### Step 3 - Load and Extract Solution
- If status is good, load the solution: `model.solutions.load_from(results)`.
- Extract the objective value: `obj_val = pyo.value(model.obj)`.
- Retrieve non-zero flows by iterating over `model.x` and filtering with a tolerance (e.g., `if pyo.value(model.x[i,j]) > 1e-6`).

### Step 4 - (Optional) Verify Solution Correctness
- Programmatically verify flow conservation at each node by recomputing net flow from the solution.
- Check that all flows respect capacity and lower bounds within a numerical tolerance.
- **Be aware of multiple optimal solutions**: Network flow problems can have multiple optimal flow distributions with the same objective value. Different solvers may return different flows; verify the objective value matches.
- **Cross-Check with Alternative Solver**: For critical validation, solve the same model with a different solver (e.g., CBC after HiGHS) to confirm optimal objective value and solution integrity.
- This step is for debugging and should be optional in production.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Data
nodes = [...]  # list of node identifiers
demand = {node: value, ...}  # positive for sink, negative for source; zero for circulation
arcs_data = {
    (i, j): {'cost': c, 'cap': cap, 'lb': lb} for all arcs  # lb optional, default 0
}

# Prerequisite check: verify supply-demand balance
total_supply = sum(v for v in demand.values() if v < 0)  # negative values are supply
total_demand = sum(v for v in demand.values() if v > 0)   # positive values are demand
assert abs(total_supply + total_demand) < 1e-6, f"Supply-demand imbalance detected; problem is infeasible. Supply: {-total_supply}, Demand: {total_demand}."

model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs_data.keys(), dimen=2)
model.demand = pyo.Param(model.N, initialize=demand)
model.cost = pyo.Param(model.A, initialize={(i,j): d['cost'] for (i,j), d in arcs_data.items()})
model.capacity = pyo.Param(model.A, initialize={(i,j): d['cap'] for (i,j), d in arcs_data.items()})
model.lower_bound = pyo.Param(model.A, initialize={(i,j): d.get('lb', 0) for (i,j), d in arcs_data.items()})

# Define variable with integrated bounds
model.x = pyo.Var(
    model.A,
    bounds=lambda m, i, j: (m.lower_bound[i, j], m.capacity[i, j])
)

def flow_balance_rule(m, i):
    outflow = sum(m.x[i, j] for j in m.N if (i, j) in m.A)
    inflow = sum(m.x[j, i] for j in m.N if (j, i) in m.A)
    return inflow - outflow == m.demand[i]  # inflow - outflow = demand
model.flow_balance = pyo.Constraint(model.N, rule=flow_balance_rule)

def obj_rule(m):
    return sum(m.cost[i, j] * m.x[i, j] for (i, j) in m.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

solver = pyo.SolverFactory("highs")
solver.options = {"time_limit": [TIME_LIMIT], "presolve": "on"}
results = solver.solve(model, load_solutions=False, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    model.solutions.load_from(results)
    obj_val = pyo.value(model.obj)
    print(f"RESULT:{obj_val}")
    for (i, j) in model.A:
        val = pyo.value(model.x[i, j])
        if val > 1e-6:
            print(f"  x[{i},{j}] = {val:.4f}")
else:
    raise RuntimeError(f"Solver failed: {results.solver.status}, {results.solver.termination_condition}")
```

### Common Pitfalls
- Using `tee=True` in production, generating excessive solver logs.
- Setting solver options not supported by the backend (e.g., `"threads"` for some CBC versions).
- Not checking termination condition before loading solutions, risking `NoFeasibleSolutionError`.
- Implementing redundant verification by re-solving the model instead of checking the existing solution.

# Workflow 2 (OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
Use Google OR-Tools' linear solver API (`pywraplp`) for an imperative, programmatic model build. This is well-suited for rapid prototyping and problems where the model structure is generated algorithmically. Variable bounds are set directly upon creation, integrating capacity constraints.

### Step 1 - Initialize Solver and Data Structures
- Choose a solver backend: `solver = pywraplp.Solver.CreateSolver('GLOP')` for LP or `'CBC'` for MILP.
- Store problem parameters in nested dictionaries or lists keyed by node indices: `cost`, `capacity`, `demand`, `lower_bound` (optional, default 0).
- **Adopt a consistent sign convention**: For each node `i`, assign `demand[i] = net inflow - net outflow`. Therefore, supply nodes (net outflow) have negative demand values; demand nodes (net inflow) have positive demand values.
- **Prerequisite check**: Verify total supply equals total demand (`sum(v for v in demand.values() if v < 0) == sum(v for v in demand.values() if v > 0)`) before solving; if not, the problem is infeasible.

### Step 2 - Create Flow Variables with Integrated Bounds
- For each directed arc `(i, j)` where capacity data exists, create a variable: `x[i][j] = solver.NumVar(lower_bound[i][j], capacity[i][j], f'x_{i}_{j}')`.
- This directly enforces lower and upper bounds.

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
    "demand[i ∈ N]: net demand (positive for sink, negative for source; zero for circulation)",
    "cost[(i,j) ∈ A]: unit flow cost",
    "capacity[(i,j) ∈ A]: maximum flow",
    "lower_bound[(i,j) ∈ A]: minimum flow (optional, default 0)"
  ],
  "decision_variables": [
    "x[(i,j) ∈ A]: flow variable with bounds [lower_bound[i,j], capacity[i,j]]"
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
Solve using OR-Tools' solver object directly. Focus on efficient model construction, robust solution status checking, and extracting results into a structured format for downstream use.

### Step 1 - Execute Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `status = solver.Solve()`.
- Interpret status: `status == pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates success.

### Step 2 - Extract and Validate Solution
- If optimal/feasible, get objective value: `obj_val = objective.Value()`.
- Retrieve flow values by iterating over arcs: `flow_val = x[i][j].solution_value()`.
- Filter near-zero flows using a tolerance (e.g., `1e-6`) to report only significant flows.
- **Optionally verify solution correctness**: Recompute net flow at each node and check bound adherence.
- **Be aware of multiple optimal solutions**: Different solvers may return different flow distributions; verify the objective value matches.

### Step 3 - Handle Failures and Provide Diagnostics
- For non-optimal statuses (e.g., `INFEASIBLE`, `UNBOUNDED`), output a structured error message.
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
            solution_flows[(i, j)] = val
    # Package results...
else:
    # Handle failure
    status_map = {pywraplp.Solver.INFEASIBLE: 'INFEASIBLE', ...}
    raise RuntimeError(f"Solver status: {status_map.get(status, 'UNKNOWN')}")
```

### Common Pitfalls
- Not using a tolerance when checking for non-zero flows, potentially including numerical noise.
- Running redundant verification solves instead of analyzing the existing solution.
- Printing extensive debug information (like all flows) in production, cluttering output.
- Hardcoding tolerance values without documentation or consideration for problem scale.
