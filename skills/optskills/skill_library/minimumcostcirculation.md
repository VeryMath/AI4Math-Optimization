---
name: MinimumCostCirculation
description: |
  Model and solve minimum-cost circulation problems on directed networks with flow conservation, arc bounds, and linear costs using either a direct solver API or a modeling framework.

---
# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
Structure the problem as a linear program (LP) by directly creating variables with bounds and adding flow conservation constraints node-by-node. This approach uses a solver's native API for efficient, low-overhead model construction.

### Step 1 - Define Network Data Structure
- Store nodes as a list of unique identifiers.
- Store arcs as a list of tuples `(from_node, to_node)`.
- Create parallel lists or dictionaries for arc properties: `cost`, `lower_bound`, `upper_bound`.

### Step 2 - Create Variables with Embedded Bounds
- For each arc, create a continuous solver variable `flow[arc]`.
- Directly set the variable's lower and upper bounds using the provided `lower_bound[arc]` and `upper_bound[arc]` during creation.

### Step 3 - Formulate Flow Conservation Constraints
- For each node `n`, identify all arcs where `to_node == n` (inflow) and where `from_node == n` (outflow).
- Add a linear constraint: `sum(inflow_flows) == sum(outflow_flows)`.

### Step 4 - Define Linear Objective
- Set the objective to minimize `sum(cost[arc] * flow[arc] for arc in arcs)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "nodes", "description": "Set of all nodes in the network."},
    {"name": "arcs", "description": "Set of directed arcs, each defined as (from_node, to_node)."}
  ],
  "parameters": [
    {"name": "cost", "set": "arcs", "description": "Unit cost of flow per arc."},
    {"name": "lower_bound", "set": "arcs", "description": "Minimum required flow on an arc."},
    {"name": "upper_bound", "set": "arcs", "description": "Maximum allowed flow on an arc."}
  ],
  "decision_variables": [
    {"name": "flow", "set": "arcs", "type": "continuous", "description": "Amount of flow on each arc."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a] * flow[a] for a in arcs)"
  },
  "constraints": [
    {"name": "flow_conservation", "set": "nodes", "expression": "sum(flow[a] for a in arcs if arc_to[a]==n) == sum(flow[a] for a in arcs if arc_from[a]==n)"},
    {"name": "arc_bounds", "set": "arcs", "expression": "lower_bound[a] <= flow[a] <= upper_bound[a]"}
  ]
}
```

### Common Pitfalls
- Forgetting to handle arcs with no explicit upper bound, leading to unbounded variables. Always define a finite upper bound, even if large.
- Incorrectly identifying inflow/outflow arcs due to mismatched node indexing. Use consistent data structures.
- Creating duplicate constraints for nodes with no incident arcs, which may cause solver errors. Filter nodes based on incident arcs.

## Solving stage

### Strategy Overview
Use a dedicated LP solver (like GLOP) through its Python API. Focus on building the model efficiently, solving, and rigorously checking the solution status before extracting results.

### Step 1 - Initialize Solver and Build Model
- Create a solver instance (e.g., `pywraplp.Solver.CreateSolver('GLOP')`).
- Follow the modeling steps to add variables, constraints, and the objective.

### Step 2 - Solve and Check Status
- Call `solver.Solve()`.
- Check the return status. Accept `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE`, `UNBOUNDED`, or `ABNORMAL` statuses with informative error messages.

### Step 3 - Extract and Verify Solution
- If the status is acceptable, retrieve the objective value.
- Retrieve variable values for all arcs. Optionally, filter and print only active arcs (flow > tolerance).
- Programmatically verify key properties: flow conservation at each node and adherence to arc bounds within a small tolerance.

### Step 4 - Output Results
- Format the output as required (e.g., a simple `print(f"RESULT:{objective_value}")` or a JSON dictionary of flows).
- Ensure the output is parseable by downstream processes.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
flow_vars = {}
for a in arcs:
    flow_vars[a] = solver.NumVar(lower_bound[a], upper_bound[a], f'flow_{a}')
# ... add constraints and objective

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    objective_value = solver.Objective().Value()
    solution = {a: flow_vars[a].solution_value() for a in arcs}
