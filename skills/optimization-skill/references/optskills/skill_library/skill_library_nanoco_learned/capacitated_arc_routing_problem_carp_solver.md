---
name: Capacitated Arc Routing Problem (CARP) Solver
description: |
  Models and solves the Capacitated Arc Routing Problem using either a MILP-based task sequencing formulation or a state-based MILP formulation, with solver-specific extraction and validation.
---

# Workflow 1 (Task-Sequencing MILP with OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Decompose arc routing into task sequencing by treating each required edge as a task with two possible traversal directions. Use binary assignment variables for vehicle-task-direction combinations, predecessor/successor variables for route continuity, and flow conservation constraints to enforce route structure.

### Step 1 - Define Task and Direction Sets
- For each required edge (u,v), define two tasks: direction 0 (enter at u, exit at v) and direction 1 (enter at v, exit at u).
- Precompute `start_node[task, direction]` and `end_node[task, direction]` for all task-direction pairs.

### Step 2 - Create Binary Assignment Variables
- Define `x[vehicle, task, direction]` as a binary variable indicating whether a vehicle services a given task in a specific direction.
- Define `first[vehicle, task, direction]` and `last[vehicle, task, direction]` as binary variables marking the first and last serviced tasks for each vehicle.
- Define `y[vehicle, task1, dir1, task2, dir2]` as a binary variable indicating that vehicle services task1 in dir1 immediately before task2 in dir2.

### Step 3 - Enforce Flow Conservation and Route Structure
- For each (vehicle, task, direction): `first + sum(incoming y) == x` and `last + sum(outgoing y) == x`.
- **Prerequisite Check:** Enforce that each vehicle has **exactly one** first task and **exactly one** last task **if and only if** it services at least one task. Use auxiliary binary variable `vehicle_used[vehicle]` and constraints:
  - `sum(task, direction) x[vehicle, task, direction] >= 1 => vehicle_used[vehicle] == 1`
  - `sum(task, direction) x[vehicle, task, direction] == 0 => vehicle_used[vehicle] == 0`
  - `sum(task, direction) first[vehicle, task, direction] == vehicle_used[vehicle]`
  - `sum(task, direction) last[vehicle, task, direction] == vehicle_used[vehicle]`
- This prevents cycles without designated start/end points and ensures a valid route structure.

### Step 4 - Add Capacity and Coverage Constraints
- Capacity: For each vehicle, `sum(demand[task] * x[vehicle, task, direction]) <= capacity`.
- Coverage: For each task, `sum(x[vehicle, task, direction] over vehicles and directions) == 1`.

### Step 5 - Prevent Invalid Transitions
- Add constraint `y[vehicle, task, dir1, task, dir2] == 0` to prevent self-loops where a task immediately follows itself.

### Step 6 - Formulate Objective
- Minimize total travel distance = sum over vehicles of (distance from depot to first task's start node) + (service traversal distance for each assigned task) + (deadhead distance between consecutive tasks) + (distance from last task's end node back to depot).

### Formulation Template
```json
{
  "sets": ["VEHICLES", "TASKS", "DIRECTIONS"],
  "parameters": ["demand[TASKS]", "capacity[VEHICLES]", "start_node[TASKS, DIRECTIONS]", "end_node[TASKS, DIRECTIONS]", "dist_matrix[NODES, NODES]"],
  "decision_variables": [
    "x[VEHICLES, TASKS, DIRECTIONS] binary",
    "first[VEHICLES, TASKS, DIRECTIONS] binary",
    "last[VEHICLES, TASKS, DIRECTIONS] binary",
    "y[VEHICLES, TASKS, DIRECTIONS, TASKS, DIRECTIONS] binary",
    "vehicle_used[VEHICLES] binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(v in VEHICLES, t in TASKS, d in DIRECTIONS) (dist_matrix[DEPOT, start_node[t,d]] * first[v,t,d] + dist_matrix[end_node[t,d], DEPOT] * last[v,t,d] + dist_matrix[end_node[t,d], start_node[t2,d2]] * y[v,t,d,t2,d2] + dist_matrix[start_node[t,d], end_node[t,d]] * x[v,t,d])"
  },
  "constraints": [
    "forall v in VEHICLES, t in TASKS, d in DIRECTIONS: first[v,t,d] + sum(t2,d2) y[v,t2,d2,t,d] == x[v,t,d]",
    "forall v in VEHICLES, t in TASKS, d in DIRECTIONS: last[v,t,d] + sum(t2,d2) y[v,t,d,t2,d2] == x[v,t,d]",
    "forall v in VEHICLES: sum(t,d) demand[t] * x[v,t,d] <= capacity[v]",
    "forall t in TASKS: sum(v,d) x[v,t,d] == 1",
    "forall v in VEHICLES, t in TASKS, d1 in DIRECTIONS, d2 in DIRECTIONS: y[v,t,d1,t,d2] == 0",
    "forall v in VEHICLES: sum(t,d) x[v,t,d] >= 1 -> vehicle_used[v] == 1",
    "forall v in VEHICLES: sum(t,d) x[v,t,d] == 0 -> vehicle_used[v] == 0",
    "forall v in VEHICLES: sum(t,d) first[v,t,d] == vehicle_used[v]",
    "forall v in VEHICLES: sum(t,d) last[v,t,d] == vehicle_used[v]"
  ]
}
```

