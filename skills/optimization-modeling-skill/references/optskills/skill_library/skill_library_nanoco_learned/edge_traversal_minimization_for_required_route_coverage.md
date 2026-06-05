---
name: Edge Traversal Minimization for Required Route Coverage
description: |
  Models and solves routing problems requiring traversal of specified edges with minimum total distance, using integer flow formulations and either constraint programming or mixed-integer programming solvers.
---

# Workflow 1 (CP-SAT Integer Flow)

## Modeling stage

### Strategy Overview
Model the problem as an integer flow on a directed, fully connected network of nodes. Use CP-SAT to enforce flow conservation and required edge coverage, ensuring a closed Eulerian tour that services all required edges. The vehicle may traverse any arc between nodes; the distance matrix defines the cost for each possible traversal.

### Step 1 - Define Directed Flow Variables
- For each ordered pair `(i,j)` with `i != j`, create an integer variable `y[(i,j)]` representing the number of traversals from `i` to `j`.
- Set domain to `[0, UB]` where `UB` is a small integer (e.g., 10) to bound the search space.

### Step 2 - Enforce Flow Conservation
- For each node `k`, add constraint: `sum(y[(k,j)] for j != k) == sum(y[(i,k)] for i != k)`.
- This ensures the tour is a closed walk (Eulerian circuit).

### Step 3 - Cover Required Edges
- For each required undirected edge `(u,v)`, add constraint: `y[(u,v)] + y[(v,u)] >= 1`.
- This guarantees at least one traversal in either direction.

### Step 4 - Set Objective
- Minimize total distance: `sum(dist[i][j] * y[(i,j)] for all ordered pairs (i,j) with i != j)`.
- Use a precomputed all-pairs shortest path distance matrix.

### Formulation Template
```json
{
  "sets": ["NODES", "REQUIRED_EDGES"],
  "parameters": ["dist[i][j] for all i,j in NODES, i != j"],
  "decision_variables": [
    "y[(i,j)] integer >= 0 for each ordered pair (i,j) with i != j"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(dist[i][j] * y[(i,j)] for all i != j)"
  },
  "constraints": [
    "sum(y[(k,j)] for j != k) == sum(y[(i,k)] for i != k) for each k in NODES",
    "y[(u,v)] + y[(v,u)] >= 1 for each undirected required edge (u,v) in REQUIRED_EDGES"
  ]
}
```

### Common Pitfalls
- **Incorrectly restricting traversals to physical edges.** The model must allow flow on all arcs; required edges define service obligations, not traversal restrictions.
- Using binary variables instead of integer variables, which prevents modeling multiple traversals of the same arc.
- Omitting the required edge coverage constraint, leaving edges unserviced.
- **Mismatching cost calculation with allowed arcs.** The objective must sum over all ordered pairs `(i,j)` where `i != j`, using the distance matrix for cost. Do not limit the sum to a subset of edges.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver to handle the integer programming model. Configure for parallel search and time-limited execution, then extract and verify the solution.

### Step 1 - Initialize Solver and Model
- Import `cp_model` from `ortools.sat.python`.
- Create `CpModel()` instance and add all variables with appropriate domains.

### Step 2 - Add Constraints and Objective
- Add flow conservation constraints using `model.Add()`.
- Add required edge coverage constraints.
- Set objective using `model.Minimize()` with the full distance matrix over all ordered pairs.

### Step 3 - Configure and Solve
- Create `CpSolver()` instance.
- Set parameters: `max_time_in_seconds = [TIME_LIMIT]`, `num_search_workers = 8`, `random_seed = 42`.
- Call `solver.Solve(model)` and capture status.

### Step 4 - Extract and Verify Results
- Check status: `OPTIMAL` or `FEASIBLE` indicate valid solutions.
- Print non-zero directed flows for verification.
- **Verify that all required edges are covered:** For each `(u,v)` in required edges, ensure `solver.Value(y[(u,v)]) + solver.Value(y[(v,u)]) >= 1`.
- **Verify flow conservation per node** by recomputing inflow and outflow.
- **Verify objective consistency:** Recompute total cost from the solution flows and the full distance matrix to ensure it matches the solver's reported objective.

