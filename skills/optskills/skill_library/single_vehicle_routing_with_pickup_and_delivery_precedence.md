---
name: Single Vehicle Routing with Pickup and Delivery Precedence
description: |
  Model and solve a single-vehicle routing problem that must start and end at a depot, visit all nodes exactly once, and respect precedence constraints for pickup-delivery pairs, minimizing total travel distance.
---

# Workflow 1 (OR-Tools Routing Model)

## Modeling stage

### Strategy Overview
Use OR-Tools' `RoutingModel` to formulate the problem as a Vehicle Routing Problem (VRP) with a single vehicle. The solver natively handles tour constraints and provides built-in support for pickup-delivery precedence through cumulative dimension variables.

### Step 1 - Define Distance Matrix and Problem Parameters
- Create a 2D list `dist_matrix` where `dist_matrix[i][j]` is the travel cost from node `i` to node `j`. Ensure the matrix is symmetric if distances are undirected.
- Set `num_nodes` to the total number of locations including the depot (index 0).
- Set `num_vehicles = 1` and `depot_index = 0`.

### Step 2 - Initialize Routing Index Manager and Model
- Instantiate `RoutingIndexManager(num_nodes, num_vehicles, depot_index)` to map between internal indices and original node IDs.
- Create `RoutingModel(manager)` to build the routing model.

### Step 3 - Register Transit Callback and Set Arc Cost
- Define a distance callback function that returns `dist_matrix[from_node][to_node]` using `manager.IndexToNode(index)`.
- Register the callback with `routing.RegisterTransitCallback(distance_callback)`.
- Set it as the arc cost evaluator: `routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_id)`.

### Step 4 - Add Distance Dimension for Precedence Enforcement
- Add a distance dimension: `routing.AddDimension(transit_callback_id, 0, max_distance, True, "Distance")` where `max_distance` is a sufficiently large upper bound (e.g., sum of all distances).
- This dimension tracks cumulative travel distance along the route, enabling precedence constraints via cumulative variables.

### Step 5 - Enforce Pickup-Delivery Precedence Constraints
- For each pickup-delivery pair `(pickup_node, delivery_node)`:
  - Get indices: `pickup_index = manager.NodeToIndex(pickup_node)`, `delivery_index = manager.NodeToIndex(delivery_node)`.
  - Ensure same vehicle: `routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))`.
  - Enforce precedence: `routing.solver().Add(distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index))`.

### Step 6 - Configure Search Parameters
- Set first solution strategy: `search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC`.
- Set local search metaheuristic: `search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH`.
- Set time limit: `search_params.time_limit.seconds = [TIME_LIMIT]`.
- Set solution limit: `search_params.solution_limit = [SOLUTION_LIMIT]`.

### Formulation Template
```json
{
  "sets": ["N: set of nodes (0 = depot, 1..n-1 = locations)", "P: set of pickup-delivery pairs (p, d)"],
  "parameters": ["dist_matrix[i][j]: travel distance from node i to node j", "max_distance: upper bound for cumulative distance"],
  "decision_variables": ["vehicle_route: sequence of nodes visited by the single vehicle"],
  "objective": {
    "sense": "min",
    "expression": "sum of dist_matrix[route[i]][route[i+1]] for all consecutive nodes in route"
  },
  "constraints": [
    "tour: route starts and ends at depot",
    "visit_all_nodes_exactly_once: each node appears exactly once in route",
    "precedence_pickup_before_delivery: for each (p, d) in P, pickup node appears before delivery node in route"
  ]
}
```

### Common Pitfalls
- Forgetting to convert between manager indices and node IDs when defining the distance callback, causing incorrect cost evaluation.
- Setting `max_distance` too small in `AddDimension`, which may incorrectly prune feasible solutions.
- Omitting the same-vehicle constraint for pickup-delivery pairs when using multiple vehicles (not needed for single vehicle but good practice for extensibility).