### Common Pitfalls
- Forgetting to include all four distance components (depot-to-first, service, deadhead, last-to-depot) in the objective.
- Using incomplete flow conservation without enforcing exactly one first/last per used vehicle, leading to disconnected route fragments or cycles.
- Using `itertools.product` for enumeration instead of solver variables for realistic instance sizes.
- Not linking `vehicle_used` correctly to assignment variables, causing invalid route extraction.

## Solving stage

### Strategy Overview
Implement the model using OR-Tools CP-SAT solver with binary integer variables. Configure solver parameters for time limits and optimality gaps, then extract and validate the solution by reconstructing routes from the decision variables.

### Step 1 - Initialize Solver and Variables
- Create a `CpModel()` instance.
- Add all binary decision variables (`x`, `first`, `last`, `y`, `vehicle_used`) using `model.NewBoolVar()`.

### Step 2 - Add Constraints
- Add flow conservation and route structure constraints using `model.Add()`.
- Add capacity constraints using `model.Add(sum(...) <= capacity)`.
- Add coverage constraints using `model.Add(sum(...) == 1)`.
- Add self-loop prevention constraints.
- **Prerequisite Check:** Add vehicle usage linking constraints using `model.Add(sum(x) >= 1).OnlyEnforceIf(vehicle_used)` and `model.Add(sum(x) == 0).OnlyEnforceIf(vehicle_used.Not())`. Enforce `sum(first) == vehicle_used` and `sum(last) == vehicle_used`.

### Step 3 - Set Objective
- Build the linear expression for total travel distance.
- Use `model.Minimize(expression)` to set the objective.

### Step 4 - Configure and Solve
- Create a `CpSolver()` instance.
- Set parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.relative_gap_limit = [GAP]`.
- Call `status = solver.Solve(model)`.

### Step 5 - Extract and Validate Solution
- **Early Warning:** Check `status == cp_model.OPTIMAL` or `status == cp_model.FEASIBLE`. If not, return status immediately. **Do not proceed with extraction on infeasible or unknown status.**
- For each vehicle, verify `vehicle_used` is consistent with assigned tasks. If `vehicle_used` is 1, ensure exactly one `first` and one `last` variable is 1.
- For each vehicle with `vehicle_used == 1`, iterate over tasks to find `first` variable with value 1, then follow `y` variables to reconstruct the sequence.
- **Fallback Guidance:** If a vehicle has assigned tasks but no clear start/end sequence, flag the solution as potentially infeasible and re-check constraint satisfaction.
- Compute actual route distance from the node sequence and compare with objective value to validate.

### Code Usage
```python
from ortools.sat.python import cp_model

