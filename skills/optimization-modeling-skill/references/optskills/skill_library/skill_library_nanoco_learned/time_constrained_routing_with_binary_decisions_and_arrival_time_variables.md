---
name: Time-Constrained Routing with Binary Decisions and Arrival Time Variables
description: |
  Models and solves a single-vehicle routing problem with time windows using either a MILP formulation with MTZ constraints or a CP-SAT formulation with circuit and time propagation, minimizing total travel time.
---

# Workflow 1 (MILP with MTZ Constraints)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program using binary arc variables and continuous arrival time variables. Connectivity is enforced via flow conservation, and time window feasibility is ensured through Miller-Tucker-Zemlin (MTZ) constraints that propagate arrival times along selected arcs.

### Step 1 - Define Sets and Parameters
- Define the set of nodes including the depot (index 0) and customer nodes.
- Define the travel time matrix `dist[i][j]` for all node pairs.
- Define time window bounds `a[i]` (earliest) and `b[i]` (latest) for each node.
- Compute a sufficiently large constant `M = max(b) + max(dist)` for MTZ constraints.

### Step 2 - Create Decision Variables
- Create binary variables `x[i][j]` for each directed arc `(i,j)`, indicating whether the vehicle travels directly from node `i` to node `j`.
- Create continuous variables `t[i]` representing the arrival time at each node.

### Step 3 - Add Flow Conservation Constraints
- For each node `j` (including depot), enforce exactly one incoming arc: `sum_i x[i][j] == 1`.
- For each node `i` (including depot), enforce exactly one outgoing arc: `sum_j x[i][j] == 1`.

### Step 4 - Add Time Window Constraints
- Bound arrival times: `a[i] <= t[i] <= b[i]` for all nodes `i`.

### Step 5 - Add Travel Time Propagation (MTZ)
- For each arc `(i,j)`, add: `t[j] >= t[i] + dist[i][j] - M * (1 - x[i][j])`, where `M` is a sufficiently large number (e.g., `max(b) + max(dist)`).

### Step 6 - Fix Depot Start Time
- Set `t[0] == 0` to fix departure from the depot.

### Formulation Template
```json
{
  "sets": ["N: set of nodes (0 = depot, 1..n = customers)"],
  "parameters": [
    "dist[i][j]: travel time from i to j",
    "a[i]: earliest arrival time at node i",
    "b[i]: latest arrival time at node i",
    "M: large constant, e.g., max(b) + max(dist)"
  ],
  "decision_variables": [
    "x[i][j] ∈ {0,1}: 1 if vehicle travels from i to j",
    "t[i] ≥ 0: arrival time at node i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i,j} dist[i][j] * x[i][j]"
  },
  "constraints": [
    "sum_{i} x[i][j] == 1 for all j ∈ N",
    "sum_{j} x[i][j] == 1 for all i ∈ N",
    "a[i] <= t[i] <= b[i] for all i ∈ N",
    "t[j] >= t[i] + dist[i][j] - M * (1 - x[i][j]) for all i,j ∈ N",
    "t[0] == 0"
  ]
}
```

### Common Pitfalls
- Using a too-small `M` value can incorrectly bind constraints when `x[i][j]=0`, causing infeasibility. Always set `M` to at least `max(b) + max(dist)`.
- Forgetting to include the depot in flow conservation constraints (both incoming and outgoing) will break tour completion.
- Using strict inequality constraints (e.g., `t[i] > a[i]`) is not supported; use non-strict bounds and rely on integer domains.

## Solving stage

### Strategy Overview
Use a MILP solver (e.g., Gurobi, CPLEX) with explicit parameter control. Solve to optimality with a MIP gap of zero, then extract the route and verify arrival times.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `gp.Model()` for Gurobi).
- Set parameters: `TimeLimit = [TIME_LIMIT]`, `MIPGap = 0.0`, `Threads`, `Seed` for reproducibility.

### Step 2 - Build Model from Formulation
- Add decision variables with appropriate types and bounds.
- Add constraints using the formulation template.
- Set the objective function.

### Step 3 - Solve and Check Status
- Call `optimize()`.
- Check solver status: if `GRB.OPTIMAL` or `GRB.TIME_LIMIT` with a feasible solution (`model.SolCount > 0`), proceed. Otherwise, report infeasibility or error.

### Step 4 - Extract Solution
- Retrieve the route by following `x[i][j] > 0.5` starting from the depot.
- Retrieve arrival times `t[i]` and verify they satisfy time windows.
- Compute total travel time from the objective value.

