---
name: Multi-Vehicle Routing with Optional Fleet Usage
description: |
  Formulate and solve vehicle routing problems with optional vehicle usage using binary arc variables and Miller-Tucker-Zemlin subtour elimination, producing executable routes from solver output.
---

# Workflow 1 (MIP Solver with Explicit Vehicle Assignment)

## Modeling stage

### Strategy Overview
This workflow uses a mixed-integer programming (MIP) formulation with separate binary variables for arc selection (`x[v,i,j]`) and vehicle assignment (`y[v,i]`). This explicit linking simplifies constraint expression and is well-suited for solvers like SCIP and Gurobi. The Miller-Tucker-Zemlin (MTZ) method eliminates subtours.

### Step 1 - Define Core Sets and Parameters
- Define the set of vehicles `V`, the set of all nodes `N` (including depot at index 0), and the set of customer nodes `C = N \ {0}`.
- Define a distance matrix `dist[i][j]` for all `i, j` in `N`.
- Define parameter `M` as a sufficiently large number (e.g., `|C|` or `|N|`) for MTZ constraints.

### Step 2 - Create Decision Variables
- Create binary variable `x[v,i,j]` for each vehicle `v` and node pair `(i,j)`. `x[v,i,j] = 1` if vehicle `v` travels directly from node `i` to node `j`.
- Create binary variable `y[v,i]` for each vehicle `v` and node `i`. `y[v,i] = 1` if vehicle `v` visits node `i`.
- Create continuous variable `u[i]` for each customer node `i` for MTZ sequencing.

### Step 3 - Formulate Objective and Basic Constraints
- **Objective**: Minimize total travel distance: `min sum_{v,i,j} dist[i][j] * x[v,i,j]`.
- **Single Visitation**: Each customer is visited exactly once: `sum_{v,i} x[v,i,j] = 1` for all `j` in `C`.
- **Flow Conservation**: For each vehicle `v` and node `j`: `sum_i x[v,i,j] = sum_k x[v,j,k]`.
- **Link Assignment to Flow**: For each vehicle `v` and node `j`: `sum_i x[v,i,j] = y[v,j]` and `sum_k x[v,j,k] = y[v,j]`.

### Step 4 - Implement Depot and Vehicle Usage Logic
- **Optional Departure/Return**: For each vehicle `v`: `sum_{j in C} x[v,0,j] <= 1` and `sum_{i in C} x[v,i,0] <= 1`. Use `<=` to allow vehicles to remain unused.
- **Depot Self-Loop Prohibition**: `x[v,0,0] = 0` for all `v`.
- **Customer Self-Loop Prohibition**: `x[v,i,i] = 0` for all `v`, `i` in `C`.

### Step 5 - Apply MTZ Subtour Elimination
- For each customer pair `(i,j)` where `i != j`: `u[i] - u[j] + M * sum_v x[v,i,j] <= M - 1`.
- Set bounds: `1 <= u[i] <= |C|` for `i` in `C`. Fix `u[0] = 0` for the depot.

### Formulation Template
```json
{
  "sets": [
    "V: set of vehicles (index v)",
    "N: set of all nodes (index i, j, k), with depot at index 0",
    "C: set of customer nodes, C = N \\ {0}"
  ],
  "parameters": [
    "dist[i][j]: distance/cost from node i to j, for i,j in N",
    "M: sufficiently large constant (e.g., |C|)"
  ],
  "decision_variables": [
    "x[v,i,j]: binary, 1 if vehicle v travels from i to j",
    "y[v,i]: binary, 1 if vehicle v visits node i",
    "u[i]: continuous, MTZ sequencing variable for node i"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{v in V} sum_{i in N} sum_{j in N} dist[i][j] * x[v,i,j]"
  },
  "constraints": [
    "single_visitation: forall j in C -> sum_{v in V} sum_{i in N} x[v,i,j] = 1",
    "flow_conservation: forall v in V, j in N -> sum_{i in N} x[v,i,j] = sum_{k in N} x[v,j,k]",
    "link_flow_to_visit_in: forall v in V, j in N -> sum_{i in N} x[v,i,j] = y[v,j]",
    "link_flow_to_visit_out: forall v in V, j in N -> sum_{k in N} x[v,j,k] = y[v,j]",
    "departure_limit: forall v in V -> sum_{j in C} x[v,0,j] <= 1",
    "return_limit: forall v in V -> sum_{i in C} x[v,i,0] <= 1",
    "no_self_loop_depot: forall v in V -> x[v,0,0] = 0",
    "no_self_loop_customer: forall v in V, i in C -> x[v,i,i] = 0",
    "mtz: forall i in C, j in C, i != j -> u[i] - u[j] + M * sum_{v in V} x[v,i,j] <= M - 1",
    "u_lower_bound: forall i in C -> u[i] >= 1",
    "u_upper_bound: forall i in C -> u[i] <= |C|",
    "u_depot: u[0] = 0"
  ]
}
```

