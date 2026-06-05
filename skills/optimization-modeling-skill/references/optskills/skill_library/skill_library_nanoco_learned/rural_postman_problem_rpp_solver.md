---
name: Rural Postman Problem (RPP) Solver
description: |
  Model and solve the Rural Postman Problem (RPP) to find a minimum-cost closed tour covering a set of required edges, using either a direct MIP formulation with connectivity cuts or a matching-based reduction to an Eulerian graph.

---
# Workflow 1 (Direct MIP with Cut-Set Constraints)

## Modeling stage

### Strategy Overview
Model the RPP as a Mixed-Integer Program (MIP) using integer edge traversal variables. Enforce mandatory edge coverage, Eulerian degree conditions, and connectivity via explicit cut-set constraints to guarantee a single closed tour.

### Step 1 - Define Core Variables and Objective
- Define non-negative integer variables `x[edge]` representing the number of times each undirected edge is traversed.
- Formulate the objective to minimize total traversal cost: `min sum(cost[edge] * x[edge] for edge in all_edges)`.

### Step 2 - Enforce Mandatory Edge Coverage
- For each edge in the required set `R`, add a constraint `x[edge] >= 1`.

### Step 3 - Impose Eulerian Degree Conditions
- For each node `i`, introduce an auxiliary non-negative integer variable `k[i]`.
- Add a constraint that the sum of `x` for all edges incident to node `i` equals `2 * k[i]`. This ensures even degree at each node, a necessary condition for an Eulerian circuit.

### Step 4 - Ensure Connectivity via Subtour Elimination
- To prevent disconnected cycles, add cut-set constraints for every proper subset `S` of nodes that does not contain the designated depot node.
- For each such subset `S`, add the constraint: `sum(x[edge] for edge in the cut(S)) >= 2`. This forces at least two connections between `S` and its complement, ensuring a single connected tour.
- **Prerequisite Check**: Before solving, verify the depot node is incident to at least one required edge or is connected to the required subgraph via the underlying network. If the depot is isolated, the problem may be infeasible or produce a disconnected solution.
- **Scalability Warning**: Pre-generating all cut-set constraints for large graphs (|NODES| > [SMALL_INSTANCE_THRESHOLD]) leads to an exponential number of constraints; use lazy constraint callbacks for scalability.

### Formulation Template
```json
{
  "sets": [
    "NODES",
    "EDGES (undirected pairs from NODES)",
    "REQUIRED_EDGES (subset of EDGES)"
  ],
  "parameters": [
    "cost[edge in EDGES] (non-negative)",
    "depot (node in NODES)"
  ],
  "decision_variables": [
    "x[edge in EDGES] (non-negative integer)",
    "k[node in NODES] (non-negative integer)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[edge] * x[edge] for edge in EDGES)"
  },
  "constraints": [
    "coverage[edge in REQUIRED_EDGES]: x[edge] >= 1",
    "even_degree[node in NODES]: sum(x[(i,j)] for (i,j) in EDGES if i==node or j==node) == 2 * k[node]",
    "connectivity[S in proper_subsets(NODES \\ {depot})]: sum(x[(i,j)] for (i,j) in EDGES if (i in S) != (j in S)) >= 2"
  ]
}
```

### Common Pitfalls
- Using binary variables (`x[edge] in {0,1}`) incorrectly limits the model to traversing each edge at most once, which may render the problem infeasible if required edges are not connected.
- Forgetting to exclude the depot from the subsets `S` in the cut-set constraints, which can lead to redundant or incorrect constraints.
- **Depot Isolation**: The standard cut-set constraints only ensure connectivity among non-depot nodes. A solution may satisfy all constraints yet leave the depot disconnected (degree 0). Always verify depot connectivity post-solution.
- **Suboptimality Risk**: For small instances where the required subgraph is connected, the direct MIP formulation may be computationally heavy and prone to finding suboptimal solutions. Consider using Workflow 2 (Matching-Based Reduction) in such cases.

## Solving stage

### Strategy Overview
Solve the MIP using a standard solver like SCIP or CBC. After obtaining a solution, verify its feasibility and construct the explicit Eulerian tour.