### Code Usage
```python
import gurobipy as gp

# --- Data (placeholders) ---
N = list(range(num_nodes))
dist = [[...] for _ in N]
a = [...]
b = [...]
M = max(b) + max(max(row) for row in dist)

# --- Model ---
model = gp.Model("VRPTW_MTZ")
model.Params.TimeLimit = [TIME_LIMIT]
model.Params.MIPGap = 0.0
model.Params.Threads = 4
model.Params.Seed = 42

# Variables
x = model.addVars(N, N, vtype=gp.GRB.BINARY, name="x")
t = model.addVars(N, vtype=gp.GRB.CONTINUOUS, lb=0, name="t")

# Flow conservation
for j in N:
    model.addConstr(gp.quicksum(x[i, j] for i in N) == 1, name=f"in_{j}")
for i in N:
    model.addConstr(gp.quicksum(x[i, j] for j in N) == 1, name=f"out_{i}")

# Time windows
for i in N:
    model.addConstr(t[i] >= a[i], name=f"tw_lb_{i}")
    model.addConstr(t[i] <= b[i], name=f"tw_ub_{i}")

# MTZ constraints
for i in N:
    for j in N:
        if i != j:
            model.addConstr(t[j] >= t[i] + dist[i][j] - M * (1 - x[i, j]), name=f"mtz_{i}_{j}")

# Depot start
model.addConstr(t[0] == 0, name="depot_start")

# Objective
model.setObjective(gp.quicksum(dist[i][j] * x[i, j] for i in N for j in N), gp.GRB.MINIMIZE)

# Solve
model.optimize()

# --- Result parsing ---
if model.status == gp.GRB.OPTIMAL or (model.status == gp.GRB.TIME_LIMIT and model.SolCount > 0):
    route = [0]
    current = 0
    while True:
        next_node = [j for j in N if x[current, j].X > 0.5][0]
        if next_node == 0:
            break
        route.append(next_node)
        current = next_node
    arrival_times = [t[i].X for i in route]
    print(f"RESULT:{model.ObjVal}")
else:
    print('{"status": "infeasible", "error": "No feasible solution found"}')
```

### Common Pitfalls
- Not checking `SolCount > 0` when status is `TIME_LIMIT`; the solver may have no feasible solution yet.
- Assuming the solver will find a solution quickly; always set a reasonable time limit and handle timeouts gracefully.
- Using `x[i,j].X` without verifying the variable is in the solution; check `model.SolCount` first.

# Workflow 2 (CP-SAT with Circuit Constraint)

## Modeling stage

### Strategy Overview
Formulate the problem using Google OR-Tools CP-SAT solver with a circuit constraint to enforce a single tour, and a time dimension to handle arrival times and waiting. The solver natively supports time windows and slack (waiting) variables.

### Step 1 - Define Nodes and Travel Times
- Create a list of nodes including the depot (index 0).
- Define a travel time callback function that returns `dist[i][j]` for any node pair.

### Step 2 - Create Routing Model and Parameters
- Instantiate `RoutingIndexManager` with the number of nodes and 1 vehicle.
- Set the depot index to 0.
- Register the travel time callback with `RegisterTransitCallback`.

### Step 3 - Add Time Dimension with Slack
- Add a time dimension using `AddDimension` with:
  - `slack_max` set to a large value (e.g., `horizon`) to allow waiting.
  - `capacity` set to the maximum time horizon (e.g., `max(b)`).
  - `fix_start_cumul_to_zero=True` to fix depot departure to 0.

### Step 4 - Set Time Window Constraints
- For each node, call `time_dimension.CumulVar(index).SetRange(a[i], b[i])`.
- For the depot, set the start cumul to `[0, 0]` and the end cumul to `[a[0], b[0]]`.

### Step 5 - Set Objective and Add Finalizers
- Set the arc cost evaluator to the travel time callback.
- Set the objective to minimize total travel time.
- Add `routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(index))` for all nodes to encourage earlier arrivals and reduce waiting time.

### Formulation Template
```json
{
  "sets": ["N: set of nodes (0 = depot, 1..n = customers)"],
  "parameters": [
    "dist[i][j]: travel time from i to j",
    "a[i]: earliest arrival time at node i",
    "b[i]: latest arrival time at node i",
    "horizon: max(b) + max(dist)"
  ],
  "decision_variables": [
    "NextVar[i]: next node visited after i (implicit circuit)",
    "CumulVar[i]: arrival time at node i (includes waiting)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum of dist[i][j] over selected arcs"
  },
  "constraints": [
    "Circuit constraint: each node has exactly one successor and one predecessor",
    "CumulVar[i] ∈ [a[i], b[i]] for all i ∈ N",
    "CumulVar[0] == 0 at start",
    "CumulVar[j] >= CumulVar[i] + dist[i][j] when NextVar[i] == j"
  ]
}
```

### Common Pitfalls
- Setting `slack_max = 0` prevents waiting, which can make the model infeasible if time windows require early arrival. Always allow slack.
- Confusing physical arrival time with service start time; the cumul variable represents service start (including waiting), not physical arrival.
- Not setting `fix_start_cumul_to_zero=True` and then manually setting the depot cumul range inconsistently (e.g., `SetRange(0, 0)` without fixing start).
- Not adding `AddVariableMinimizedByFinalizer` for time window nodes; the solver may not properly enforce cumul bounds during local search.

