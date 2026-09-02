---
name: Lexicographic Max-Flow Min-Cost Solver
description: |
  Models and solves a two-stage lexicographic optimization problem that first maximizes total flow from source to sink, then minimizes total cost among all maximum-flow solutions.
---

# Workflow 1 (Sequential Pyomo with HiGHS)

## Modeling stage

### Strategy Overview
Formulate the lexicographic objective as two separate Pyomo models solved sequentially. Stage 1 maximizes total flow into the sink. Stage 2 fixes the optimal flow value from Stage 1 and minimizes total cost. Both models share the same variable definitions, flow conservation, and capacity constraints.

### Step 1 - Define Sets and Parameters
- Define a set `NODES` containing all nodes, and a set `ARCS` as a subset of `NODES x NODES`.
- Specify source node `source` and sink node `sink` as scalar parameters.
- Define parameter `capacity[arc]` for each arc, and `cost[arc]` for each arc.

### Step 2 - Declare Decision Variables
- Create a single continuous variable `flow_on_arc[arc]` for each arc in `ARCS`.
- Set domain to `pyo.NonNegativeReals` to enforce nonnegativity.

### Step 3 - Enforce Flow Conservation
- For each intermediate node `n` (not source or sink), write a constraint: `sum(flow_on_arc[i,n] for i in NODES if (i,n) in ARCS) == sum(flow_on_arc[n,j] for j in NODES if (n,j) in ARCS)`.
- Use `pyo.Constraint.Skip` for source and sink nodes.

### Step 4 - Enforce Arc Capacity
- For each arc `(i,j)` in `ARCS`, write: `flow_on_arc[i,j] <= capacity[i,j]`.

### Step 5 - Stage 1 Objective (Max Flow)
- Define objective `obj1` as `sum(flow_on_arc[i,sink] for i in NODES if (i,sink) in ARCS)` with `sense=pyo.maximize`.

### Step 6 - Stage 2 Objective (Min Cost)
- After Stage 1, create a new model with the same variables and constraints.
- Add a fixed-flow constraint: `sum(flow_on_arc[i,sink] for i in NODES if (i,sink) in ARCS) == max_flow_value`.
- Define objective `obj2` as `sum(cost[i,j] * flow_on_arc[i,j] for (i,j) in ARCS)` with `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["NODES", "ARCS"],
  "parameters": ["source", "sink", "capacity[ARCS]", "cost[ARCS]"],
  "decision_variables": ["flow_on_arc[ARCS]"],
  "objective": {
    "sense": "lexicographic (max flow, then min cost)",
    "stage1": "maximize total flow into sink",
    "stage2": "minimize total cost given max flow"
  },
  "constraints": [
    "flow_conservation: sum(inflow) == sum(outflow) for each intermediate node",
    "arc_capacity: flow_on_arc[i,j] <= capacity[i,j] for each arc",
    "nonnegativity: flow_on_arc >= 0 (via domain)",
    "stage2_fixed_flow: total flow into sink equals max_flow_value"
  ]
}
```

### Common Pitfalls
- Forgetting to skip source and sink nodes in flow conservation constraints, causing infeasibility.
- Using the same model object for both stages without properly fixing the flow value, leading to incorrect cost minimization.
- Defining flow conservation with incorrect indexing (e.g., using `for each node` without filtering).

## Solving stage

### Strategy Overview
Use Pyomo with the HiGHS solver for efficient LP solving. Execute Stage 1 to obtain the maximum flow value, then build and solve Stage 2 with the fixed flow constraint. Always check solver status and termination conditions before proceeding.

### Step 1 - Build and Solve Stage 1 Model
- Instantiate `pyo.SolverFactory("highs")` and set `solver.options["time_limit"] = [TIME_LIMIT]`.
- Solve the Stage 1 model: `results = solver.solve(m1, tee=False)`.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Extract `max_flow_value = float(pyo.value(m1.obj1))`.

### Step 2 - Build and Solve Stage 2 Model
- Create a new Pyomo model `m2` with identical variables and constraints.
- Add the fixed-flow constraint using the `max_flow_value` from Stage 1.
- Solve `m2` with the same solver and status checks.
- Extract `min_cost_value = float(pyo.value(m2.obj2))`.