def build_carp_model(vehicles, tasks, directions, demand, capacity, start_node, end_node, dist_matrix, depot):
    model = cp_model.CpModel()
    
    # Decision variables
    x = {}
    first = {}
    last = {}
    y = {}
    vehicle_used = {}
    for v in vehicles:
        vehicle_used[v] = model.NewBoolVar(f'used_{v}')
        for t in tasks:
            for d in directions:
                x[v,t,d] = model.NewBoolVar(f'x_{v}_{t}_{d}')
                first[v,t,d] = model.NewBoolVar(f'first_{v}_{t}_{d}')
                last[v,t,d] = model.NewBoolVar(f'last_{v}_{t}_{d}')
                for t2 in tasks:
                    for d2 in directions:
                        y[v,t,d,t2,d2] = model.NewBoolVar(f'y_{v}_{t}_{d}_{t2}_{d2}')
    
    # Flow conservation
    for v in vehicles:
        for t in tasks:
            for d in directions:
                incoming = sum(y[v,t2,d2,t,d] for t2 in tasks for d2 in directions)
                outgoing = sum(y[v,t,d,t2,d2] for t2 in tasks for d2 in directions)
                model.Add(first[v,t,d] + incoming == x[v,t,d])
                model.Add(last[v,t,d] + outgoing == x[v,t,d])
    
    # Vehicle usage linking
    for v in vehicles:
        total_assigned = sum(x[v,t,d] for t in tasks for d in directions)
        model.Add(total_assigned >= 1).OnlyEnforceIf(vehicle_used[v])
        model.Add(total_assigned == 0).OnlyEnforceIf(vehicle_used[v].Not())
        model.Add(sum(first[v,t,d] for t in tasks for d in directions) == vehicle_used[v])
        model.Add(sum(last[v,t,d] for t in tasks for d in directions) == vehicle_used[v])
    
    # Capacity constraints
    for v in vehicles:
        model.Add(sum(demand[t] * x[v,t,d] for t in tasks for d in directions) <= capacity[v])
    
    # Coverage constraints
    for t in tasks:
        model.Add(sum(x[v,t,d] for v in vehicles for d in directions) == 1)
    
    # Self-loop prevention
    for v in vehicles:
        for t in tasks:
            for d1 in directions:
                for d2 in directions:
                    model.Add(y[v,t,d1,t,d2] == 0)
    
    # Objective
    obj_terms = []
    for v in vehicles:
        for t in tasks:
            for d in directions:
                obj_terms.append(dist_matrix[depot][start_node[t,d]] * first[v,t,d])
                obj_terms.append(dist_matrix[end_node[t,d]][depot] * last[v,t,d])
                obj_terms.append(dist_matrix[start_node[t,d]][end_node[t,d]] * x[v,t,d])
                for t2 in tasks:
                    for d2 in directions:
                        obj_terms.append(dist_matrix[end_node[t,d]][start_node[t2,d2]] * y[v,t,d,t2,d2])
    model.Minimize(sum(obj_terms))
    
    return model, x, first, last, y, vehicle_used

def solve_carp(model, x, first, last, y, vehicle_used, vehicles, tasks, directions, time_limit=60):
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.relative_gap_limit = 0.0
    
    status = solver.Solve(model)
    
    # Early failure detection: do not extract on non-feasible status
    if status not in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        return {"status": "INFEASIBLE" if status == cp_model.INFEASIBLE else "UNKNOWN", "objective": None}
    
    result = {"status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
              "objective": solver.ObjectiveValue()}
    
    # Extract routes
    routes = {}
    for v in vehicles:
        if solver.Value(vehicle_used[v]) == 1:
            route = []
            # Find first task
            for t in tasks:
                for d in directions:
                    if solver.Value(first[v,t,d]) == 1:
                        route.append((t,d))
                        break
                if route:
                    break
            
            # Follow sequence
            while route:
                current_t, current_d = route[-1]
                next_found = False
                for t2 in tasks:
                    for d2 in directions:
                        if solver.Value(y[v,current_t,current_d,t2,d2]) == 1:
                            route.append((t2,d2))
                            next_found = True
                            break
                    if next_found:
                        break
                if not next_found:
                    break
            
            routes[v] = route
        else:
            routes[v] = []
    
    result["routes"] = routes
    return result

# Usage
# model, x, first, last, y, vehicle_used = build_carp_model(vehicles, tasks, directions, demand, capacity, start_node, end_node, dist_matrix, depot)
# result = solve_carp(model, x, first, last, y, vehicle_used, vehicles, tasks, directions)
# print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to runtime errors.
- Assuming all vehicles must be used; the model naturally allows vehicles with no assigned tasks.
- Forgetting to set a time limit, causing the solver to run indefinitely on larger instances.
- Extracting routes without verifying `vehicle_used` and start/end consistency, risking incorrect reconstruction.

# Workflow 2 (State-Based MILP with HiGHS)

## Modeling stage