### Step 1 - Configure and Solve the MIP
- Instantiate the solver (e.g., `pywraplp.Solver.CreateSolver("SCIP")`).
- Build the model using the formulation, adding all pre-computed cut-set constraints for small instances.
- Set solver parameters such as time limit, relative MIP gap, and number of threads.
- Call `solver.Solve()` and check the status for optimality or feasibility.

### Step 2 - Verify Solution Correctness
- Extract the solution values for `x[edge]`.
- Programmatically verify all constraints: check `x[edge] >= 1` for required edges, verify even degree at each node, and confirm the graph defined by edges with `x[edge] > 0` is connected (e.g., using a BFS/DFS).
- **Critical Depot Check**: Explicitly verify the depot node has positive degree in the solution (`sum(x[edge] for edges incident to depot) > 0`). If depot degree is zero, the solution is invalid (disconnected depot). This check must be performed even if all other constraints are satisfied.
- Log any constraint violations for debugging.

### Step 3 - Construct the Eulerian Tour
- Build a multigraph representation where each edge `(i,j)` appears `x[edge].solution_value()` times.
- Apply Hierholzer's algorithm to find an Eulerian circuit starting and ending at the depot.
- Output the sequence of nodes representing the tour.

### Code Usage
```python
import math
from ortools.linear_solver import pywraplp

# 1. Initialize solver
solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise Exception('Solver not available.')

# 2. Define variables (example for a small graph)
x = {}
for i in NODES:
    for j in NODES:
        if i < j:
            x[(i, j)] = solver.IntVar(0, solver.infinity(), f'x_{i}_{j}')

# 3. Set objective
objective = solver.Objective()
for (i, j), var in x.items():
    objective.SetCoefficient(var, COST_MATRIX[i][j])
objective.SetMinimization()

# 4. Add mandatory coverage constraints
for (i, j) in REQUIRED_EDGES:
    solver.Add(x[(min(i, j), max(i, j))] >= 1)

# 5. Add even-degree constraints
k_vars = {}
for i in NODES:
    k_vars[i] = solver.IntVar(0, solver.infinity(), f'k_{i}')
    degree_expr = sum(x.get((min(i, adj), max(i, adj)), 0) for adj in NODES if adj != i)
    solver.Add(degree_expr == 2 * k_vars[i])

# 6. Add connectivity constraints (for small N, pre-generate all cuts)
# ... (implementation for generating proper subsets S)
# for S in all_proper_subsets:
#     cut_expr = 0
#     for (i, j) in x:
#         if (i in S) != (j in S):
#             cut_expr += x[(i, j)]
#     solver.Add(cut_expr >= 2)

# 7. Solve
status = solver.Solve()
if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Objective value = {objective.Value()}')
    # Extract solution and build tour
    solution_x = {edge: var.solution_value() for edge, var in x.items()}
    # --- Critical Depot Connectivity Check ---
    depot_degree = sum(solution_x.get((min(DEPOT, adj), max(DEPOT, adj)), 0) for adj in NODES if adj != DEPOT)
    if depot_degree == 0:
        raise Exception('Solution invalid: depot is disconnected (degree 0).')
    # ... verification and tour construction code
else:
    print('No solution found.')
```

### Common Pitfalls
- Not checking the solver status for `FEASIBLE` in addition to `OPTIMAL`, which may miss valid but suboptimal solutions.
- Attempting to generate all cut-set constraints for more than ~[SMALL_INSTANCE_THRESHOLD] nodes, causing memory issues; implement a callback or use an alternative formulation.
- Assuming the solver's solution is automatically connected; always run a connectivity check post-solve.
- **Missing Depot Verification**: Accepting a solution where the depot has degree 0 violates the closed tour requirement. Always explicitly check depot degree.
- **Suboptimality Risk**: The MIP solver may not find the global optimum for this problem structure. If the required subgraph is connected, consider verifying the solution cost against the matching-based reduction (Workflow 2) for optimality assurance.

# Workflow 2 (Matching-Based Reduction)

## Modeling stage

