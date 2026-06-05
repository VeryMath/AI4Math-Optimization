---
name: Binary Arc Selection with Flow Conservation
description: |
  Model and solve network optimization problems where arcs are selected via binary variables and flow conservation enforces connectivity from source to sink, minimizing total cost.
---

# Workflow 1 (MIP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Program (MIP) using Pyomo's algebraic modeling language. Define binary variables for arc selection and enforce flow conservation constraints to ensure a connected path from source to sink, with the objective of minimizing total fixed arc costs.

### Step 1 - Define Sets and Parameters
- Define a set `N` for all nodes in the network.
- Define a set `A` for all directed arcs, as `(i,j)` tuples where `i != j`.
- Create a parameter `c` mapping each arc in `A` to its associated cost.
- Define scalar parameters: `source` node, `sink` node, `supply` (net flow from source, e.g., 1), `demand` (net flow into sink, e.g., 1).

### Step 2 - Create Binary Decision Variables
- Create a binary variable `x[i,j]` for each arc in set `A`. A value of 1 indicates the arc is selected.

### Step 3 - Formulate the Objective Function
- Define the objective to minimize the total cost of selected arcs: `min sum( c[i,j] * x[i,j] for (i,j) in A )`.

### Step 4 - Implement Flow Conservation Constraints
- For the source node `s`, enforce net outflow equals the supply: `sum( x[s,j] for j in N if (s,j) in A ) - sum( x[j,s] for j in N if (j,s) in A ) == supply`.
- For the sink node `t`, enforce net inflow equals the demand: `sum( x[j,t] for j in N if (j,t) in A ) - sum( x[t,j] for j in N if (t,j) in A ) == demand`.
- For all intermediate nodes `k` (where `k != s` and `k != t`), enforce flow balance: `sum( x[j,k] for j in N if (j,k) in A ) == sum( x[k,j] for j in N if (k,j) in A )`.

### Formulation Template
```json
{
  "sets": [
    "N: set of nodes",
    "A: set of directed arcs (i,j) where i != j"
  ],
  "parameters": [
    "c[A]: cost for using arc (i,j)",
    "source: source node index",
    "sink: sink node index",
    "supply: net flow from source (e.g., 1)",
    "demand: net flow into sink (e.g., 1)"
  ],
  "decision_variables": [
    "x[A] ∈ {0, 1}: binary arc selection"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( c[i,j] * x[i,j] for (i,j) in A )"
  },
  "constraints": [
    "source_flow: sum( x[source,j] for j in N if (source,j) in A ) - sum( x[j,source] for j in N if (j,source) in A ) == supply",
    "sink_flow: sum( x[j,sink] for j in N if (j,sink) in A ) - sum( x[sink,j] for j in N if (sink,j) in A ) == demand",
    "flow_conservation[k in N, k != source, k != sink]: sum( x[j,k] for j in N if (j,k) in A ) == sum( x[k,j] for j in N if (k,j) in A )"
  ]
}
```

### Common Pitfalls
- Creating variables for non-existent arcs (e.g., self-loops). Always define the arc set `A` explicitly from available cost data.
- Incorrectly signing flow balance constraints for source/sink nodes, leading to infeasibility. Verify net outflow for source is positive and net inflow for sink is positive.
- Assuming binary variables can carry fractional flow in conservation equations. The formulation uses binary selection; flow quantity is implied by the unit supply/demand.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver backend (e.g., Gurobi, CBC, HiGHS). Configure solver options for performance and reliability, then extract and verify the solution.

### Step 1 - Instantiate Solver and Set Options
- Create a solver object using `SolverFactory("solver_name")`.
- Set key options: a time limit (`TimeLimit` or `seconds`), optimality gap (`MIPGap` or `ratio`), thread count for parallelism, and a random seed for reproducibility.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model, tee=False)`.
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`). Proceed only if both indicate a valid solution.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value via `pyo.value(model.obj)`.
- Extract selected arcs by iterating over `model.A` and checking `pyo.value(model.x[arc]) > 0.5`.
- Optionally, verify flow conservation by recalculating inflows/outflows for all nodes using the selected arcs.

### Step 4 - Output Results
- Print the total cost in a standard format (e.g., `RESULT:{total_cost}`) for automated parsing.
- For failures, output a structured JSON payload with status details.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (follow formulation steps)
model = pyo.ConcreteModel()
model.N = pyo.Set(initialize=nodes)
model.A = pyo.Set(initialize=arcs, dimen=2)
model.c = pyo.Param(model.A, initialize=cost_dict)
model.x = pyo.Var(model.A, domain=pyo.Binary)

def obj_rule(m):
    return sum(m.c[i,j] * m.x[i,j] for (i,j) in m.A)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# Add constraints
def source_flow_rule(m):
    return (sum(m.x[i,j] for (i,j) in m.A if i == source) -
            sum(m.x[i,j] for (i,j) in m.A if j == source)) == supply
model.source_flow = pyo.Constraint(rule=source_flow_rule)

def sink_flow_rule(m):
    return (sum(m.x[i,j] for (i,j) in m.A if j == sink) -
            sum(m.x[i,j] for (i,j) in m.A if i == sink)) == demand
model.sink_flow = pyo.Constraint(rule=sink_flow_rule)

def flow_conservation_rule(m, k):
    if k == source or k == sink:
        return pyo.Constraint.Skip
    return (sum(m.x[i,j] for (i,j) in m.A if j == k) ==
            sum(m.x[i,j] for (i,j) in m.A if i == k))
model.flow_conservation = pyo.Constraint(model.N, rule=flow_conservation_rule)

