---
name: Maximum Cardinality Bipartite Matching
description: |
  Model and solve one-to-one assignment problems between two disjoint sets with preference compatibility, aiming to maximize the total number of matches.
---

# Workflow 1 (Network Flow via Max-Flow)

## Modeling stage

### Strategy Overview
Transform the bipartite matching problem into a maximum flow problem on a directed network. The flow value directly represents the number of matches, and unit capacities enforce one-to-one constraints.

### Step 1 - Identify Sets and Compatibility
- Define two disjoint sets: `LEFT_SET` (size `m`) and `RIGHT_SET` (size `n`).
- Define a binary compatibility parameter `ALLOWED_PAIRS` as a list of tuples `(i, j)` where `i ∈ LEFT_SET` and `j ∈ RIGHT_SET`. Use zero-based indices consistent with the problem description.
- Elements with no feasible edges are automatically excluded from the matching.

### Step 2 - Construct Flow Network
- Create a source node (index `0`) and a sink node (index `m + n + 1`).
- Add arcs from source to each left node `i` (index `1 + i`) with capacity `1`.
- For each allowed pair `(i, j)`, add an arc from left node `i` to right node `j` (index `1 + m + j`) with capacity `1`.
- Add arcs from each right node `j` to the sink with capacity `1`.

### Step 3 - Define Objective Implicitly
- The objective to maximize the number of matches is equivalent to maximizing the total flow from source to sink. No explicit objective function is needed in the flow model.

### Formulation Template
```json
{
  "sets": ["LEFT_SET", "RIGHT_SET"],
  "parameters": ["ALLOWED_PAIRS"],
  "decision_variables": ["flow_arcs (implicit via solver)"],
  "objective": {
    "sense": "max",
    "expression": "maximize total flow from source to sink"
  },
  "constraints": [
    "source → LEFT_SET arcs: capacity = 1",
    "LEFT_SET → RIGHT_SET arcs: capacity = 1 for ALLOWED_PAIRS",
    "RIGHT_SET → sink arcs: capacity = 1",
    "flow conservation at all nodes except source and sink"
  ]
}
```

### Common Pitfalls
- Incorrect node indexing leading to arc misplacement. Use a systematic offset scheme (e.g., source=0, left nodes=1..m, right nodes=m+1..m+n, sink=m+n+1).
- Adding arcs for non-allowed pairs, which incorrectly expands the feasible region.
- Forgetting to set arc capacities to 1, which violates the one-to-one matching constraint.

## Solving stage

### Strategy Overview
Use a dedicated max-flow algorithm (e.g., OR-Tools SimpleMaxFlow) to find the maximum flow, then extract assignments by identifying arcs with positive flow between the two sets.

### Step 1 - Initialize Max-Flow Solver
- Instantiate the max-flow solver (e.g., `SimpleMaxFlow()`).
- Define node indices according to the predetermined offset scheme.

### Step 2 - Build Network Programmatically
- Add source-to-left arcs with `add_arc_with_capacity(source, left_node, 1)`.
- Add left-to-right arcs for each `(i, j)` in `ALLOWED_PAIRS`.
- Add right-to-sink arcs with `add_arc_with_capacity(right_node, sink, 1)`.

### Step 3 - Solve and Check Status
- Call the solver's `solve(source, sink)` method.
- Verify the status is `OPTIMAL` before proceeding. If not `OPTIMAL`, return `None` and an empty list.

### Step 4 - Extract and Map Assignments
- Iterate over all arcs.
- Filter arcs where `flow(arc) > 0` and the tail is a left node and the head is a right node (excluding the sink).
- Map the internal node indices back to the original set indices using the offset scheme.

### Step 5 - Validate Solution Correctness
- Verify all assignments are in `ALLOWED_PAIRS`.
- Confirm each left node appears at most once and each right node appears at most once.
- The maximum number of matches is bounded by `min(m, n)`; achieving full utilization of the smaller set indicates optimality.

### Reusable Code Template
```python
from ortools.graph.python import max_flow

def max_bipartite_matching(left_size, right_size, allowed_pairs):
    smf = max_flow.SimpleMaxFlow()
    source = 0
    sink = left_size + right_size + 1
    left_offset = 1
    right_offset = left_size + 1

    # source to left nodes
    for i in range(left_size):
        smf.add_arc_with_capacity(source, left_offset + i, 1)

    # left to right (allowed pairs)
    for i, j in allowed_pairs:
        smf.add_arc_with_capacity(left_offset + i, right_offset + j, 1)

    # right nodes to sink
    for j in range(right_size):
        smf.add_arc_with_capacity(right_offset + j, sink, 1)

    status = smf.solve(source, sink)
    if status != smf.OPTIMAL:
        return None, []

    max_matches = smf.optimal_flow()
    assignments = []
    for arc in range(smf.num_arcs()):
        if smf.flow(arc) > 0:
            tail = smf.tail(arc)
            head = smf.head(arc)
            if left_offset <= tail < right_offset and head >= right_offset and head != sink:
                i = tail - left_offset
                j = head - right_offset
                assignments.append((i, j))
    return max_matches, assignments
```