## Solving stage

### Strategy Overview
Solve the routing model with configured parameters, extract the optimal route, validate constraints manually, and output results in a structured JSON format for downstream consumption.

### Step 1 - Solve the Model
- Call `solution = routing.SolveWithParameters(search_params)`.
- Check if `solution` is `None`; if so, print failure JSON: `{"status": "failed", "solver_status": routing.status()}`.

### Step 2 - Extract the Route
- Start at `index = routing.Start(0)`.
- While not `routing.IsEnd(index)`:
  - Append `manager.IndexToNode(index)` to route list.
  - Set `index = solution.Value(routing.NextVar(index))`.
- Append `manager.IndexToNode(index)` to include the return to depot.

### Step 3 - Compute Total Distance
- Use `solution.ObjectiveValue()` for the solver-computed total distance.
- Optionally compute manually by summing distances between consecutive nodes in the extracted route to verify.

### Step 4 - Validate Solution Correctness
- Verify route starts and ends at depot (node 0).
- Check that all nodes appear exactly once (set equality).
- For each pickup-delivery pair, confirm pickup index < delivery index in the route list.
- Manually compute total distance: `sum(dist_matrix[route[i]][route[i+1]] for i in range(len(route)-1))` and compare to solver's objective.

### Step 5 - Output Structured JSON
- Build payload with keys: `"status"`, `"objective"`, `"route"`, `"total_distance_computed"`, `"solver_status"`.
- Print using `print(f"RESULT_JSON:{json.dumps(payload)}")`.