### Common Pitfalls
- Using `=` instead of `<=` for depot constraints, which forces all vehicles to be used unnecessarily.
- Setting `M` too small in MTZ constraints, which can cut off valid solutions.
- Forgetting to prohibit self-loops (`x[v,i,i] = 0`), which can lead to degenerate, zero-distance "routes".
- Not linking assignment variables (`y[v,i]`) to flow constraints, resulting in disconnected visits.

## Solving stage

### Strategy Overview
Solve the MIP model using a high-performance solver like Gurobi or SCIP via their Python APIs. Configure for deterministic performance, extract routes by tracing arcs from the solution, and validate the solution's completeness and objective value.

### Step 1 - Configure and Solve the Model
- Instantiate the solver (e.g., `gurobipy.Model()` or `pywraplp.Solver.CreateSolver("SCIP")`).
- Set solver parameters for reproducibility and performance: time limit, optimality gap tolerance, thread count, and random seed.
- Build the model using the formulation template, add all variables and constraints.
- Call the solver's `optimize()` or `Solve()` method.

### Step 2 - Check Solution Status and Extract Values
- Check the solver status (e.g., `model.status == GRB.OPTIMAL` or `solver.OPTIMAL`).
- If optimal or feasible, retrieve variable values: `x_val[v,i,j] = x[v,i,j].X` (Gurobi) or `x[v,i,j].solution_value()` (OR-Tools).
- Use a tolerance (e.g., `0.5`) to convert fractional values from tolerances to binary decisions.

### Step 3 - Reconstruct Vehicle Routes
- For each vehicle `v`:
    - If `sum_{j in C} x_val[v,0,j] < 0.5`, the vehicle is unused.
    - Otherwise, start at the depot (`node = 0`).
    - While `node` is not the depot or the route is just starting:
        - Find `next_node` such that `x_val[v, node, next_node] > 0.5`.
        - Append `next_node` to the route for vehicle `v`.
        - Set `node = next_node`.
    - The route ends when `next_node` is `0` (return to depot).
- Collect all non-empty routes.

### Step 4 - Validate and Report the Solution
- Verify every customer node appears in exactly one reconstructed route.
- Calculate the total distance by summing `dist[i][j]` for each arc `(i,j)` in the reconstructed routes.
- Compare this calculated distance to the solver's reported objective value to catch extraction errors.
- Report the routes, used vehicle count, and total distance.

### Code Usage
```python
# build model from formulation
import gurobipy as gp
from gurobipy import GRB

model = gp.Model('VRP')
# ... create variables x, y, u using model.addVar() ...
# ... add objective using model.setObjective() ...
# ... add all constraints using model.addConstr() ...

# solve with status / termination checks
model.setParam('TimeLimit', 30)
model.setParam('MIPGap', 0.0001)
model.setParam('Threads', 4)
model.setParam('Seed', 42)
model.optimize()

if model.status == GRB.OPTIMAL or model.status == GRB.TIME_LIMIT:
    # Extract solution values into a dictionary x_val
    x_val = {}
    for v in V:
        for i in N:
            for j in N:
                x_val[(v,i,j)] = x[v,i,j].X
    # Reconstruct routes
    routes = {}
    for v in V:
        route = [0]
        current = 0
        while True:
            next_node = None
            for j in N:
                if x_val.get((v, current, j), 0) > 0.5:
                    next_node = j
                    break
            if next_node is None or next_node == 0:
                break
            route.append(next_node)
            current = next_node
        if len(route) > 1: # Vehicle left depot
            route.append(0) # Close the loop if not already at depot
            routes[v] = route
    # Validate and print results
    # ...
else:
    print("No feasible solution found")
```