# Solve with configured solver
solver = pyo.SolverFactory("gurobi")
solver.options["TimeLimit"] = 30
solver.options["MIPGap"] = 0.0
solver.options["Threads"] = 4
solver.options["Seed"] = 42

results = solver.solve(model, tee=False)
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    total_cost = float(pyo.value(model.obj))
    selected_arcs = [(i,j) for (i,j) in model.A if pyo.value(model.x[i,j]) > 0.5]
    print(f"RESULT:{total_cost}")
else:
    import json
    payload = {"status": str(status), "termination": str(term)}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to attempts to read solutions from failed solves.
- Accessing variable values for indices not in the variable set, causing KeyErrors. Always iterate over the defined set `model.A`.
- Setting overly restrictive solver options (e.g., `MIPGap=0.0` on large problems) without a time limit, causing excessive runtime.

# Workflow 2 (Specialized Network Solver with OR-Tools)

## Modeling stage

### Strategy Overview
Leverage a specialized network flow algorithm (OR-Tools MinCostFlow) which internally handles flow conservation. Model the problem as a min-cost flow with unit supply at the source, unit demand at the sink, and arc capacities of 1 to enforce binary selection.

### Step 1 - Map Network Elements
- Map node identifiers to consecutive integer indices required by the solver API.
- Define all directed arcs, excluding self-loops.

### Step 2 - Define Arc Capacities and Costs
- Assign a capacity of 1 to each arc to enforce binary usage.
- Assign the given cost as the unit cost for flow on each arc.

### Step 3 - Set Node Supplies
- Set the supply for the source node to the required flow amount (e.g., 1).
- Set the supply for the sink node to the negative of the flow amount (e.g., -1).
- Set the supply for all intermediate nodes to 0.

### Step 4 - Formulate the Optimization Problem
- The solver's internal formulation minimizes `sum( cost[arc] * flow[arc] )` subject to flow conservation at nodes and flow <= capacity on arcs.

### Formulation Template
```json
{
  "sets": [
    "N: set of node indices (0..n-1)",
    "A: list of directed arcs (tail, head)"
  ],
  "parameters": [
    "capacity[A]: 1 for all arcs (enforces binary selection)",
    "unit_cost[A]: cost per unit flow on arc",
    "supply[N]: net flow for each node (source: >0, sink: <0, others: 0)"
  ],
  "decision_variables": [
    "flow[A] ∈ [0, capacity]: continuous flow on each arc"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum( unit_cost[a] * flow[a] for a in A )"
  },
  "constraints": [
    "flow_conservation[i in N]: sum( flow[a] for a in A where a.head == i ) - sum( flow[a] for a in A where a.tail == i ) == supply[i]",
    "capacity[a in A]: flow[a] <= capacity[a]"
  ]
}
```

### Common Pitfalls
- Forgetting to set supplies for all nodes, leading to an undefined flow problem.
- Using arc capacities greater than 1, which allows fractional flow and may not enforce a single path.
- Mismatching node indices between arc definitions and supply assignments.

## Solving stage

### Strategy Overview
Use OR-Tools' `SimpleMinCostFlow` solver, which is optimized for linear min-cost flow problems. Build the network, solve, and extract the solution based on positive flow values.

### Step 1 - Initialize Solver and Add Arcs
- Create a `SimpleMinCostFlow` object.
- For each arc, add it to the solver using `add_arc_with_capacity_and_unit_cost(tail, head, capacity, cost)`.

### Step 2 - Set Node Supplies
- For each node index, call `set_node_supply(node_index, supply_value)`.

### Step 3 - Solve and Check Optimality
- Call `solve()` and check if the return status equals `SimpleMinCostFlow.OPTIMAL`.

### Step 4 - Extract Solution
- Retrieve the total cost via `optimal_cost()`.
- Iterate through all arc indices, using `flow(arc_index)` to get the flow value. Arcs with flow > 0.5 are selected.

### Step 5 - Verify Path Connectivity
- Trace the path from source to sink using the selected arcs to ensure a simple path is formed.

### Code Usage
```python
from ortools.graph.python import min_cost_flow

# Initialize solver
smcf = min_cost_flow.SimpleMinCostFlow()

# Add arcs (assuming arcs_list contains (tail, head, cost) tuples)
for tail, head, cost in arcs_list:
    arc_index = smcf.add_arc_with_capacity_and_unit_cost(tail, head, 1, cost)

# Set supplies
node_count = max(max(tail, head) for tail, head, _ in arcs_list) + 1
for i in range(node_count):
    if i == source_index:
        smcf.set_node_supply(i, 1)
    elif i == sink_index:
        smcf.set_node_supply(i, -1)
    else:
        smcf.set_node_supply(i, 0)

# Solve
status = smcf.solve()
if status == smcf.OPTIMAL:
    total_cost = smcf.optimal_cost()
    selected_arcs = []
    for arc_index in range(smcf.num_arcs()):
        if smcf.flow(arc_index) > 0.5:  # tolerance for binary flow
            selected_arcs.append((smcf.tail(arc_index), smcf.head(arc_index)))
    print(f"RESULT:{total_cost}")
else:
    print(f"RESULT_JSON:{{\"status\": {status}}}")
```

### Common Pitfalls
- Assuming the solver status is boolean; it is an integer constant (`SimpleMinCostFlow.OPTIMAL`).
- Not handling cases where the solver returns `INFEASIBLE` or `UNBALANCED`; always check the status.
- Misinterpreting flow values due to numerical precision; use a tolerance (e.g., > 0.5) when identifying selected arcs.
