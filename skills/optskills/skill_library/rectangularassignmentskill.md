---
name: RectangularAssignmentSkill
description: |
  Solves unbalanced assignment problems where one set must be fully matched to a subset of another set, minimizing total cost via binary linear programming or network flow.
---

# Workflow 1 (MIP Solver with Explicit Formulation)

## Modeling stage

### Strategy Overview
Model the problem as a Binary Integer Program (BIP) using explicit sets, binary decision variables for each potential assignment, and linear constraints enforcing one-to-one and cardinality rules.

### Step 1 - Problem Recognition and Set Definition
- Identify the two disjoint sets: Set A (elements requiring full assignment) and Set B (elements with limited capacity).
- Define the dimensions: `m = |A|`, `n = |B|`, with `m <= n` for a feasible matching.
- Prepare the `m x n` cost matrix `c[i][j]` for assigning element `i` in A to element `j` in B.

### Step 2 - Variable and Constraint Formulation
- Create binary decision variable `x[i][j]` for each `(i, j)` pair.
- Add constraint: `sum_{j in B} x[i][j] == 1` for each `i in A`. This ensures each element in A is assigned exactly once.
- Add constraint: `sum_{i in A} x[i][j] <= 1` for each `j in B`. This ensures each element in B is assigned at most once.
- Define the objective: Minimize `sum_{i in A} sum_{j in B} c[i][j] * x[i][j]`.

### Formulation Template
```json
{
  "sets": ["A", "B"],
  "parameters": ["c[i][j]"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A} sum_{j in B} c[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{j in B} x[i][j] == 1, for all i in A",
    "sum_{i in A} x[i][j] <= 1, for all j in B"
  ]
}
```

### Common Pitfalls
- Assuming square cost matrices; always check dimensions `m` and `n`.
- Forgetting to enforce `x[i][j]` as binary, which is essential for a matching.
- Misindexing the cost matrix when sets are defined as lists or ranges.

## Solving stage

### Strategy Overview
Solve the formulated BIP using a Mixed-Integer Programming (MIP) solver via a modeling library (e.g., OR-Tools, Pyomo). The focus is on a direct, declarative approach that separates model building from solver execution.

### Step 1 - Solver and Model Setup
- Instantiate a solver object capable of handling binary variables (e.g., SCIP, CBC, HiGHS).
- Create the model container and define the index sets `A` and `B` as Python ranges or lists.
- Add binary variables `x[i][j]` to the model for all `(i, j)` pairs.

### Step 2 - Constraint and Objective Implementation
- Use loops to add the `sum == 1` constraints for each `i` in A.
- Use loops to add the `sum <= 1` constraints for each `j` in B.
- Build the linear objective expression using the cost matrix and the variables.

### Step 3 - Solve and Solution Extraction
- Invoke the solver with appropriate parameters (e.g., time limit, optimality gap).
- Check the solver status for `OPTIMAL` or `FEASIBLE`.
- Extract the solution by iterating over variables `x[i][j]` and collecting pairs where the solution value is > 0.5.
- Compute the achieved total cost from the objective value or by summing costs of assigned pairs.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')
x = {}
for i in range(m):
    for j in range(n):
        x[i, j] = solver.BoolVar(f'x[{i},{j}]')

# Constraints: Each i assigned exactly once
for i in range(m):
    solver.Add(sum(x[i, j] for j in range(n)) == 1)
# Constraints: Each j assigned at most once
for j in range(n):
    solver.Add(sum(x[i, j] for i in range(m)) <= 1)

# Objective
objective = solver.Sum(c[i][j] * x[i, j] for i in range(m) for j in range(n))
solver.Minimize(objective)

# solve with status / termination checks
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    assignments = [(i, j) for i in range(m) for j in range(n) if x[i, j].solution_value() > 0.5]
    total_cost = solver.Objective().Value()