### Code Usage
```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp
import json

def solve_vrp_pd(dist_matrix, pickup_delivery_pairs, depot=0, time_limit=30, solution_limit=100):
    num_nodes = len(dist_matrix)
    manager = pywrapcp.RoutingIndexManager(num_nodes, 1, depot)
    routing = pywrapcp.RoutingModel(manager)

    def distance_callback(from_index, to_index):
        from_node = manager.IndexToNode(from_index)
        to_node = manager.IndexToNode(to_index)
        return dist_matrix[from_node][to_node]

    transit_callback_id = routing.RegisterTransitCallback(distance_callback)
    routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_id)

    max_distance = sum(sum(row) for row in dist_matrix)  # safe upper bound
    routing.AddDimension(transit_callback_id, 0, max_distance, True, "Distance")
    distance_dimension = routing.GetDimensionOrDie("Distance")

    for pickup, delivery in pickup_delivery_pairs:
        pickup_index = manager.NodeToIndex(pickup)
        delivery_index = manager.NodeToIndex(delivery)
        routing.solver().Add(routing.VehicleVar(pickup_index) == routing.VehicleVar(delivery_index))
        routing.solver().Add(distance_dimension.CumulVar(pickup_index) <= distance_dimension.CumulVar(delivery_index))

    search_params = pywrapcp.DefaultRoutingSearchParameters()
    search_params.first_solution_strategy = routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC
    search_params.local_search_metaheuristic = routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH
    search_params.time_limit.seconds = time_limit
    search_params.solution_limit = solution_limit

    solution = routing.SolveWithParameters(search_params)
    if not solution:
        print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'solver_status': routing.status()})}")
        return

    route = []
    index = routing.Start(0)
    while not routing.IsEnd(index):
        route.append(manager.IndexToNode(index))
        index = solution.Value(routing.NextVar(index))
    route.append(manager.IndexToNode(index))

    total_distance = solution.ObjectiveValue()
    payload = {
        "status": "success",
        "objective": total_distance,
        "route": route,
        "total_distance_computed": total_distance,
        "solver_status": routing.status()
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not checking for `None` solution before extraction, causing runtime errors.
- Extracting the route incorrectly by missing the final return to depot edge.
- Assuming solver status alone indicates feasibility; always validate constraints manually after extraction.

# Workflow 2 (CP-SAT Circuit Model)

## Modeling stage

### Strategy Overview
Use OR-Tools CP-SAT solver with the `AddCircuit` constraint to enforce a single Hamiltonian cycle. Introduce integer position variables to model precedence constraints, avoiding complex subtour elimination formulations.

### Step 1 - Define Sets and Parameters
- Let `N = {0, 1, ..., n-1}` where node 0 is the depot.
- Define `dist_matrix[i][j]` for all `i, j in N, i != j`.
- Define `pickup_delivery_pairs` as list of tuples `(pickup, delivery)`.

### Step 2 - Create Binary Arc Variables
- For each ordered pair `(i, j)` with `i != j`, create `x[i][j] = model.NewBoolVar(f'x_{i}_{j}')`.
- These variables indicate whether the tour directly travels from node `i` to node `j`.

### Step 3 - Enforce Hamiltonian Cycle with AddCircuit
- Build a list of arcs: for each `i != j`, append `(i, j, x[i][j])` to the arcs list.
- Add `model.AddCircuit(arcs)` to enforce a single tour visiting all nodes exactly once.

### Step 4 - Create Position Variables for Precedence
- For each node `i`, create `u[i] = model.NewIntVar(0, n-1, f'u_{i}')` representing the visit order.
- Add `model.Add(u[0] == 0)` to fix depot as first node.
- Add `model.AddAllDifferent(u)` to ensure unique positions.

### Step 5 - Link Arc Variables to Position Variables
- For each arc `(i, j)` where `j != 0` (non-depot destination): `model.Add(u[j] == u[i] + 1).OnlyEnforceIf(x[i][j])`.
- For arcs returning to depot `(i, 0)`: `model.Add(u[i] == n - 1).OnlyEnforceIf(x[i][0])`.
- For arcs leaving depot `(0, j)`: `model.Add(u[j] == 1).OnlyEnforceIf(x[0][j])`.

### Step 6 - Add Precedence Constraints
- For each pickup-delivery pair `(p, d)`, add `model.Add(u[p] < u[d])`.

### Step 7 - Define Objective
- Minimize total travel distance: `model.Minimize(sum(dist_matrix[i][j] * x[i][j] for i in N for j in N if i != j))`.

### Formulation Template
```json
{
  "sets": ["N: set of nodes (0 = depot, 1..n-1 = locations)", "A: set of ordered pairs (i, j) for i != j"],
  "parameters": ["dist_matrix[i][j]: travel distance from node i to node j"],
  "decision_variables": [
    "x[i][j]: binary, 1 if tour travels directly from i to j",
    "u[i]: integer, position of node i in the tour (0-indexed)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,j in A} dist_matrix[i][j] * x[i][j]"
  },
  "constraints": [
    "model.AddCircuit(arcs): enforces single Hamiltonian cycle",
    "u[0] == 0: depot is first",
    "model.AddAllDifferent(u): unique positions",
    "u[j] == u[i] + 1 .OnlyEnforceIf(x[i][j]) for j != 0: arc-position consistency",
    "u[i] == n - 1 .OnlyEnforceIf(x[i][0]): return to depot is last",
    "u[j] == 1 .OnlyEnforceIf(x[0][j]): first move from depot",
    "u[p] < u[d] for each pickup-delivery pair (p, d): precedence"
  ]
}
```

### Common Pitfalls
- Forgetting to include arcs for all ordered pairs in `AddCircuit`, causing infeasibility.
- Adding position constraints for depot arcs incorrectly (e.g., using `u[j] == u[i] + 1` for arcs returning to depot), which over-constrains the model.
- Not using `OnlyEnforceIf` correctly, leading to constraints that apply even when the arc is not selected.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with appropriate parameters for optimality, extract the tour from solved arc variables, validate all constraints, and output structured results.

### Step 1 - Configure and Run Solver
- Create `solver = cp_model.CpSolver()`.
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = [NUM_WORKERS]`, `solver.parameters.random_seed = [SEED]`, `solver.parameters.relative_gap_limit = 0.0`.
- Call `status = solver.Solve(model)`.