### Code Usage
```python
from ortools.sat.python import cp_model

def solve_route_coverage_cpsat(nodes, required_edges, dist, time_limit=60, ub=10):
    model = cp_model.CpModel()
    y = {}
    # Create directed flow variables for all ordered pairs
    for i in nodes:
        for j in nodes:
            if i != j:
                y[(i, j)] = model.NewIntVar(0, ub, f'y_{i}_{j}')
    
    # Flow conservation
    for k in nodes:
        outflow = sum(y[(k, j)] for j in nodes if j != k)
        inflow = sum(y[(i, k)] for i in nodes if i != k)
        model.Add(outflow == inflow)
    
    # Required edge coverage
    for (u, v) in required_edges:
        model.Add(y[(u, v)] + y[(v, u)] >= 1)
    
    # Objective: sum over all ordered pairs
    model.Minimize(sum(dist[i][j] * y[(i, j)] for i in nodes for j in nodes if i != j))
    
    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = time_limit
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    status = solver.Solve(model)
    
    if status == cp_model.OPTIMAL or status == cp_model.FEASIBLE:
        result = {"status": "OPTIMAL" if status == cp_model.OPTIMAL else "FEASIBLE",
                  "objective": solver.ObjectiveValue()}
        # Verification checks
        for (u, v) in required_edges:
            if not (solver.Value(y[(u, v)]) + solver.Value(y[(v, u)]) >= 1):
                raise ValueError(f"Required edge ({u},{v}) not covered.")
        # Print non-zero flows
        for (i, j) in y:
            if solver.Value(y[(i, j)]) > 0:
                print(f"Arc ({i}->{j}): {solver.Value(y[(i, j)])} traversals")
        return result
    else:
        return {"status": "INFEASIBLE", "objective": None}
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, missing valid suboptimal solutions.
- Forgetting to set `random_seed` for reproducibility across runs.
- **Failing to verify required edge coverage and objective consistency**, potentially accepting solutions that violate problem constraints or have mismatched costs.

# Workflow 2 (HiGHS MIP Flow)

## Modeling stage

### Strategy Overview
Model the problem directly with directed integer flow variables on all arcs in a fully connected network. Use a MIP solver to minimize total traversal distance while enforcing flow conservation and required edge coverage. The distance matrix provides the cost for each possible arc traversal.

### Step 1 - Define Directed Flow Variables
- For each ordered pair `(i,j)` with `i != j`, create an integer variable `x[i,j]` representing the number of traversals from `i` to `j`.
- Set domain to `NonNegativeIntegers` to allow multiple passes.

### Step 2 - Enforce Flow Conservation
- For each node `k`, add constraint: `sum(x[k,j] for j != k) == sum(x[i,k] for i != k)`.
- This ensures a closed tour starting and ending at the same node.

### Step 3 - Cover Required Edges
- For each required undirected edge `(u,v)`, add constraint: `x[u,v] + x[v,u] >= 1`.
- This guarantees at least one traversal in either direction.

### Step 4 - Set Objective
- Minimize total distance: `sum(dist[i,j] * x[i,j] for all ordered pairs (i,j) with i != j)`.
- Use a precomputed all-pairs shortest path distance matrix.

### Formulation Template
```json
{
  "sets": ["NODES", "ARCS = {(i,j) for i,j in NODES, i != j}", "REQUIRED_EDGES"],
  "parameters": ["dist[i][j] for all (i,j) in ARCS"],
  "decision_variables": [
    "x[i,j] integer >= 0 for each (i,j) in ARCS"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(dist[i][j] * x[i,j] for all (i,j) in ARCS)"
  },
  "constraints": [
    "sum(x[k,j] for j != k) == sum(x[i,k] for i != k) for each k in NODES",
    "x[u,v] + x[v,u] >= 1 for each undirected required edge (u,v) in REQUIRED_EDGES"
  ]
}
```

### Common Pitfalls
- Using binary variables instead of integer variables, preventing multiple traversals of the same arc.
- Forgetting to add both directions for required edge coverage, leaving the edge potentially uncovered.
- **Restricting the arc set to physical edges.** The model must use the fully connected arc set `ARCS`; required edges only impose coverage constraints.
- **Mismatching the objective sum with the arc set.** Ensure the objective sums over all arcs in `ARCS`, not a subset.

## Solving stage

### Strategy Overview
Use HiGHS solver via Pyomo to solve the MIP model. Configure for exact optimality with time limit and parallel threads, then extract and verify the solution.

### Step 1 - Build Pyomo Model
- Import `pyomo.environ` as `pyo`.
- Create `ConcreteModel()` with sets for nodes and arcs (all ordered pairs `i != j`).
- Add `Var` for each arc with domain `NonNegativeIntegers`.

### Step 2 - Add Constraints and Objective
- Add flow conservation constraints using `Constraint` for each node.
- Add required edge coverage constraints.
- Set objective using `Objective` with `sense=minimize`, summing over all arcs.

### Step 3 - Configure and Solve
- Create solver instance: `SolverFactory("highs")`.
- Set options: `time_limit=[TIME_LIMIT]`, `mip_rel_gap=0.0`, `threads=4`.
- Call `solver.solve(model)` and capture status.

### Step 4 - Extract and Verify Results
- Check `SolverStatus.ok` and `TerminationCondition.optimal` or `feasible`.
- **Verify required edge coverage:** For each `(u,v)` in required edges, ensure `model.x[u,v].value + model.x[v,u].value >= 1`.
- **Verify flow conservation per node** by recomputing inflow and outflow.
- **Verify objective consistency:** Recompute total cost from solution flows and the distance matrix.
- Iterate over all arcs to print non-zero flows for verification.

### Code Usage
```python
import pyomo.environ as pyo