### Common Pitfalls
- Not checking for `TIME_LIMIT` status, which may still provide a good feasible solution.
- Using a naive tolerance (e.g., `0.0`) for binary variable values, missing values slightly above zero due to solver tolerances.
- Infinite loops during route reconstruction if the solution contains subtours (indicating failed MTZ constraints).
- Forgetting to close the route by appending the depot return node in the reconstruction logic.

# Workflow 2 (Compact Formulation with Per-Vehicle MTZ)

## Modeling stage

### Strategy Overview
This workflow uses a more compact MIP formulation, common in academic literature, where MTZ sequencing variables `u[v,i]` are defined per vehicle. This eliminates the need for separate assignment variables (`y[v,i]`) and can reduce model size for solvers like CBC. Vehicle usage remains optional.

### Step 1 - Define Sets and Parameters
- Define the set of vehicles `V`, the set of all nodes `N` (depot at `0`), and customer nodes `C = N \ {0}`.
- Define distance matrix `dist[i][j]`.
- Define `N_customer` = `|C|` for use in MTZ bounds.

### Step 2 - Create Decision Variables
- Create binary variable `x[v,i,j]` for each vehicle `v` and node pair `(i,j)`.
- Create continuous variable `u[v,i]` for each vehicle `v` and node `i`. This represents the position of node `i` in vehicle `v`'s route (0 for depot).

### Step 3 - Formulate Objective and Visitation Constraints
- **Objective**: Minimize total distance: `min sum_{v,i,j} dist[i][j] * x[v,i,j]`.
- **Single Visitation**: Each customer is visited by exactly one vehicle: `sum_{v, j != i} x[v,i,j] = 1` for all `i` in `C`. (Sum over all outgoing arcs from `i` across vehicles).
- **Flow Conservation**: For each vehicle `v` and node `i`: `sum_j x[v,i,j] = sum_j x[v,j,i]`.

### Step 4 - Implement Depot and Vehicle Usage Logic
- **Optional Departure**: For each vehicle `v`: `sum_{j in C} x[v,0,j] <= 1`.
- **Optional Return**: For each vehicle `v`: `sum_{i in C} x[v,i,0] <= 1`.
- **Depot Flow Balance**: For each vehicle `v`: `sum_{j in C} x[v,0,j] = sum_{i in C} x[v,i,0]`. Ensures a vehicle that leaves depot must return.
- **No Self-Loops**: `x[v,i,i] = 0` for all `v`, `i`.

### Step 5 - Apply Per-Vehicle MTZ Subtour Elimination
- For each vehicle `v` and customer pair `(i,j)` with `i != j`: `u[v,i] - u[v,j] + N_customer * x[v,i,j] <= N_customer - 1`.
- Set bounds: For customers `i` in `C`: `1 <= u[v,i] <= N_customer`. For the depot: `u[v,0] = 0`.

### Formulation Template
```json
{
  "sets": [
    "V: set of vehicles (index v)",
    "N: set of all nodes (index i, j), depot at 0",
    "C: set of customer nodes, C = N \\ {0}"
  ],
  "parameters": [
    "dist[i][j]: distance from node i to j",
    "N_customer: number of customer nodes, |C|"
  ],
  "decision_variables": [
    "x[v,i,j]: binary, 1 if vehicle v travels from i to j",
    "u[v,i]: continuous, position of node i in vehicle v's route (MTZ)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{v in V} sum_{i in N} sum_{j in N} dist[i][j] * x[v,i,j]"
  },
  "constraints": [
    "single_visitation: forall i in C -> sum_{v in V} sum_{j in N, j != i} x[v,i,j] = 1",
    "flow_conservation: forall v in V, i in N -> sum_{j in N} x[v,i,j] = sum_{j in N} x[v,j,i]",
    "departure_limit: forall v in V -> sum_{j in C} x[v,0,j] <= 1",
    "return_limit: forall v in V -> sum_{i in C} x[v,i,0] <= 1",
    "depot_balance: forall v in V -> sum_{j in C} x[v,0,j] = sum_{i in C} x[v,i,0]",
    "no_self_loop: forall v in V, i in N -> x[v,i,i] = 0",
    "mtz: forall v in V, i in C, j in C, i != j -> u[v,i] - u[v,j] + N_customer * x[v,i,j] <= N_customer - 1",
    "u_customer_lb: forall v in V, i in C -> u[v,i] >= 1",
    "u_customer_ub: forall v in V, i in C -> u[v,i] <= N_customer",
    "u_depot: forall v in V -> u[v,0] = 0"
  ]
}
```