## Solving stage

### Strategy Overview
Use OR-Tools routing solver with multiple first solution strategies and local search metaheuristics. Parse the solution by reading cumul variables directly from the solver to get accurate arrival times including waiting.

### Step 1 - Set Search Parameters
- Create `DefaultRoutingSearchParameters`.
- Set `first_solution_strategy` to `PATH_CHEAPEST_ARC` initially.
- Set `local_search_metaheuristic` to `GUIDED_LOCAL_SEARCH`.
- Set `time_limit` to a reasonable value (e.g., `[TIME_LIMIT]` seconds).
- Enable logging if debugging.

### Step 2 - Solve with Fallback Strategies
- Call `SolveWithParameters`.
- If status is not `ROUTING_SUCCESS`, try alternative first solution strategies in order: `SAVINGS`, `SWEEP`, `CHRISTOFIDES`, `BEST_INSERTION`.

### Step 3 - Extract and Verify Solution
- Use `solution.Value(time_dimension.CumulVar(index))` to get arrival times for each node.
- Use `solution.Value(routing.NextVar(index))` to reconstruct the route.
- Verify arrival times against time windows.
- Compute total travel time as the sum of arc distances along the route, not the solver-reported objective which may include waiting time.

### Code Usage
```python
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

# --- Data (placeholders) ---
num_nodes = len(a)
dist = [[...] for _ in range(num_nodes)]
a = [...]
b = [...]
horizon = max(b) + max(max(row) for row in dist)

# --- Model ---
manager = pywrapcp.RoutingIndexManager(num_nodes, 1, 0)
routing = pywrapcp.RoutingModel(manager)

def travel_time_callback(from_index, to_index):
    from_node = manager.IndexToNode(from_index)
    to_node = manager.IndexToNode(to_index)
    return dist[from_node][to_node]

transit_callback_index = routing.RegisterTransitCallback(travel_time_callback)
routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

# Time dimension
time_dimension_name = 'Time'
routing.AddDimension(
    transit_callback_index,
    horizon,  # slack_max (allow waiting)
    horizon,  # capacity (max time)
    True,     # fix_start_cumul_to_zero
    time_dimension_name
)
time_dimension = routing.GetDimensionOrDie(time_dimension_name)

# Time windows
for node in range(num_nodes):
    index = manager.NodeToIndex(node)
    time_dimension.CumulVar(index).SetRange(a[node], b[node])

# Depot start/end
depot_index = manager.NodeToIndex(0)
time_dimension.CumulVar(depot_index).SetRange(0, 0)  # start at 0
routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(depot_index))

# Add finalizers for all nodes
for node in range(num_nodes):
    index = manager.NodeToIndex(node)
    routing.AddVariableMinimizedByFinalizer(time_dimension.CumulVar(index))

# --- Solve ---
search_parameters = pywrapcp.DefaultRoutingSearchParameters()
search_parameters.first_solution_strategy = (
    routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
search_parameters.local_search_metaheuristic = (
    routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
search_parameters.time_limit.seconds = [TIME_LIMIT]
search_parameters.log_search = False

solution = routing.SolveWithParameters(search_parameters)

# Fallback strategies
if not solution:
    for strategy in [
        routing_enums_pb2.FirstSolutionStrategy.SAVINGS,
        routing_enums_pb2.FirstSolutionStrategy.SWEEP,
        routing_enums_pb2.FirstSolutionStrategy.CHRISTOFIDES,
        routing_enums_pb2.FirstSolutionStrategy.BEST_INSERTION,
    ]:
        search_parameters.first_solution_strategy = strategy
        solution = routing.SolveWithParameters(search_parameters)
        if solution:
            break

# --- Result parsing ---
if solution:
    route = []
    index = routing.Start(0)
    total_time = 0
    while not routing.IsEnd(index):
        node = manager.IndexToNode(index)
        route.append(node)
        arrival = solution.Value(time_dimension.CumulVar(index))
        next_index = solution.Value(routing.NextVar(index))
        if not routing.IsEnd(next_index):
            total_time += dist[node][manager.IndexToNode(next_index)]
        index = next_index
    route.append(0)  # return to depot
    print(f"RESULT:{total_time}")
else:
    print('{"status": "infeasible", "error": "No feasible solution found"}')
```

### Common Pitfalls
- Assuming a single first solution strategy is sufficient; always try multiple strategies before concluding infeasibility.
- Manually summing travel times for validation instead of reading cumul variables; cumul values include waiting and are the actual constrained values.
- Not verifying solution feasibility by cross-checking arrival times against time windows.