### Strategy Overview
Model the CARP as a state-based MILP where each required edge has two service states (orientations). Use binary assignment and sequencing variables with Miller-Tucker-Zemlin (MTZ) subtour elimination constraints to ensure valid routes.

### Step 1 - Define Service States
- For each required edge (u,v) with demand d, define state 0 (enter at u, exit at v) and state 1 (enter at v, exit at u).
- Precompute entry and exit nodes for each state.

### Step 2 - Create Binary Assignment Variables
- Define `x[vehicle, edge, state]` = 1 if vehicle services edge in that state.
- Define `start[vehicle, edge, state]` and `end[vehicle, edge, state]` as binary variables marking first and last serviced edges.

### Step 3 - Create Sequencing Variables
- Define `z[vehicle, edge1, state1, edge2, state2]` = 1 if vehicle services edge1 in state1 immediately before edge2 in state2.

### Step 4 - Enforce Flow Conservation and Route Structure
- For each (vehicle, edge, state): `start + sum(incoming z) == x` and `end + sum(outgoing z) == x`.
- **Prerequisite Check:** Enforce that each vehicle has exactly one start and one end edge **if and only if** it services at least one edge. Use auxiliary binary variable `vehicle_active[vehicle]` and constraints:
  - `sum(edge, state) x[vehicle, edge, state] >= 1 => vehicle_active[vehicle] == 1`
  - `sum(edge, state) x[vehicle, edge, state] == 0 => vehicle_active[vehicle] == 0`
  - `sum(edge, state) start[vehicle, edge, state] == vehicle_active[vehicle]`
  - `sum(edge, state) end[vehicle, edge, state] == vehicle_active[vehicle]`

### Step 5 - Add Capacity and Coverage Constraints
- Capacity: For each vehicle, `sum(demand[edge] * x[vehicle, edge, state]) <= capacity`.
- Coverage: For each edge, `sum(x[vehicle, edge, state] over vehicles and states) == 1`.

### Step 6 - Add MTZ Subtour Elimination
- Define continuous position variables `u[vehicle, edge, state]` bounded between 0 and (number of edges + 1).
- For each `z[vehicle, e1, s1, e2, s2]` = 1, enforce `u[vehicle, e2, s2] >= u[vehicle, e1, s1] + 1` using a big-M formulation: `u[e2,s2] >= u[e1,s1] + 1 - M*(1 - z[e1,s1,e2,s2])` with `M = len(edges) + 1`.

### Step 7 - Formulate Objective
- Minimize total travel distance = sum over vehicles of (distance from depot to first edge's entry node) + (service traversal cost for each edge) + (deadhead cost between consecutive edges) + (distance from last edge's exit node back to depot).

### Formulation Template
```json
{
  "sets": ["VEHICLES", "EDGES", "STATES"],
  "parameters": ["demand[EDGES]", "capacity[VEHICLES]", "entry_node[EDGES, STATES]", "exit_node[EDGES, STATES]", "dist_matrix[NODES, NODES]"],
  "decision_variables": [
    "x[VEHICLES, EDGES, STATES] binary",
    "start[VEHICLES, EDGES, STATES] binary",
    "end[VEHICLES, EDGES, STATES] binary",
    "z[VEHICLES, EDGES, STATES, EDGES, STATES] binary",
    "u[VEHICLES, EDGES, STATES] continuous",
    "vehicle_active[VEHICLES] binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(v in VEHICLES, e in EDGES, s in STATES) (dist_matrix[DEPOT, entry_node[e,s]] * start[v,e,s] + dist_matrix[exit_node[e,s], DEPOT] * end[v,e,s] + dist_matrix[entry_node[e,s], exit_node[e,s]] * x[v,e,s]) + sum(v in VEHICLES, e1 in EDGES, s1 in STATES, e2 in EDGES, s2 in STATES) dist_matrix[exit_node[e1,s1], entry_node[e2,s2]] * z[v,e1,s1,e2,s2]"
  },
  "constraints": [
    "forall v in VEHICLES, e in EDGES, s in STATES: start[v,e,s] + sum(e2,s2) z[v,e2,s2,e,s] == x[v,e,s]",
    "forall v in VEHICLES, e in EDGES, s in STATES: end[v,e,s] + sum(e2,s2) z[v,e,s,e2,s2] == x[v,e,s]",
    "forall v in VEHICLES: sum(e,s) demand[e] * x[v,e,s] <= capacity[v]",
    "forall e in EDGES: sum(v,s) x[v,e,s] == 1",
    "forall v in VEHICLES, e1 in EDGES, s1 in STATES, e2 in EDGES, s2 in STATES: u[v,e2,s2] >= u[v,e1,s1] + 1 - (len(EDGES)+1) * (1 - z[v,e1,s1,e2,s2])",
    "forall v in VEHICLES, e in EDGES, s in STATES: 0 <= u[v,e,s] <= len(EDGES) + 1",
    "forall v in VEHICLES: sum(e,s) x[v,e,s] >= 1 -> vehicle_active[v] == 1",
    "forall v in VEHICLES: sum(e,s) x[v,e,s] == 0 -> vehicle_active[v] == 0",
    "forall v in VEHICLES: sum(e,s) start[v,e,s] == vehicle_active[v]",
    "forall v in VEHICLES: sum(e,s) end[v,e,s] == vehicle_active[v]"
  ]
}
```

