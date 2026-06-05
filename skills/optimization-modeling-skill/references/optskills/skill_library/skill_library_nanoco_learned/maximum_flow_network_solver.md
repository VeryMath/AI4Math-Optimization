---
name: Maximum Flow Network Solver
description: |
  A skill for modeling and solving maximum flow problems on capacitated directed networks, providing workflows for specialized graph algorithms and general linear programming formulations.

---
# Workflow 1 (Specialized Graph Algorithm)

## Modeling stage

### Strategy Overview
Model the problem as a directed graph where arcs have capacities. Use a specialized max-flow algorithm (e.g., Edmonds-Karp, Push-Relabel) which implicitly handles variables and constraints, focusing on graph construction and source-sink definition.

### Step 1 - Define Network Topology
- Identify the set of nodes and the set of directed arcs.
- For each arc, define its tail (start node), head (end node), and capacity.

### Step 2 - Map Data to Solver Input
- Prepare three parallel lists: `start_nodes`, `end_nodes`, and `capacities`.
- Ensure node indices are unique consecutive integers, typically starting from 0.

### Step 3 - Configure Source and Sink
- Designate a single source node (where flow originates) and a single sink node (where flow terminates).

### Formulation Template
```json
{
  "sets": [
    "NODES",
    "ARCS"
  ],
  "parameters": [
    {"name": "capacity", "index": "ARCS"}
  ],
  "decision_variables": [],
  "objective": {
    "sense": "max",
    "expression": "total_flow_from_source_to_sink"
  },
  "constraints": [
    "capacity_constraint (implicit in algorithm)",
    "flow_conservation (implicit in algorithm)"
  ]
}
```

### Common Pitfalls
- Using non-integer or non-consecutive node identifiers, causing solver errors.
- Incorrectly ordering the `start_nodes` and `end_nodes` lists, reversing arc direction.
- Forgetting to verify the solver's status is `OPTIMAL` before extracting results.

## Solving stage

### Strategy Overview
Utilize a dedicated max-flow solver API. The solving process involves adding arcs, invoking the algorithm, and extracting the flow value and distribution.

### Step 1 - Initialize Solver
- Instantiate the specialized max-flow solver object (e.g., `SimpleMaxFlow`).

### Step 2 - Build the Graph
- Iterate through all arcs, adding each to the solver with its capacity using `add_arc_with_capacity`.

### Step 3 - Solve and Check Status
- Call the solver's `solve(source, sink)` method.
- Check the returned status equals `OPTIMAL`; handle `INFEASIBLE` or other statuses appropriately.

### Step 4 - Extract and Verify Solution
- Retrieve the optimal flow value via `optimal_flow()`.
- Optionally, iterate through arcs to get the flow on each arc for verification or reporting.

### Code Usage
```python
# build model from formulation
solver = max_flow.SimpleMaxFlow()
for i in range(num_arcs):
    solver.add_arc_with_capacity(start_nodes[i], end_nodes[i], capacities[i])

# solve with status / termination checks
status = solver.solve(source, sink)
if status == solver.OPTIMAL:
    max_flow_value = solver.optimal_flow()
    # Optional: Retrieve per-arc flows
    for i in range(solver.num_arcs()):
        flow = solver.flow(i)
else:
    # Handle failure
```

### Common Pitfalls
- Assuming the solver found a feasible solution without checking the status.
- Misinterpreting arc indices when retrieving per-arc flows after the solve.
- Not accounting for the possibility of multiple optimal flow distributions.

# Workflow 2 (Linear Programming Formulation)

## Modeling stage

### Strategy Overview
Formulate the maximum flow problem as a Linear Program (LP). Explicitly define continuous flow variables for each arc, subject to capacity bounds and flow conservation constraints at all nodes except the source and sink.

### Step 1 - Define Variables and Parameters
- Create one non-negative continuous variable for each directed arc, representing the flow on that arc. Set its upper bound equal to the arc's capacity.
- Use descriptive naming (e.g., `flow[(i,j)]`) for clarity and retrieval.

### Step 2 - Enforce Capacity Constraints
- For each arc, the flow variable is automatically bounded by `[0, capacity]` when created with these bounds.

### Step 3 - Enforce Flow Conservation
- For each node that is neither the source nor the sink, create a constraint: the sum of flows on incoming arcs equals the sum of flows on outgoing arcs.
- Programmatically build inflow and outflow lists by scanning all arcs.

### Step 4 - Formulate the Objective
- Define the objective to maximize the total flow into the sink node (sum of flows on all arcs terminating at the sink).

### Formulation Template
```json
{
  "sets": [
    "NODES",
    "ARCS"
  ],
  "parameters": [
    {"name": "capacity", "index": "ARCS"}
  ],
  "decision_variables": [
    {"name": "flow", "index": "ARCS", "type": "continuous", "lb": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(flow[(i, sink)] for all arcs (i, sink) into sink)"
  },
  "constraints": [
    "flow[a] <= capacity[a] for all a in ARCS (enforced by variable bounds)",
    "sum(flow[(i, n)]) == sum(flow[(n, j)]) for all n in NODES where n != source, sink"
  ]
}
```

### Common Pitfalls
- Incorrectly indexing nodes when constructing flow conservation constraints, leading to unbalanced equations.
- Adding unnecessary constraints for the source or sink nodes, which are handled implicitly by the objective.
- Formulating the objective on the wrong set of arcs (e.g., maximizing flow out of the sink).

## Solving stage

### Strategy Overview
Use a general-purpose LP solver. The process involves building the model with explicit variables and constraints, solving it, and then verifying the solution satisfies the network flow properties.