```

### Common Pitfalls
- Not verifying the solver status before extracting the solution, leading to errors.
- Using a loose optimality gap when an exact solution is required.
- Inefficiently building large models in loops; consider vectorized construction if supported.

# Workflow 2 (Network Flow Solver)

## Modeling stage

### Strategy Overview
Reformulate the assignment problem as a minimum-cost flow problem on a bipartite network. This leverages efficient network simplex algorithms and provides a natural representation of the matching constraints through flow conservation and arc capacities.

### Step 1 - Network Structure Definition
- Define nodes: a source node is not strictly needed. Have supply nodes for set A (supply = 1), transshipment nodes for set B (supply = 0), and a sink node (supply = -|A|).
- Define arcs: from each node `i` in A to each node `j` in B, with capacity 1 and unit cost `c[i][j]`.
- Define arcs: from each node `j` in B to the sink node, with capacity 1 and zero cost.

### Step 2 - Flow Formulation
- The flow on arc `(i, j)` represents the assignment variable `x[i][j]`.
- Flow conservation at node `i` in A ensures its unit supply is sent out.
- Flow conservation at node `j` in B ensures at most one unit can pass through to the sink, enforcing the `<= 1` constraint.
- The objective is to minimize the total cost of flow on arcs from A to B.

### Formulation Template
```json
{
  "sets": ["A_nodes", "B_nodes"],
  "parameters": ["c[i][j]", "supply[A_i] = 1", "supply[B_j] = 0", "supply[sink] = -|A|"],
  "decision_variables": ["flow[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in A} sum_{j in B} c[i][j] * flow[i][j]"
  },
  "constraints": [
    "Flow conservation at each node.",
    "Capacity on each arc from A to B: flow[i][j] <= 1",
    "Capacity on each arc from B to sink: flow[j][sink] <= 1"
  ]
}
```

### Common Pitfalls
- Incorrectly setting node supplies, leading to infeasibility.
- Forgetting to add arcs from B nodes to the sink, which are necessary to absorb the flow.
- Misinterpreting the solver's flow output, which may be fractional if not using an integer flow solver.

## Solving stage

### Strategy Overview
Use a dedicated minimum-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) to find the optimal integral flow. This approach is often faster for pure network problems and requires less modeling overhead.

### Step 1 - Graph Construction
- Instantiate a min-cost flow object.
- Add nodes for each element in A, each element in B, and one sink node. Set their supplies accordingly.
- For each `(i, j)` pair, add an arc from node `i` (A) to node `j` (B) with capacity 1 and cost `c[i][j]`.
- For each node `j` in B, add an arc from `j` to the sink node with capacity 1 and cost 0.

### Step 2 - Solve and Flow Interpretation
- Call the solver's `Solve()` method.
- Check the return status (e.g., `OPTIMAL`).
- Iterate over all arcs, specifically those from A to B. Arcs with a flow value > 0.5 indicate an assignment.
- The total cost is provided by the solver.

### Step 3 - Validation and Output
- Verify that the number of assignments equals `|A|`.
- Optionally, verify that no node in B receives more than one unit of flow.
- Output the list of assignments and the total cost.

### Code Usage
```python
# build model from formulation
from ortools.graph import pywrapgraph
min_cost_flow = pywrapgraph.SimpleMinCostFlow()

# Add nodes and set supplies
for i in range(m): # A nodes
    min_cost_flow.AddNodeWithSupply(i, 1)
for j in range(n): # B nodes
    min_cost_flow.AddNodeWithSupply(m + j, 0)
sink_id = m + n
min_cost_flow.AddNodeWithSupply(sink_id, -m)

# Add arcs from A to B
for i in range(m):
    for j in range(n):
        min_cost_flow.AddArcWithCapacityAndUnitCost(i, m + j, 1, c[i][j])
# Add arcs from B to sink
for j in range(n):
    min_cost_flow.AddArcWithCapacityAndUnitCost(m + j, sink_id, 1, 0)

# solve with status / termination checks
if min_cost_flow.Solve() == min_cost_flow.OPTIMAL:
    total_cost = min_cost_flow.OptimalCost()
    assignments = []
    for arc in range(min_cost_flow.NumArcs()):
        if min_cost_flow.Tail(arc) < m and min_cost_flow.Head(arc) < (m + n):
            if min_cost_flow.Flow(arc) > 0:
                i = min_cost_flow.Tail(arc)
                j = min_cost_flow.Head(arc) - m
                assignments.append((i, j))
```

### Common Pitfalls
- Assuming the solver returns integer flows; while `SimpleMinCostFlow` does for this structure, always check.
- Not mapping arc indices back to the original `(i, j)` indices correctly when extracting the solution.
- Ignoring the solver status, which could be `INFEASIBLE` or `UNBALANCED`.
