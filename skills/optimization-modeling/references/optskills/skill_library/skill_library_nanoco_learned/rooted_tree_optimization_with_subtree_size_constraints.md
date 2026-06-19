---
name: Rooted Tree Optimization with Subtree Size Constraints
description: |
  Models and solves minimum-cost rooted tree problems with connectivity and subtree size limits using single-commodity flow formulations, with two solver backends (CBC and GLPK).
---

# Workflow 1 (CBC Flow Formulation)

## Modeling stage

### Strategy Overview
Use a directed single-commodity flow formulation to enforce tree structure, connectivity, and subtree size constraints. Binary variables represent parent-child relationships, while continuous flow variables track subtree sizes and ensure connectivity.

### Step 1 - Define Directed Edge Variables
- Create binary variables `y[i,j]` for each ordered pair `(i,j)` with `i != j`, indicating a directed edge from node `i` to node `j`.
- For undirected graphs, define variables for both directions to allow flexible orientation.

### Step 2 - Enforce Tree Structure via In-Degree
- For each non-root node `j`, require exactly one incoming edge: `sum(y[i,j] for i != j) == 1`.
- For the root node, set all incoming edges to zero: `sum(y[i,root] for i != root) == 0`.

### Step 3 - Add Flow Variables for Connectivity
- Introduce continuous flow variables `f[i,j]` on each directed edge, bounded between `0` and `N-1` (where `N` is total nodes).
- Set root outflow: `sum(f[root,j] for j != root) == N-1`.
- For each non-root node `j`, enforce flow conservation: `sum(f[i,j] for i != j) - sum(f[j,k] for k != j) == 1`.

### Step 4 - Link Flow to Binary Variables
- Use Big-M constraints: `f[i,j] <= (N-1) * y[i,j]` for all directed edges, ensuring flow only exists on selected arcs.

### Step 5 - Apply Subtree Size Constraints
- For each node `j`, the flow on edge `(root,j)` equals the size of the subtree rooted at `j`.
- Constrain: `f[root,j] <= max_subtree_size` for all `j != root`.

### Step 6 - Define Objective
- Minimize total edge cost: `sum(cost[i,j] * (y[i,j] + y[j,i]) for i < j)` to avoid double-counting undirected edges.

### Formulation Template
```json
{
  "sets": ["NODES", "ROOT"],
  "parameters": ["cost[NODES,NODES]", "max_subtree_size"],
  "decision_variables": [
    "y[NODES,NODES] binary",
    "f[NODES,NODES] continuous >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i<j} cost[i,j] * (y[i,j] + y[j,i])"
  },
  "constraints": [
    "sum_{i != j} y[i,j] == 1 for all j != ROOT",
    "sum_{i != ROOT} y[i,ROOT] == 0",
    "sum_{j != ROOT} f[ROOT,j] == N-1",
    "sum_{i != j} f[i,j] - sum_{k != j} f[j,k] == 1 for all j != ROOT",
    "f[i,j] <= (N-1) * y[i,j] for all i,j",
    "f[ROOT,j] <= max_subtree_size for all j != ROOT"
  ]
}
```

### Common Pitfalls
- Forgetting to define flow variables for both directions of each undirected edge, which can cause infeasibility.
- Setting Big-M too large (e.g., `N` instead of `N-1`), weakening the LP relaxation and slowing solver convergence.
- Misapplying subtree size constraints to non-root edges, which is unnecessary and can over-constrain the model.

## Solving stage

### Strategy Overview
Use the CBC solver via Pyomo with a time limit and optimality gap tolerance. Extract the tree structure from binary variable values and validate subtree sizes from flow values.

### Step 1 - Configure Solver
- Set solver to `cbc` with options: `seconds=[TIME_LIMIT]` (e.g., 120) and `ratio=0.0` (zero MIP gap for optimality).
- Enable presolve and multi-threading if available.

### Step 2 - Solve and Check Status
- Call `solver.solve(model)` and check `SolverStatus.ok` and `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- If infeasible, print failure JSON and exit.

### Step 3 - Extract and Verify Solution
- Iterate over all directed edges and select those with `y[i,j].value > 0.5`.
- Verify exactly `N-1` edges are selected.
- Compute subtree sizes from `f[ROOT,j].value` and validate against `max_subtree_size`.
- Reconstruct the tree by following parent-child relationships from `y` variables.

### Step 4 - Output Results
- For successful solves: `print(f"RESULT:{float(pyo.value(model.obj))}")`.
- For failures: `print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'message': '...'})}")`.