### Step 2 - Check Solver Status
- If `status` is not `cp_model.OPTIMAL` or `cp_model.FEASIBLE`, output failure JSON: `{"status": "failed", "reason": "no_feasible_solution", "solver_status": int(status)}`.

### Step 3 - Extract the Tour
- Start at `current = 0`.
- Initialize `route = [0]`.
- For `step` in range `n-1`:
  - Find `next_node` where `solver.Value(x[current][next_node]) == 1` and `next_node != 0`.
  - Append `next_node` to route, set `current = next_node`.
- Append `0` to close the tour.

### Step 4 - Validate Solution
- Verify route length equals `n + 1` (includes return to depot).
- Check all nodes appear exactly once (excluding final depot).
- For each pickup-delivery pair, find indices in route and confirm pickup index < delivery index.

### Step 5 - Output Structured JSON
- Build payload with keys: `"status"`, `"objective"`, `"route"`, `"positions"`, `"solver_status"`.
- Print using `print(f"RESULT_JSON:{json.dumps(payload)}")`.

### Code Usage
```python
from ortools.sat.python import cp_model
import json

def solve_tsp_pd_cpsat(dist_matrix, pickup_delivery_pairs, time_limit=30, num_workers=8, seed=42):
    n = len(dist_matrix)
    model = cp_model.CpModel()

    # Binary arc variables
    x = {}
    for i in range(n):
        for j in range(n):
            if i != j:
                x[i, j] = model.NewBoolVar(f'x_{i}_{j}')

    # Circuit constraint
    arcs = []
    for i in range(n):
        for j in range(n):
            if i != j:
                arcs.append((i, j, x[i, j]))
    model.AddCircuit(arcs)

    # Position variables
    u = [model.NewIntVar(0, n-1, f'u_{i}') for i in range(n)]
    model.Add(u[0] == 0)
    model.AddAllDifferent(u)

    # Link arcs to positions
    for i in range(n):
        for j in range(1, n):  # non-depot destinations
            if i != j:
                model.Add(u[j] == u[i] + 1).OnlyEnforceIf(x[i, j])
        if i != 0:  # arcs returning to depot
            model.Add(u[i] == n - 1).OnlyEnforceIf(x[i, 0])
    for j in range(1, n):  # arcs leaving depot
        model.Add(u[j] == 1).OnlyEnforceIf(x[0, j])

    # Precedence constraints
    for pickup, delivery in pickup_delivery_pairs:
        model.Add(u[pickup] < u[delivery])

    # Objective
    model.Minimize(sum(dist_matrix[i][j] * x[i, j] for i in range(n) for j in range(n) if i != j))

    # Solve
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = num_workers
    solver.parameters.random_seed = seed
    solver.parameters.relative_gap_limit = 0.0
    status = solver.Solve(model)

    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'reason': 'no_feasible_solution', 'solver_status': int(status)})}")
        return

    # Extract route
    route = [0]
    current = 0
    for _ in range(n - 1):
        for j in range(n):
            if j != current and solver.Value(x[current, j]) == 1:
                route.append(j)
                current = j
                break
    route.append(0)

    total_distance = int(solver.ObjectiveValue())
    positions = [solver.Value(u[i]) for i in range(n)]
    payload = {
        "status": "success",
        "objective": total_distance,
        "route": route,
        "positions": positions,
        "solver_status": int(status)
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not setting `relative_gap_limit = 0.0` when exact optimality is required, potentially returning suboptimal solutions.
- Extracting the tour incorrectly by not breaking out of the inner loop after finding the next node, leading to duplicate entries.
- Forgetting to validate that the extracted route actually forms a valid Hamiltonian cycle (e.g., missing nodes or incorrect return to depot).
