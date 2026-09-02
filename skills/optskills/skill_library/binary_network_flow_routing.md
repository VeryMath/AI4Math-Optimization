---
name: Binary Network Flow Routing
description: |
  Model and solve network flow problems with binary arc selection variables, enforcing flow conservation and minimizing linear costs, using either a direct solver API or a modeling framework.
---

# Workflow 1 (Direct Solver API)

## Modeling stage

### Strategy Overview
This workflow uses a direct solver API (e.g., OR-Tools) to construct a binary network flow model. It is procedural, building variables and constraints in loops, and is well-suited for integration into larger scripts or performance-critical applications.

### Step 1 - Define Network Structure
- Enumerate all nodes and all possible directed arcs (i,j) where i ≠ j.
- Store arc costs in a dictionary keyed by (i,j) for efficient lookup.
- Define node supply/demand in a dictionary, where positive values are supply, negative are demand, and zero are transshipment nodes. For a single-path routing problem, set source supply = 1, sink demand = -1, and all others = 0.

### Step 2 - Create Binary Decision Variables
- For each directed arc, create a binary variable `x[i,j] ∈ {0,1}` using `solver.BoolVar(name)`.
- Store variables in a dictionary keyed by (i,j) for easy reference in constraints and objective.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `n`, create a constraint: `sum(outgoing flow) - sum(incoming flow) = supply_demand[n]`.
- Compute sums by iterating over all arcs and filtering based on origin/destination.