### Common Pitfalls
- Using the total number of nodes `|N|` instead of `|C|` in the MTZ `N_customer` constant, making the constraint too weak.
- Omitting the depot flow balance constraint, which can lead to paths that start but do not end at the depot, or vice-versa.
- Applying MTZ constraints for all `i,j` in `N` (including depot), which is unnecessary and can cause infeasibility.
- Forgetting to fix `u[v,0]=0`, which is required for the MTZ formulation to work correctly.

## Solving stage

### Strategy Overview
Solve the model using an open-source MIP solver like CBC via a modeling library such as Pyomo. Emphasize model construction clarity, solver configuration for practical performance, and robust solution extraction that handles unused vehicles.

### Step 1 - Build Model with Pyomo and Configure Solver
- Define a Pyomo `ConcreteModel`.
- Create `model.x` as a `Var` indexed by `(v,i,j)` with domain `Binary`.
- Create `model.u` as a `Var` indexed by `(v,i)` with bounds.
- Add the objective and all constraints using Pyomo's `Constraint` and `Objective` components.
- Create a solver object (e.g., `SolverFactory('cbc')`) and set options: time limit, relative gap tolerance.

### Step 2 - Solve and Check Termination Condition
- Execute `solver.solve(model)`.
- Check the solver termination condition (`model.solutions[0].termination_condition`). Accept `optimal`, `feasible`, or `maxTimeLimit` with a solution.
- Check the solver status (`model.solutions[0].status`). Accept `ok`.

### Step 3 - Extract Solution and Reconstruct Routes
- Load the solution into the model object.
- Retrieve variable values: `x_val = value(model.x[v,i,j])`.
- For each vehicle `v`, trace a route starting from the depot if `sum_{j} value(model.x[v,0,j]) > 0.5`.
- Follow the sequence of arcs where `x_val > 0.5` until returning to the depot.
- Collect routes for vehicles that left the depot.

### Step 4 - Validate Solution and Compute Metrics
- Verify all customer nodes appear in exactly one extracted route.
- Compute the total distance by summing the distances of arcs in the extracted routes.
- Compare this computed distance to `value(model.objective)` to ensure consistency.
- Report the list of routes, number of used vehicles, and total distance.

### Code Usage
```python
# build model from formulation
from pyomo.environ import ConcreteModel, Set, Param, Var, Binary, NonNegativeReals, Objective, Constraint, SolverFactory, value

model = ConcreteModel('VRP_MTZ')
# Define sets
model.V = Set(initialize=range(num_vehicles))
model.N = Set(initialize=range(num_nodes))
model.C = Set(initialize=range(1, num_nodes)) # customers
# ... define parameters (dist) as a Param model.dist ...
# Variables
model.x = Var(model.V, model.N, model.N, domain=Binary)
model.u = Var(model.V, model.N, domain=NonNegativeReals, bounds=(0, num_customers))
# Objective
model.obj = Objective(expr=sum(model.dist[i,j] * model.x[v,i,j] for v in model.V for i in model.N for j in model.N))
# Add constraints (examples)
def single_visit_rule(model, i):
    return sum(model.x[v,i,j] for v in model.V for j in model.N if j != i) == 1
model.single_visit = Constraint(model.C, rule=single_visit_rule)
# ... add all other constraints ...

# solve with status / termination checks
solver = SolverFactory('cbc')
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0001
results = solver.solve(model)

if results.solver.termination_condition == 'optimal' or results.solver.termination_condition == 'feasible':
    if results.solver.status == 'ok':
        # Extract solution
        routes = {}
        for v in model.V:
            route = [0]
            current = 0
            visited = set()
            while True:
                next_node = None
                for j in model.N:
                    if value(model.x[v, current, j]) > 0.5:
                        next_node = j
                        break
                if next_node is None or next_node in visited: # prevent cycles
                    break
                if next_node == 0:
                    route.append(0)
                    break
                route.append(next_node)
                visited.add(next_node)
                current = next_node
            if len(route) > 1:
                routes[v] = route
        # Validate and report
        # ...
else:
    print("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting proper bounds on `u[v,i]` variables in Pyomo, leading to unbounded variables.
- Using `value()` on variables before loading the solution, resulting in `None` or default values.
- Inefficient constraint rule definitions that slow down model construction for large instances.
- Not handling the case where the solver hits a time limit but returns a feasible solution (`termination_condition == 'maxTimeLimit'`).