### Common Pitfalls
- Not bounding MTZ position variables, leading to unboundedness or numerical issues.
- Forgetting to include the service traversal distance in the objective (distance from entry to exit node for each assigned edge).
- Using a big-M value that is too small, causing MTZ constraints to be ineffective for subtour elimination.
- Not enforcing the link between vehicle activity and start/end variables, allowing cycles without designated start/end.

## Solving stage

### Strategy Overview
Implement the model using HiGHS solver via Pyomo or directly with Python-MIP. Configure solver parameters for time limits and optimality gaps, then extract and validate the solution by reconstructing routes from the decision variables.

### Step 1 - Initialize Model and Variables
- Create a `Model()` instance from Python-MIP or Pyomo.
- Add all binary decision variables (`x`, `start`, `end`, `z`, `vehicle_active`) and continuous variables (`u`).

### Step 2 - Add Constraints
- Add flow conservation and route structure constraints.
- Add capacity and coverage constraints.
- Add MTZ subtour elimination constraints using big-M formulation with `M = len(edges) + 1`.
- **Prerequisite Check:** Add vehicle activity linking constraints using indicator constraints or big-M.

### Step 3 - Set Objective
- Build the linear expression for total travel distance.
- Set the objective to minimize.

### Step 4 - Configure and Solve
- Set solver parameters: `model.optimize(max_seconds=[TIME_LIMIT], mip_rel_gap=[GAP])`.
- Check solver status after optimization.

### Step 5 - Extract and Validate Solution
- **Early Warning:** Verify `status == SolverStatus.ok` and `termination_condition` is `optimal` or `feasible`. If not, return status immediately. **Do not output pseudo numeric answers when execution fails.**
- For each vehicle, check `vehicle_active` consistency. If active, ensure exactly one `start` and one `end` variable is 1.
- For each active vehicle, find the start edge-state pair, then follow `z` variables to reconstruct the sequence.
- **Fallback Guidance:** If a vehicle has assigned edges but no clear start/end sequence, flag the solution as potentially infeasible and re-check constraint satisfaction.
- Manually verify capacity constraints and coverage.
- Recompute total distance from the solution to validate the objective value.