### Step 3 - Extract and Verify Results
- For each arc, retrieve `flow_on_arc` values from `m2`.
- Manually verify flow conservation at all nodes and total cost calculation.
- Output results in a structured format (e.g., JSON with status, max flow, min cost, arc flows).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# --- Stage 1: Max Flow ---
m1 = pyo.ConcreteModel()
m1.NODES = pyo.Set(initialize=node_list)
m1.ARCS = pyo.Set(initialize=arc_list, dimen=2)
m1.capacity = pyo.Param(m1.ARCS, initialize=capacity_dict)
m1.cost = pyo.Param(m1.ARCS, initialize=cost_dict)
m1.flow = pyo.Var(m1.ARCS, domain=pyo.NonNegativeReals)

def flow_conservation_rule(m, n):
    if n == source or n == sink:
        return pyo.Constraint.Skip
    inflow = sum(m.flow[i, n] for i in m.NODES if (i, n) in m.ARCS)
    outflow = sum(m.flow[n, j] for j in m.NODES if (n, j) in m.ARCS)
    return inflow == outflow
m1.flow_cons = pyo.Constraint(m1.NODES, rule=flow_conservation_rule)

def cap_rule(m, i, j):
    return m.flow[i, j] <= m.capacity[i, j]
m1.cap_cons = pyo.Constraint(m1.ARCS, rule=cap_rule)

m1.obj1 = pyo.Objective(
    expr=sum(m1.flow[i, sink] for i in m1.NODES if (i, sink) in m1.ARCS),
    sense=pyo.maximize
)

solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = [TIME_LIMIT]
results = solver.solve(m1, tee=False)
assert results.solver.status == SolverStatus.ok
assert results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}
max_flow_value = float(pyo.value(m1.obj1))

# --- Stage 2: Min Cost ---
m2 = pyo.ConcreteModel()
m2.NODES = pyo.Set(initialize=node_list)
m2.ARCS = pyo.Set(initialize=arc_list, dimen=2)
m2.capacity = pyo.Param(m2.ARCS, initialize=capacity_dict)
m2.cost = pyo.Param(m2.ARCS, initialize=cost_dict)
m2.flow = pyo.Var(m2.ARCS, domain=pyo.NonNegativeReals)

m2.flow_cons = pyo.Constraint(m2.NODES, rule=flow_conservation_rule)
m2.cap_cons = pyo.Constraint(m2.ARCS, rule=cap_rule)

def fixed_flow_rule(m):
    return sum(m.flow[i, sink] for i in m.NODES if (i, sink) in m.ARCS) == max_flow_value
m2.fixed_flow = pyo.Constraint(rule=fixed_flow_rule)

m2.obj2 = pyo.Objective(
    expr=sum(m2.cost[i, j] * m2.flow[i, j] for (i, j) in m2.ARCS),
    sense=pyo.minimize
)

results2 = solver.solve(m2, tee=False)
assert results2.solver.status == SolverStatus.ok
assert results2.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}
min_cost_value = float(pyo.value(m2.obj2))