### Step 4 - Define Linear Cost Objective
- Formulate the objective as the sum of `cost[i,j] * x[i,j]` over all arcs.
- Set the sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "NODES: list of node identifiers",
    "ARCS: list of directed arcs (i,j) where i, j ∈ NODES and i ≠ j"
  ],
  "parameters": [
    "cost[ARCS]: linear cost per arc usage",
    "supply_demand[NODES]: net flow required at each node"
  ],
  "decision_variables": [
    "x[ARCS] ∈ {0, 1}: binary arc selection"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for all (i,j) in ARCS)"
  },
  "constraints": [
    "flow_conservation[n] for each n in NODES: sum(x[n,j] for j if (n,j) in ARCS) - sum(x[i,n] for i if (i,n) in ARCS) = supply_demand[n]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops (i,i) from the arc set, which can lead to nonsensical solutions.
- Incorrectly signing the supply/demand parameter in the flow balance equation, causing flow to reverse direction.
- Using a sparse cost dictionary without ensuring all possible arcs are defined, which may unintentionally prohibit valid routes.

## Solving stage

### Strategy Overview
Solve the constructed model using a Mixed-Integer Programming (MIP) solver like SCIP or CBC via a direct API. Configure solver settings for performance and reproducibility, then extract and verify the solution.

### Step 1 - Configure and Execute Solver
- Instantiate the solver (e.g., `solver = ort.Solver.CreateSolver("SCIP")`) and verify it is not null.
- Set a time limit (e.g., `[TIME_LIMIT]` milliseconds), optimality gap tolerance (e.g., 0.0 for exact), number of threads, and a random seed for reproducibility.
- Call the solver's `Solve()` method.

### Step 2 - Check Solution Status
- Check if the solver status is `OPTIMAL` or `FEASIBLE`.
- If the status is not acceptable, output a structured error message and halt.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value.
- Iterate over all binary variables, collecting arcs where `solution_value() > 0.5` (accounting for numerical tolerance).
- Optionally, recalculate node balances from the selected arcs to verify flow conservation.
- Reconstruct the path from source to sink by following selected arcs sequentially.

### Code Usage
```python
# build model from formulation
import ortools.linear_solver.pywraplp as ort

solver = ort.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver not created")
# ... (variable and constraint creation as per modeling stage)
solver.Minimize(objective_expr)

# solve with status / termination checks
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

if status in [ort.Solver.OPTIMAL, ort.Solver.FEASIBLE]:
    obj_val = solver.Objective().Value()
    solution_arcs = []
    for (i, j), var in x_vars.items():
        if var.solution_value() > 0.5:
            solution_arcs.append((i, j))
    # Output or further processing
else:
    # Handle failure
    print(f"RESULT_JSON:{{\"status\": \"failed\", \"solver_status\": {status}}}")
```

### Common Pitfalls
- Not setting a time limit, which can cause the solver to run indefinitely on difficult instances.
- Failing to check for `FEASIBLE` status in addition to `OPTIMAL`, potentially discarding valid heuristic solutions.
- Using a strict equality (`== 1.0`) to check binary variable values, which may fail due to solver tolerances; always use a threshold (e.g., `> 0.5`).

# Workflow 2 (Modeling Framework with Pyomo)

## Modeling stage

### Strategy Overview
This workflow uses the Pyomo modeling framework to declaratively define the binary network flow problem. It separates model specification from solver execution, improving readability and maintainability, especially for complex models.

### Step 1 - Declare Model Sets and Parameters
- Define `pyo.Set` objects for `nodes` and `arcs`.
- Define `pyo.Param` objects for `cost` (indexed by arcs) and `supply_demand` (indexed by nodes).

### Step 2 - Declare Binary Variables and Objective
- Define `pyo.Var` with `domain=pyo.Binary` for arc selection, indexed by the arc set.
- Define a `pyo.Objective` with the sense `minimize` and expression as the sum of cost times variable over all arcs.

### Step 3 - Implement Flow Balance Rule
- Create a `pyo.Constraint` indexed by nodes.
- For each node, the rule function calculates outflow and inflow using conditional sums over the arc set and enforces equality with the supply/demand parameter.

### Formulation Template
```json
{
  "sets": [
    "NODES: pyomo Set",
    "ARCS: pyomo Set (dimen=2)"
  ],
  "parameters": [
    "cost: pyomo Param indexed by ARCS",
    "supply_demand: pyomo Param indexed by NODES"
  ],
  "decision_variables": [
    "x: pyomo Var indexed by ARCS, domain=Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[i,j] * x[i,j] for (i,j) in ARCS)"
  },
  "constraints": [
    "flow_balance[n] for each n in NODES: sum(x[n,j] for j in NODES if (n,j) in ARCS) - sum(x[i,n] for i in NODES if (i,n) in ARCS) == supply_demand[n]"
  ]
}
```

### Common Pitfalls
- Defining the arc set incorrectly (e.g., missing arcs or including self-loops) leading to an infeasible or incorrect model.
- Using a `ConcreteModel` but initializing parameters with rules that depend on mutable data, causing initialization errors.
- Writing constraint rules that inefficiently iterate over the entire node set for each node, impacting build time for large networks.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a backend solver (e.g., Gurobi, CBC). Configure solver options, execute, and rigorously check termination conditions before extracting results. Includes post-solution verification.

### Step 1 - Configure Solver and Execute
- Use `pyo.SolverFactory` to instantiate the solver (e.g., `"gurobi"` or `"cbc"`).
- Set solver options: time limit (e.g., `[TIME_LIMIT]` seconds), optimality gap, threads, and seed.
- Call `solver.solve(model, tee=False)` to execute.

### Step 2 - Validate Termination Status
- Check `results.solver.status == SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`.
- If checks fail, output a structured failure payload.

### Step 3 - Extract, Verify, and Report Solution
- Retrieve the objective value using `pyo.value(model.obj)`.
- Iterate over `model.arcs` to find selected arcs (`pyo.value(model.x[i,j]) > 0.5`).
- Optionally, run a verification function to recompute node balances and ensure they match supply/demand within tolerance.
- Reconstruct the path from source to sink by following selected arcs sequentially.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

model = pyo.ConcreteModel()
model.nodes = pyo.Set(initialize=NODE_LIST)
model.arcs = pyo.Set(initialize=ARC_LIST, dimen=2)
# ... (parameter, variable, objective, and constraint definitions as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = 0.0
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}):
    obj_val = pyo.value(model.obj)
    selected_arcs = [(i, j) for (i, j) in model.arcs if pyo.value(model.x[i, j]) > 0.5]
    print(f"RESULT:{obj_val}")
else:
    failure_payload = {
        "status": "failed",
        "termination_condition": str(results.solver.termination_condition)
    }
    print(f"RESULT_JSON:{json.dumps(failure_payload)}")
```

### Common Pitfalls
- Accessing variable values without first checking that the solver terminated successfully, which may raise an error.
- Setting `MIPGap=0.0` without a time limit on very large problems, potentially causing excessively long run times.
- Forgetting to import necessary modules (`SolverStatus`, `TerminationCondition`) for proper status checking.