### Step 1 - Initialize Solver and Model
- Create a solver instance capable of handling linear programming (e.g., `GLOP`, `HiGHS`).

### Step 2 - Build the LP Model
- Create flow variables with bounds `(0, capacity)` in one pass, storing them in a dictionary keyed by arc.
- For each intermediate node, dynamically build inflow and outflow lists from the arc dictionary and add the conservation constraint.
- Set the objective to maximize the sum of flow variables on arcs ending at the sink.

### Step 3 - Solve and Check Termination
- Execute the solver.
- Verify the termination condition is `OPTIMAL`.

### Step 4 - Extract and Validate Solution
- Retrieve the objective value.
- Optionally, extract the flow values for each arc.
- Perform a post-solve validation: check that flow conservation holds at intermediate nodes and that no arc exceeds its capacity within a small tolerance (e.g., `1e-6`).

### Code Usage
```python
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
flow_vars = {}
for (i, j), cap in capacities.items():
    flow_vars[(i, j)] = solver.NumVar(0, cap, f'flow_{i}_{j}')

for node in intermediate_nodes:
    inflow = [flow_vars[(i, j)] for (i, j) in arcs if j == node]
    outflow = [flow_vars[(i, j)] for (i, j) in arcs if i == node]
    if inflow or outflow:
        solver.Add(sum(inflow) == sum(outflow))

sink_inflow = [flow_vars[(i, j)] for (i, j) in arcs if j == sink]
solver.Maximize(sum(sink_inflow))

status = solver.Solve()
if status == solver.OPTIMAL:
    max_flow_value = solver.Objective().Value()
    # Optional validation
    for (i, j), var in flow_vars.items():
        flow_val = var.solution_value()
        # Check capacity
        assert flow_val <= capacities[(i, j)] + 1e-6
else:
    # Handle failure
```

### Common Pitfalls
- Using an LP solver without enabling presolve or appropriate scaling for large networks.
- Not verifying that the extracted solution satisfies all constraints within a small tolerance due to numerical precision.
- Confusing the solver's status codes (e.g., `OPTIMAL` vs. `FEASIBLE`).

# Workflow 3 (Edmonds-Karp Algorithm Implementation)

## Modeling stage

### Strategy Overview
Recognize maximum flow problems by identifying source-sink networks with capacity constraints on arcs and flow conservation at intermediate nodes. The objective is to maximize total flow from source to sink. Map network elements to a graph structure: nodes as vertices and directed links as arcs with capacity parameters.

### Step 1 - Define Graph Representation
- Store the graph as adjacency lists of edge indices for efficient BFS traversal.
- For each directed edge, store its destination, capacity, and a pointer to its reverse edge in the residual graph.

### Step 2 - Implement Residual Network
- When adding an edge, simultaneously add a reverse edge with zero initial capacity to enable flow reduction.

## Solving stage

### Strategy Overview
Implement the Edmonds-Karp algorithm (BFS-based Ford-Fulkerson) for reliability when external libraries are unavailable. Structure the algorithm to find augmenting paths in the residual network and saturate them until no path exists.

### Step 1 - Initialize Algorithm Structures
- Create a `MaxFlow` class with methods for adding edges, BFS for finding augmenting paths, and the main Edmonds-Karp loop.
- Use efficient data structures: store edges in a flat list with indices, maintain adjacency lists for quick neighbor access, and use a parent array to reconstruct augmenting paths.

### Step 2 - Execute Edmonds-Karp Loop
- While BFS finds a path from source to sink in the residual graph:
    - Determine the bottleneck capacity along the path.
    - Augment flow along the path and its reverse edges.
- The loop terminates when BFS finds no augmenting path.

### Step 3 - Validate with LP Formulation
- Cross-check algorithm results using the LP formulation from Workflow 2 to ensure correctness.
- After solving, examine the graph structure to identify limiting arcs (e.g., minimum cut edges) and verify the solution makes intuitive sense.

### Step 4 - Handle Edge Cases
- Ensure the algorithm works for networks with multiple paths, cycles, and disconnected components by properly implementing BFS termination conditions.
- Analyze network bottlenecks by identifying the minimum cut after the algorithm completes.

### Code Usage
```python
class MaxFlow:
    def __init__(self, n):
        self.n = n
        self.adj = [[] for _ in range(n)]
        self.edges = []  # [to, cap, flow]

    def add_edge(self, u, v, cap):
        self.edges.append([v, cap, 0])
        self.adj[u].append(len(self.edges) - 1)
        self.edges.append([u, 0, 0])
        self.adj[v].append(len(self.edges) - 1)

    def bfs(self, s, t, parent):
        visited = [False] * self.n
        queue = [s]
        visited[s] = True
        while queue:
            u = queue.pop(0)
            for idx in self.adj[u]:
                v, cap, flow = self.edges[idx]
                if not visited[v] and cap - flow > 0:
                    visited[v] = True
                    parent[v] = (u, idx)
                    if v == t:
                        return True
                    queue.append(v)
        return False

    def edmonds_karp(self, s, t):
        max_flow = 0
        parent = [-1] * self.n
        while self.bfs(s, t, parent):
            path_flow = float('inf')
            v = t
            while v != s:
                u, idx = parent[v]
                path_flow = min(path_flow, self.edges[idx][1] - self.edges[idx][2])
                v = u
            v = t
            while v != s:
                u, idx = parent[v]
                self.edges[idx][2] += path_flow
                self.edges[idx ^ 1][2] -= path_flow
                v = u
            max_flow += path_flow
        return max_flow

# Usage
mf = MaxFlow(num_nodes)
for u, v, cap in arcs:
    mf.add_edge(u, v, cap)
max_flow_value = mf.edmonds_karp(source, sink)