# Output
print(f"Max flow: {max_flow_value}, Min cost: {min_cost_value}")
```

### Common Pitfalls
- Not checking solver termination condition, leading to use of suboptimal or infeasible solutions.
- Forgetting to create a new model for Stage 2 instead of reusing the Stage 1 model, causing variable conflicts.
- Using `tee=True` in production, which clutters output and slows execution.

# Workflow 2 (OR-Tools Specialized Solvers)

## Modeling stage

### Strategy Overview
Leverage OR-Tools' dedicated network flow solvers (`SimpleMaxFlow` and `SimpleMinCostFlow`) for the lexicographic problem. These solvers are purpose-built for flow problems and handle the underlying algorithms efficiently. The modeling is done via solver API calls rather than algebraic constraints.

### Step 1 - Define Network Topology
- Create a list of arcs as tuples `(from_node, to_node)` with integer node indices.
- Define parallel arrays for arc capacities and unit costs.
- Identify source and sink node indices.

### Step 2 - Stage 1: Max Flow Modeling
- Instantiate `pywrapgraph.SimpleMaxFlow`.
- For each arc, call `AddArcWithCapacity(from_node, to_node, capacity)`.
- Call `Solve(source, sink)` to compute maximum flow.

### Step 3 - Stage 2: Min-Cost Flow Modeling
- Instantiate `pywrapgraph.SimpleMinCostFlow`.
- Set supply at source to `max_flow_value` and demand at sink to `-max_flow_value` using `SetNodeSupply(node, supply)`.
- For each arc, call `AddArcWithCapacityAndUnitCost(from_node, to_node, capacity, unit_cost)`.
- Call `Solve()` to compute min-cost flow.

### Formulation Template
```json
{
  "sets": ["nodes (implicit via indices)", "arcs (list of tuples)"],
  "parameters": ["source_index", "sink_index", "capacity_per_arc", "unit_cost_per_arc"],
  "decision_variables": ["flow_on_arc (managed internally by solver)"],
  "objective": {
    "sense": "lexicographic",
    "stage1": "maximize total flow",
    "stage2": "minimize total cost given max flow"
  },
  "constraints": [
    "flow_conservation (enforced by solver)",
    "arc_capacity (enforced by solver)",
    "nonnegativity (enforced by solver)",
    "stage2_supply_demand: source supply == max_flow_value, sink demand == -max_flow_value"
  ]
}
```

### Common Pitfalls
- Using non-integer node indices or capacities, as OR-Tools solvers require integer inputs.
- Forgetting to set node supplies for all nodes (non-source/sink nodes must have supply 0).
- Mixing up the order of arguments in `AddArcWithCapacityAndUnitCost`.

## Solving stage

### Strategy Overview
Execute two sequential OR-Tools solver calls. First, use `SimpleMaxFlow` to get the maximum flow value. Then, use `SimpleMinCostFlow` with the source supply set to that value to find the minimum cost flow. Extract results using solver API methods.

### Step 1 - Solve Max Flow
- Create `SimpleMaxFlow` object and add all arcs with capacities.
- Call `Solve(source, sink)` and check return status is `SimpleMaxFlow.OPTIMAL`.
- Retrieve `max_flow_value = max_flow.OptimalFlow()`.

### Step 2 - Solve Min-Cost Flow
- Create `SimpleMinCostFlow` object.
- Set source supply to `max_flow_value` and sink supply to `-max_flow_value`.
- Set all other node supplies to 0.
- Add all arcs with capacities and unit costs.
- Call `Solve()` and check return status is `SimpleMinCostFlow.OPTIMAL`.
- Retrieve `min_cost_value = min_cost_flow.OptimalCost()`.

### Step 3 - Extract Arc Flows
- For each arc index `i`, call `min_cost_flow.Flow(i)` to get the flow on that arc.
- Verify that total flow into sink equals `max_flow_value`.
- Output results in a structured format.

### Code Usage
```python
from ortools.graph import pywrapgraph

# --- Stage 1: Max Flow ---
max_flow = pywrapgraph.SimpleMaxFlow()
for (start, end), cap in zip(arcs, capacities):
    max_flow.AddArcWithCapacity(start, end, int(cap))

status = max_flow.Solve(source, sink)
if status != max_flow.OPTIMAL:
    raise RuntimeError(f"Max flow failed with status {status}")

max_flow_value = max_flow.OptimalFlow()
print(f"Maximum flow: {max_flow_value}")

# --- Stage 2: Min-Cost Flow ---
min_cost_flow = pywrapgraph.SimpleMinCostFlow()
min_cost_flow.SetNodeSupply(source, int(max_flow_value))
min_cost_flow.SetNodeSupply(sink, -int(max_flow_value))
# Set all other node supplies to 0
for node in all_nodes:
    if node != source and node != sink:
        min_cost_flow.SetNodeSupply(node, 0)

for (start, end), cap, cost in zip(arcs, capacities, unit_costs):
    min_cost_flow.AddArcWithCapacityAndUnitCost(start, end, int(cap), int(cost))

status = min_cost_flow.Solve()
if status != min_cost_flow.OPTIMAL:
    raise RuntimeError(f"Min-cost flow failed with status {status}")

min_cost_value = min_cost_flow.OptimalCost()
print(f"Minimum cost: {min_cost_value}")

# Extract arc flows
flow_on_arcs = [min_cost_flow.Flow(i) for i in range(min_cost_flow.NumArcs())]
```

### Common Pitfalls
- Not converting float capacities/costs to integers, causing silent truncation or errors.
- Forgetting to set zero supply for intermediate nodes, leading to infeasibility.
- Assuming arc indices in `SimpleMinCostFlow` correspond to the order they were added (they do, but verify with `Tail(i)` and `Head(i)` if needed).