### Code Usage
```python
import pyomo.environ as pyo
import json

def build_and_solve(N, cost, root=0, max_subtree=4):
    model = pyo.ConcreteModel()
    model.NODES = pyo.RangeSet(0, N-1)
    model.ROOT = root

    # Decision variables
    model.y = pyo.Var(model.NODES, model.NODES, within=pyo.Binary)
    model.f = pyo.Var(model.NODES, model.NODES, within=pyo.NonNegativeReals, bounds=(0, N-1))

    # Constraints
    def in_degree_rule(m, j):
        if j == root:
            return sum(m.y[i,j] for i in m.NODES if i != j) == 0
        return sum(m.y[i,j] for i in m.NODES if i != j) == 1
    model.in_degree = pyo.Constraint(model.NODES, rule=in_degree_rule)

    def root_flow_rule(m):
        return sum(m.f[root,j] for j in m.NODES if j != root) == N-1
    model.root_flow = pyo.Constraint(rule=root_flow_rule)

    def flow_balance_rule(m, j):
        if j == root:
            return pyo.Constraint.Skip
        inflow = sum(m.f[i,j] for i in m.NODES if i != j)
        outflow = sum(m.f[j,k] for k in m.NODES if k != j)
        return inflow - outflow == 1
    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def big_m_rule(m, i, j):
        return m.f[i,j] <= (N-1) * m.y[i,j]
    model.big_m = pyo.Constraint(model.NODES, model.NODES, rule=big_m_rule)

    def subtree_limit_rule(m, j):
        if j == root:
            return pyo.Constraint.Skip
        return m.f[root,j] <= max_subtree
    model.subtree_limit = pyo.Constraint(model.NODES, rule=subtree_limit_rule)

    # Objective
    def obj_rule(m):
        total = 0
        for i in m.NODES:
            for j in m.NODES:
                if i < j:
                    total += cost[i][j] * (m.y[i,j] + m.y[j,i])
        return total
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve
    solver = pyo.SolverFactory('cbc')
    solver.options["seconds"] = 120
    solver.options["ratio"] = 0.0
    result = solver.solve(model, tee=False)

    # Check status
    if result.solver.status != pyo.SolverStatus.ok or \
       (result.solver.termination_condition != pyo.TerminationCondition.optimal and \
        result.solver.termination_condition != pyo.TerminationCondition.feasible):
        print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'message': 'No feasible solution'})}")
        return

    # Extract edges
    edges = [(i,j) for i in model.NODES for j in model.NODES if i != j and pyo.value(model.y[i,j]) > 0.5]
    # Verification
    assert len(edges) == N-1, f"Expected {N-1} edges, got {len(edges)}"
    for j in model.NODES:
        if j != root:
            size = pyo.value(model.f[root,j])
            assert size <= max_subtree, f"Subtree at {j} has size {size} > {max_subtree}"

    print(f"RESULT:{float(pyo.value(model.obj))}")
    return edges
```

### Common Pitfalls
- Not checking termination condition for feasible (non-optimal) solutions, which may still be acceptable.
- Using `solution_value()` instead of `.value` in Pyomo, causing attribute errors.
- Forgetting to convert cost matrix to a list of lists or dictionary before passing to the model.

# Workflow 2 (GLPK Flow Formulation)

## Modeling stage

### Strategy Overview
Implement the same single-commodity flow formulation using GLPK solver with direct solver options. This workflow emphasizes tighter Big-M tuning and manual post-processing verification.

### Step 1 - Define Directed Binary Variables
- Create binary variables `x[i,j]` for all ordered pairs `(i,j)` with `i != j`, representing directed edges away from the root.

### Step 2 - Enforce Rooted Arborescence
- For each non-root node `j`: `sum(x[i,j] for i != j) == 1`.
- For root node: `sum(x[i,root] for i != root) == 0`.

### Step 3 - Add Continuous Flow Variables
- Define flow variables `f[i,j]` with bounds `[0, N-1]`.
- Root sends `N-1` units: `sum(f[root,j] for j != root) == N-1`.
- Each non-root node consumes 1 unit: `sum(f[i,j] for i != j) - sum(f[j,k] for k != j) == 1`.

### Step 4 - Couple Flow with Binary Variables
- Use tight Big-M: `f[i,j] <= (N-1) * x[i,j]` for all directed edges.

### Step 5 - Subtree Size Constraints
- For each node `j != root`: `f[root,j] <= max_subtree_size`.

### Step 6 - Objective Function
- Minimize `sum(cost[i,j] * (x[i,j] + x[j,i]) for i < j)`.

### Formulation Template
```json
{
  "sets": ["NODES", "ROOT"],
  "parameters": ["cost[NODES,NODES]", "max_subtree_size"],
  "decision_variables": [
    "x[NODES,NODES] binary",
    "f[NODES,NODES] continuous >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{i<j} cost[i,j] * (x[i,j] + x[j,i])"
  },
  "constraints": [
    "sum_{i != j} x[i,j] == 1 for all j != ROOT",
    "sum_{i != ROOT} x[i,ROOT] == 0",
    "sum_{j != ROOT} f[ROOT,j] == N-1",
    "sum_{i != j} f[i,j] - sum_{k != j} f[j,k] == 1 for all j != ROOT",
    "f[i,j] <= (N-1) * x[i,j] for all i,j",
    "f[ROOT,j] <= max_subtree_size for all j != ROOT"
  ]
}
```