else:
    raise Exception(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `FEASIBLE` status guarantees optimality. It does not; it only confirms a feasible solution was found.
- Not using a tolerance (e.g., `1e-6`) when checking flow conservation equality due to floating-point arithmetic.
- Extracting variable values without first confirming a successful solve status.

# Workflow 2 (Modeling Framework - Pyomo)

## Modeling stage

### Strategy Overview
Use a modeling framework (Pyomo) to declaratively define sets, parameters, variables, and constraints. This approach separates the problem formulation from the solver interface, improving readability and maintainability for complex networks.

### Step 1 - Define Abstract Sets and Parameters
- Declare `pyo.Set` objects for `nodes` and `arcs` (with `dimen=2`).
- Declare `pyo.Param` objects for `cost`, `lower_bound`, and `upper_bound`, indexed by `arcs`.

### Step 2 - Create Variables with Rule-Based Bounds
- Create a `pyo.Var` object `flow` indexed by `arcs` within the `NonNegativeReals` domain.
- Use a rule or loop to set the `lower_bound` and `upper_bound` attributes for each variable based on the corresponding parameters.

### Step 3 - Declare Flow Conservation Constraints
- Define a `pyo.Constraint` rule indexed by `nodes`.
- Within the rule for a node `n`, sum flows on arcs where the destination is `n` (inflow) and equate it to the sum of flows on arcs where the origin is `n` (outflow).

### Step 4 - Define the Objective
- Create a `pyo.Objective` rule to minimize the sum of `cost[arc] * flow[arc]` over all arcs.

### Formulation Template
```json
{
  "sets": [
    {"name": "N", "description": "Set of nodes."},
    {"name": "A", "description": "Set of directed arcs (i,j).", "dimen": 2}
  ],
  "parameters": [
    {"name": "c", "set": "A", "description": "Cost per unit flow on arc."},
    {"name": "l", "set": "A", "description": "Lower bound for flow on arc."},
    {"name": "u", "set": "A", "description": "Upper bound (capacity) for flow on arc."}
  ],
  "decision_variables": [
    {"name": "x", "set": "A", "type": "continuous", "description": "Flow on each arc."}
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(c[a] * x[a] for a in A)"
  },
  "constraints": [
    {"name": "balance", "set": "N", "expression": "sum(x[(i,n)] for (i,n) in A) == sum(x[(n,j)] for (n,j) in A)"}
  ]
}
```

### Common Pitfalls
- Defining parameter dictionaries with missing keys for some arcs, causing KeyError during model instantiation. Ensure all arcs have defined values, using `.get()` with defaults if needed.
- Inefficient constraint rules that iterate over all arcs for every node, leading to O(|N|*|A|) complexity. Use pre-computed dictionaries mapping nodes to incident arcs.
- Forgetting to call `model_instance = model.create_instance(data)` when using an abstract model, leaving the model un-initialized.

## Solving stage

### Strategy Overview
Use Pyomo's `SolverFactory` to interface with a capable LP solver (e.g., HiGHS, CBC). Configure solver options for performance and reliability, then solve the instance and meticulously inspect the results object.

### Step 1 - Instantiate Model and Select Solver
- Create a concrete model instance with the provided network data.
- Initialize the solver: `solver = pyo.SolverFactory('highs')`.

### Step 2 - Configure Solver and Solve
- Set solver options such as `time_limit`, `threads`, and `mip_rel_gap` (if applicable).
- Execute `results = solver.solve(model, tee=False)`.

### Step 3 - Validate Solution Status
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If status is not ok or termination is not acceptable, analyze logs and raise an error.

### Step 4 - Extract and Process Solution
- Load the solution into the model instance: `model.solutions.load_from(results)`.
- Access the objective value via `pyo.value(model.obj)`.
- Iterate over the `flow` variable to extract values, applying a tolerance filter (e.g., `> 1e-6`) to identify active arcs.

### Step 5 - Report and Verify
- Format the output (objective value and active flows).
- Optionally, run a post-solve verification script to check flow conservation and bound adherence programmatically.

### Code Usage
```python
# build model from formulation
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
model.x = pyo.Var(model.A, domain=pyo.NonNegativeReals, bounds=arc_bounds_rule)
# ... define constraints and objective

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
results = solver.solve(model)
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
    objective_value = pyo.value(model.obj)
else:
    raise Exception(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Confusing `SolverStatus` (communication status) with `TerminationCondition` (solution quality). Both must be checked.
- Attempting to access variable values (`pyo.value(model.x[arc])`) before loading the solution, which returns `None`.
- Not setting `tee=True` during initial debugging to see the solver's log output.