### Strategy Overview
Reduce the RPP to a Minimum-Weight Perfect Matching (MWPM) problem. First construct an Eulerian multigraph by adding shortest paths between odd-degree nodes in the required subgraph, then find an Eulerian circuit. The core MIP solves the matching problem.

### Step 1 - Analyze the Required Subgraph
- Construct a graph `G_R` containing only the required edges.
- Calculate the degree of each node within `G_R`.
- Identify the set `ODD_NODES` of nodes with odd degree in `G_R`. By the Handshaking Lemma, this set has even cardinality.
- **Depot Connectivity Pre-check**: If the depot is not incident to any required edge, it will have degree 0 in `G_R` (even) and will not be in `ODD_NODES`. The standard matching formulation will not connect the depot, potentially leading to a disconnected final tour. In such cases, either treat the depot as an odd node artificially (by adding a dummy required edge of zero cost to a neighbor) or use Workflow 1.

### Step 2 - Compute Shortest Path Distances
- Compute all-pairs shortest path distances `dist[i][j]` on the original complete graph (or the underlying network) using a suitable algorithm (e.g., Floyd-Warshall).
- **Symmetry Verification**: Ensure the distance matrix is symmetric (`dist[i][j] == dist[j][i]`). If input data is asymmetric, correct it (e.g., by taking the minimum or enforcing symmetry) to guarantee a valid matching cost matrix.

### Step 3 - Model Minimum-Weight Perfect Matching
- Define binary variables `z[i,j]` for each pair `(i,j)` in `ODD_NODES` where `i < j`, indicating that a shortest path between `i` and `j` is added to the tour.
- Add constraints so that each odd node is matched exactly once: for each node `i` in `ODD_NODES`, `sum(z[i,j] for j != i) == 1`.
- The objective is to minimize the total cost of added paths: `min sum(dist[i][j] * z[i,j] for i,j in ODD_NODES, i<j)`.

### Step 4 - Construct the Eulerian Multigraph
- The solution to the matching problem dictates which shortest paths to add.
- The final Eulerian multigraph is the union of: 1) all required edges (each taken once), and 2) each edge along the shortest paths corresponding to matched pairs (edges on these paths may be used multiple times, which is accounted for in the distance calculation).
- **Post-Matching Depot Check**: After building the multigraph, verify the depot node has positive degree. If not, the solution is invalid (depot isolated).

### Formulation Template
```json
{
  "sets": [
    "NODES",
    "REQUIRED_EDGES",
    "ODD_NODES (subset of NODES with odd degree in REQUIRED_EDGES graph)"
  ],
  "parameters": [
    "shortest_path_distance[i in NODES, j in NODES] (non-negative, symmetric)",
    "required_cost (sum of costs of all REQUIRED_EDGES)"
  ],
  "decision_variables": [
    "z[i in ODD_NODES, j in ODD_NODES, i < j] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "required_cost + sum(shortest_path_distance[i][j] * z[i,j] for i,j in ODD_NODES, i<j)"
  },
  "constraints": [
    "matching[node in ODD_NODES]: sum(z[min(node, other), max(node, other)] for other in ODD_NODES if other != node) == 1"
  ]
}
```

### Common Pitfalls
- Incorrectly identifying odd-degree nodes if the required subgraph is treated as directed.
- Using edge costs instead of shortest path distances for the matching cost matrix, which underestimates the true cost of connecting odd nodes.
- Forgetting to add the fixed cost of the required edges to the final objective value.
- **Isolated Depot**: The matching formulation only connects odd-degree nodes from the required subgraph. If the depot has even degree (including degree 0) in the required subgraph, it may remain disconnected. Always verify depot inclusion after constructing the multigraph.
- **Graph Connectivity Assumption**: The matching solution assumes the original graph is connected. If the required subgraph is disconnected, the matching may produce a disconnected multigraph. Always verify connectivity before constructing the Eulerian circuit.

## Solving stage

### Strategy Overview
Solve the MWPM MIP, then post-process to build the Eulerian multigraph and generate the final tour. This approach often requires solving a smaller, simpler MIP compared to the direct formulation.