### Common Pitfalls
- Not checking solver status, leading to extraction errors on infeasible or non-optimal solves.
- Misinterpreting arc indices when extracting matches; always verify tail/head belong to the correct node partitions.
- Assuming a perfect matching is always possible; the optimal flow may be less than `min(left_size, right_size)`.

# Workflow 2 (Binary Integer Programming via CP-SAT/MILP)

## Modeling stage

### Strategy Overview
Formulate the problem as a Binary Integer Program (BIP) with explicit binary assignment variables, linear constraints for one-to-one matching and preference compatibility, and a linear objective to maximize the sum of assignments.

### Step 1 - Define Sets and Parameters
- Define sets `SET_A` (size `m`) and `SET_B` (size `n`).
- Define a binary parameter `COMPATIBLE[i][j]` (1 if assignment is allowed, 0 otherwise).

### Step 2 - Create Binary Assignment Variables
- Create a binary decision variable `x[i][j]` for each `i ∈ SET_A`, `j ∈ SET_B` where `COMPATIBLE[i][j] == 1`.
- The variable equals 1 if element `i` is matched to element `j`.
- For sparse compatibility, only create variables for allowed pairs to avoid model bloat.

### Step 3 - Add One-to-One Matching Constraints
- For each `i ∈ SET_A`: `sum(x[i][j] for j in SET_B) <= 1`.
- For each `j ∈ SET_B`: `sum(x[i][j] for i ∈ SET_A) <= 1`.

### Step 4 - Enforce Preference Compatibility
- For each pair `(i, j)` where `COMPATIBLE[i][j] == 0`, either omit the variable or fix `x[i][j] = 0`.
- If variables are created for all pairs, add constraints: `x[i][j] <= COMPATIBLE[i][j]`.

### Step 5 - Set Maximization Objective
- Define objective: `maximize sum(x[i][j] for i ∈ SET_A for j ∈ SET_B)`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["COMPATIBLE (binary matrix)"],
  "decision_variables": ["x[i][j] ∈ {0,1}"],
  "objective": {
    "sense": "max",
    "expression": "sum_{i ∈ SET_A, j ∈ SET_B} x[i][j]"
  },
  "constraints": [
    "sum_{j ∈ SET_B} x[i][j] <= 1, ∀ i ∈ SET_A",
    "sum_{i ∈ SET_A} x[i][j] <= 1, ∀ j ∈ SET_B",
    "x[i][j] <= COMPATIBLE[i][j], ∀ i ∈ SET_A, j ∈ SET_B"
  ]
}
```

### Common Pitfalls
- Creating variables for all possible pairs when compatibility is sparse, leading to unnecessary model bloat.
- Using equality (`=`) instead of inequality (`<=`) in one-to-one constraints, which forces perfect matching and may cause infeasibility.
- Forgetting to enforce compatibility constraints, allowing invalid assignments.

## Solving stage

### Strategy Overview
Use a BIP-capable solver (e.g., OR-Tools CP-SAT or a MILP solver) to find an optimal assignment. Configure for exact solution and extract results by checking variable values.

### Step 1 - Instantiate Solver and Model
- Create a model instance (e.g., `CpModel()` or `ConcreteModel()`).
- Define sets and parameters within the modeling framework.

### Step 2 - Add Variables and Constraints
- Create binary variables only for allowed pairs.
- Add the one-to-one and compatibility constraints using the model's API.

### Step 3 - Set Objective and Configure Solver
- Set the maximization objective.
- Configure solver parameters: set a time limit `[TIME_LIMIT]`, enable parallel search, set optimality gap to zero, and optionally set a random seed for reproducibility.

### Step 4 - Solve and Validate Status
- Call the solver.
- Check termination status (`OPTIMAL` or `FEASIBLE` for CP-SAT; `ok` and `optimal`/`feasible` for Pyomo).

### Step 5 - Extract Solution
- Iterate over all `(i, j)` pairs for which a variable was created.
- If the variable value is 1 (or > 0.5 for continuous solvers), record `(i, j)` as an assignment.

### Code Usage
```python
# Example using OR-Tools CP-SAT
from ortools.sat.python import cp_model

def solve_bipartite_matching_cp_sat(m, n, compatible):
    model = cp_model.CpModel()
    x = {}
    for i in range(m):
        for j in range(n):
            if compatible[i][j]:
                x[(i, j)] = model.NewBoolVar(f"x_{i}_{j}")

    # One-to-one constraints
    for i in range(m):
        model.Add(sum(x.get((i, j), 0) for j in range(n)) <= 1)
    for j in range(n):
        model.Add(sum(x.get((i, j), 0) for i in range(m)) <= 1)

    # Objective
    model.Maximize(sum(x.values()))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30.0
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignments = [(i, j) for (i, j), var in x.items() if solver.Value(var) == 1]
        objective_value = solver.ObjectiveValue()
        return objective_value, assignments
    else:
        return None, []
```

### Common Pitfalls
- Not handling sparse variable creation correctly, leading to KeyError during constraint building.
- Misinterpreting solver status codes between different solver APIs.
- Extracting assignments without verifying the solution status first, potentially reading invalid values.