### Common Pitfalls
- Using symmetric cost matrix but forgetting to sum both directions in the objective, leading to half the true cost.
- Setting flow bounds too tight (e.g., `N-2` instead of `N-1`), causing infeasibility for larger subtrees.

## Solving stage

### Strategy Overview
Use GLPK solver with time limit and zero MIP gap. Enable presolve for automatic reduction. Post-process to verify tree structure and subtree sizes.

### Step 1 - Configure GLPK Solver
- Set solver options: `tmlim=[TIME_LIMIT]` (e.g., 120 seconds), `mipgap=0.0` (optimality), `presolve=1` (enable presolve).

### Step 2 - Solve and Validate Status
- Call `solver.solve(model)` and check `SolverStatus.ok` and termination condition.
- If not optimal or feasible, output failure JSON.

### Step 3 - Extract and Verify Solution
- Collect edges where `x[i,j].value > 0.5`.
- Verify exactly `N-1` edges form a connected tree.
- Validate each root-child subtree size using `f[root,j].value <= max_subtree_size`.

### Step 4 - Output with Verification
- Print objective value for successful solves.
- Optionally print selected edges and subtree sizes for debugging.

### Code Usage
```python
import pyomo.environ as pyo
import json

def solve_with_glpk(N, cost, root=0, max_subtree=4):
    model = pyo.ConcreteModel()
    model.NODES = pyo.RangeSet(0, N-1)
    model.ROOT = root

    # Variables
    model.x = pyo.Var(model.NODES, model.NODES, within=pyo.Binary)
    model.f = pyo.Var(model.NODES, model.NODES, within=pyo.NonNegativeReals, bounds=(0, N-1))

    # Constraints
    def in_degree_rule(m, j):
        if j == root:
            return sum(m.x[i,j] for i in m.NODES if i != j) == 0
        return sum(m.x[i,j] for i in m.NODES if i != j) == 1
    model.in_degree = pyo.Constraint(model.NODES, rule=in_degree_rule)

    def root_flow_rule(m):
        return sum(m.f[root,j] for j in m.NODES if j != root) == N-1
    model.root_flow = pyo.Constraint(rule=root_flow_rule)

    def flow_balance_rule(m, j):
        if j == root:
            return pyo.Constraint.Skip
        inflow = sum(m.f[i,j] for i in m.NODES if i != j)
        outflow = sum(m.f[j,k] for k in m.NODES if k != j)
        return inflow - outflow == 1
    model.flow_balance = pyo.Constraint(model.NODES, rule=flow_balance_rule)

    def big_m_rule(m, i, j):
        return m.f[i,j] <= (N-1) * m.x[i,j]
    model.big_m = pyo.Constraint(model.NODES, model.NODES, rule=big_m_rule)

    def subtree_limit_rule(m, j):
        if j == root:
            return pyo.Constraint.Skip
        return m.f[root,j] <= max_subtree
    model.subtree_limit = pyo.Constraint(model.NODES, rule=subtree_limit_rule)

    # Objective
    def obj_rule(m):
        total = 0
        for i in m.NODES:
            for j in m.NODES:
                if i < j:
                    total += cost[i][j] * (m.x[i,j] + m.x[j,i])
        return total
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve with GLPK
    solver = pyo.SolverFactory('glpk')
    solver.options["tmlim"] = 120
    solver.options["mipgap"] = 0.0
    solver.options["presolve"] = 1
    result = solver.solve(model, tee=False)

    # Status check
    if result.solver.status != pyo.SolverStatus.ok or \
       (result.solver.termination_condition != pyo.TerminationCondition.optimal and \
        result.solver.termination_condition != pyo.TerminationCondition.feasible):
        print(f"RESULT_JSON:{json.dumps({'status': 'failed', 'message': 'No feasible solution'})}")
        return

    # Extract and verify
    edges = [(i,j) for i in model.NODES for j in model.NODES if i != j and pyo.value(model.x[i,j]) > 0.5]
    assert len(edges) == N-1, f"Expected {N-1} edges, got {len(edges)}"
    
    # Verify subtree sizes
    for j in model.NODES:
        if j != root:
            size = pyo.value(model.f[root,j])
            assert size <= max_subtree, f"Subtree at {j} has size {size} > {max_subtree}"

    print(f"RESULT:{float(pyo.value(model.obj))}")
    return edges
```

### Common Pitfalls
- GLPK may return `feasible` without `optimal` for some instances; always accept feasible solutions if optimal is not required.
- Presolve may eliminate variables; verify that all expected constraints are still present after presolve.
- GLPK's `mipgap` option expects a fraction (e.g., 0.05 for 5% gap), not a percentage.