### Code Usage
```python
from mip import Model, BINARY, CONTINUOUS, minimize, xsum, OptimizationStatus

def build_carp_model_mip(vehicles, edges, states, demand, capacity, entry_node, exit_node, dist_matrix, depot):
    model = Model("CARP")
    
    # Decision variables
    x = {}
    start = {}
    end = {}
    z = {}
    u = {}
    vehicle_active = {}
    for v in vehicles:
        vehicle_active[v] = model.add_var(var_type=BINARY, name=f'active_{v}')
        for e in edges:
            for s in states:
                x[v,e,s] = model.add_var(var_type=BINARY, name=f'x_{v}_{e}_{s}')
                start[v,e,s] = model.add_var(var_type=BINARY, name=f'start_{v}_{e}_{s}')
                end[v,e,s] = model.add_var(var_type=BINARY, name=f'end_{v}_{e}_{s}')
                u[v,e,s] = model.add_var(lb=0, ub=len(edges)+1, name=f'u_{v}_{e}_{s}')
                for e2 in edges:
                    for s2 in states:
                        z[v,e,s,e2,s2] = model.add_var(var_type=BINARY, name=f'z_{v}_{e}_{s}_{e2}_{s2}')
    
    # Flow conservation
    for v in vehicles:
        for e in edges:
            for s in states:
                incoming = xsum(z[v,e2,s2,e,s] for e2 in edges for s2 in states)
                outgoing = xsum(z[v,e,s,e2,s2] for e2 in edges for s2 in states)
                model += start[v,e,s] + incoming == x[v,e,s]
                model += end[v,e,s] + outgoing == x[v,e,s]
    
    # Vehicle activity linking
    for v in vehicles:
        total_assigned = xsum(x[v,e,s] for e in edges for s in states)
        model += total_assigned >= 1 - (len(edges)*2) * (1 - vehicle_active[v])
        model += total_assigned <= (len(edges)*2) * vehicle_active[v]
        model += xsum(start[v,e,s] for e in edges for s in states) == vehicle_active[v]
        model += xsum(end[v,e,s] for e in edges for s in states) == vehicle_active[v]
    
    # Capacity constraints
    for v in vehicles:
        model += xsum(demand[e] * x[v,e,s] for e in edges for s in states) <= capacity[v]
    
    # Coverage constraints
    for e in edges:
        model += xsum(x[v,e,s] for v in vehicles for s in states) == 1
    
    # MTZ subtour elimination
    M = len(edges) + 1
    for v in vehicles:
        for e1 in edges:
            for s1 in states:
                for e2 in edges:
                    for s2 in states:
                        if e1 != e2 or s1 != s2:
                            model += u[v,e2,s2] >= u[v,e1,s1] + 1 - M * (1 - z[v,e1,s1,e2,s2])
    
    # Objective
    obj = xsum(
        dist_matrix[depot][entry_node[e,s]] * start[v,e,s] +
        dist_matrix[exit_node[e,s]][depot] * end[v,e,s] +
        dist_matrix[entry_node[e,s]][exit_node[e,s]] * x[v,e,s]
        for v in vehicles for e in edges for s in states
    )
    obj += xsum(
        dist_matrix[exit_node[e1,s1]][entry_node[e2,s2]] * z[v,e1,s1,e2,s2]
        for v in vehicles for e1 in edges for s1 in states for e2 in edges for s2 in states
    )
    model.objective = minimize(obj)
    
    return model, x, start, end, z, vehicle_active

def solve_carp_mip(model, x, start, end, z, vehicle_active, vehicles, edges, states, time_limit=60):
    model.optimize(max_seconds=time_limit, mip_rel_gap=0.0)
    
    # Early failure detection: do not extract on non-feasible status
    if model.status not in (OptimizationStatus.OPTIMAL, OptimizationStatus.FEASIBLE):
        return {"status": "INFEASIBLE" if model.status == OptimizationStatus.INFEASIBLE else "UNKNOWN", "objective": None}
    
    result = {"status": "OPTIMAL" if model.status == OptimizationStatus.OPTIMAL else "FEASIBLE",
              "objective": model.objective_value}
    
    # Extract routes
    routes = {}
    for v in vehicles:
        if vehicle_active[v].x >= 0.5:
            route = []
            # Find start edge-state
            for e in edges:
                for s in states:
                    if start[v,e,s].x >= 0.5:
                        route.append((e,s))
                        break
                if route:
                    break
            
            # Follow sequence
            while route:
                current_e, current_s = route[-1]
                next_found = False
                for e2 in edges:
                    for s2 in states:
                        if z[v,current_e,current_s,e2,s2].x >= 0.5:
                            route.append((e2,s2))
                            next_found = True
                            break
                    if next_found:
                        break
                if not next_found:
                    break
            
            routes[v] = route
        else:
            routes[v] = []
    
    result["routes"] = routes
    return result

# Usage
# model, x, start, end, z, vehicle_active = build_carp_model_mip(vehicles, edges, states, demand, capacity, entry_node, exit_node, dist_matrix, depot)
# result = solve_carp_mip(model, x, start, end, z, vehicle_active, vehicles, edges, states)
# print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Using a big-M value that is too small, causing MTZ constraints to be ineffective for subtour elimination.
- Not checking for numerical stability when using large distance values in the objective.
- Forgetting to handle the case where a vehicle has no assigned tasks (no start variable is 1).
- Extracting routes without verifying `vehicle_active` and start/end consistency, risking incorrect reconstruction.