### Step 1 - Solve the Matching Problem
- Instantiate a MIP solver.
- Model the perfect matching problem with binary variables `z` and the degree constraints.
- Solve to optimality; this problem is typically easier than the full RPP MIP.
- **Efficient Matching Solver**: For large sets of odd nodes (more than [SMALL_ODD_SET_THRESHOLD]), use a dedicated matching solver or heuristic rather than manually enumerating all perfect matchings.

### Step 2 - Build the Combined Multigraph
- Initialize a multigraph object (e.g., using `networkx.MultiGraph`).
- Add all required edges to the multigraph.
- For each matched pair `(i,j)` where `z[i,j] = 1`, retrieve the sequence of edges constituting the shortest path between `i` and `j` (precomputed during distance calculation).
- Add each edge along this path to the multigraph. This may increase the multiplicity of edges that appear in multiple paths.

### Step 3 - Verify Depot Connectivity and Graph Connectivity
- Check that the depot node has positive degree in the multigraph. If depot degree is zero, the solution is invalid. Fallback options: (1) switch to Workflow 1 (Direct MIP), or (2) artificially add the depot to the odd-node set and re-solve the matching problem with an additional constraint to connect the depot.
- Verify the multigraph is connected (e.g., using BFS/DFS). If disconnected, the matching solution is invalid; fall back to Workflow 1.

### Step 4 - Generate the Eulerian Circuit
- Verify that the multigraph is connected and all nodes have even degree.
- Use an algorithm like `networkx.eulerian_circuit` or implement Hierholzer's algorithm to find a closed Eulerian tour.
- The tour can start and end at any node, typically the depot is specified.

### Step 5 - Compute Total Tour Cost
- The total cost is the sum of: 1) the cost of all required edges, plus 2) the sum of distances of all added shortest paths (i.e., the matching objective value).

### Code Usage
```python
import networkx as nx
from ortools.linear_solver import pywraplp

# 1. Identify odd-degree nodes in the required subgraph G_R
G_R = nx.Graph()
G_R.add_edges_from(REQUIRED_EDGES)
odd_nodes = [node for node, deg in G_R.degree() if deg % 2 == 1]

# 2. Compute all-pairs shortest path distances (precomputed)
# dist_matrix[i][j] holds shortest path distance (ensure symmetry)

# 3. Solve Minimum-Weight Perfect Matching
solver = pywraplp.Solver.CreateSolver('CBC')
z = {}
# Create binary variables
for idx_i, i in enumerate(odd_nodes):
    for j in odd_nodes[idx_i+1:]:
        z[(i, j)] = solver.BoolVar(f'z_{i}_{j}')

# Objective: minimize matching cost
objective = solver.Objective()
for (i, j), var in z.items():
    objective.SetCoefficient(var, dist_matrix[i][j])
objective.SetMinimization()

# Constraints: each odd node matched exactly once
for node in odd_nodes:
    constraint_expr = 0
    for (i, j), var in z.items():
        if i == node or j == node:
            constraint_expr += var
    solver.Add(constraint_expr == 1)

status = solver.Solve()

# 4. Post-process if solution found
if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Build multigraph
    multigraph = nx.MultiGraph()
    multigraph.add_edges_from(REQUIRED_EDGES)
    for (i, j), var in z.items():
        if var.solution_value() > 0.5:
            # Retrieve shortest path edges (precomputed)
            path_edges = get_shortest_path_edges(i, j)
            multigraph.add_edges_from(path_edges)
    # --- Critical Depot Connectivity Check ---
    if DEPOT not in multigraph or multigraph.degree(DEPOT) == 0:
        raise Exception('Solution invalid: depot is disconnected. Consider using Direct MIP workflow.')
    # --- Graph Connectivity Check ---
    if not nx.is_connected(multigraph.to_undirected()):
        raise Exception('Multigraph is disconnected. Matching solution invalid.')
    # Generate Eulerian circuit
    if nx.is_eulerian(multigraph):
        tour = list(nx.eulerian_circuit(multigraph, source=DEPOT))
        total_cost = sum(COST_MATRIX[i][j] for i, j in multigraph.edges())
        print(f'Tour: {tour}')
        print(f'Total cost: {total_cost}')