def solve_route_coverage_highs(nodes, required_edges, dist, time_limit=60):
    model = pyo.ConcreteModel()
    model.NODES = pyo.Set(initialize=nodes)
    # Arcs: all ordered pairs i != j
    model.ARCS = pyo.Set(initialize=[(i, j) for i in nodes for j in nodes if i != j], dimen=2)
    
    # Decision variables
    model.x = pyo.Var(model.ARCS, domain=pyo.NonNegativeIntegers)
    
    # Flow conservation
    def flow_conservation_rule(model, k):
        outflow = sum(model.x[k, j] for j in model.NODES if (k, j) in model.ARCS)
        inflow = sum(model.x[i, k] for i in model.NODES if (i, k) in model.ARCS)
        return outflow == inflow
    model.flow_cons = pyo.Constraint(model.NODES, rule=flow_conservation_rule)
    
    # Required edge coverage
    def required_edge_rule(model, u, v):
        return model.x[u, v] + model.x[v, u] >= 1
    model.req_edges = pyo.Constraint(required_edges, rule=required_edge_rule)
    
    # Objective: sum over all arcs
    def obj_rule(model):
        return sum(dist[i][j] * model.x[i, j] for (i, j) in model.ARCS)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)
    
    # Solve
    solver = pyo.SolverFactory("highs")
    solver.options["time_limit"] = time_limit
    solver.options["mip_rel_gap"] = 0.0
    solver.options["threads"] = 4
    result = solver.solve(model, tee=False)
    
    # Check status
    if (result.solver.status == pyo.SolverStatus.ok and 
        result.solver.termination_condition in 
        [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]):
        obj_val = pyo.value(model.obj)
        # Verification checks
        for (u, v) in required_edges:
            if not (pyo.value(model.x[u, v]) + pyo.value(model.x[v, u]) >= 1):
                raise ValueError(f"Required edge ({u},{v}) not covered.")
        # Print non-zero flows
        for (i, j) in model.ARCS:
            val = pyo.value(model.x[i, j])
            if val > 0:
                print(f"Arc ({i}->{j}): {val} traversals")
        return {"status": "OPTIMAL" if result.solver.termination_condition == pyo.TerminationCondition.optimal else "FEASIBLE",
                "objective": obj_val}
    else:
        return {"status": "INFEASIBLE", "objective": None}
```

### Common Pitfalls
- Not checking both `SolverStatus.ok` and termination condition, potentially accepting failed solves.
- Setting `mip_rel_gap` too high, accepting suboptimal solutions when exact optimality is required.
- **Failing to verify required edge coverage and objective consistency**, which can hide model-solution mismatches.
