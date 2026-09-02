---
name: Minimum Cut via Binary Partition
description: |
  Formulate and solve the minimum s-t cut problem using either a mixed-integer linear programming (MIP) approach with explicit binary partition variables or a max-flow reduction using the max-flow min-cut theorem.

---
# Workflow 1 (MIP with Binary Partition Variables)

## Modeling stage

### Strategy Overview
Model the minimum cut problem directly by assigning each node to one of two partitions (S or T) using binary variables. The cut capacity is linearized via auxiliary continuous variables, resulting in a mixed-integer linear program that can be solved with any standard MIP solver.

### Step 1 - Define Node Partition Variables
- Introduce a binary variable `x[i]` for each node `i` in the set of nodes `N`.
- Set `x[i] = 1` if node `i` belongs to the source side (S), and `x[i] = 0` if it belongs to the sink side (T).

### Step 2 - Fix Source and Sink Membership
- Add a constraint `x[source] == 1` to enforce that the source node is in S.
- Add a constraint `x[sink] == 0` to enforce that the sink node is in T.

### Step 3 - Linearize Cut Indicator
- For each directed arc `(i, j)` in the set of arcs `A`, introduce a continuous auxiliary variable `y[i,j] >= 0`.
- Add constraints `y[i,j] >= x[i] - x[j]` for all arcs `(i,j)`. This ensures `y[i,j] = 1` when the arc crosses from S to T (i.e., `x[i]=1` and `x[j]=0`), and `y[i,j] = 0` otherwise due to the minimization objective.

### Step 4 - Define Objective
- Minimize the total cut capacity: `minimize sum(capacity[i,j] * y[i,j] for all arcs (i,j) in A)`.

### Formulation Template
```json
{
  "sets": ["N: set of nodes", "A: set of directed arcs (i,j)"],
  "parameters": ["source: source node index", "sink: sink node index", "capacity[i,j]: capacity of arc (i,j) for (i,j) in A"],
  "decision_variables": [
    "x[i] in {0,1} for i in N: 1 if node i is in S, 0 if in T",
    "y[i,j] >= 0 for (i,j) in A: cut indicator variable"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(capacity[i,j] * y[i,j] for (i,j) in A)"
  },
  "constraints": [
    "x[source] == 1",
    "x[sink] == 0",
    "y[i,j] >= x[i] - x[j] for all (i,j) in A"
  ]
}
```

### Common Pitfalls
- Forgetting to enforce `x[source] == 1` and `x[sink] == 0`, which can lead to trivial cuts (e.g., all nodes in S or all in T).
- Omitting the non-negativity constraint on `y[i,j]`, which may cause the solver to assign negative values.
- Using a large number of arcs without considering that the LP relaxation is naturally integral due to total unimodularity; a pure LP solver may suffice.

## Solving stage

### Strategy Overview
Solve the MIP formulation using a standard MIP solver (e.g., CBC, GLPK, or Gurobi) via Pyomo. The problem is totally unimodular, so the LP relaxation yields integer solutions, but a MIP solver is used for robustness.

### Step 1 - Build the Model in Pyomo
- Import `pyomo.environ` as `pyo`.
- Create a `ConcreteModel` and define sets `N` and `A` from the input data.
- Declare binary variables `x` indexed over `N` and continuous non-negative variables `y` indexed over `A`.
- Add constraints for source/sink fixation and cut linearization.
- Set the objective expression.

### Step 2 - Configure and Solve
- Instantiate a solver (e.g., `SolverFactory('cbc')` or `SolverFactory('glpk')`).
- Set solver options: `mipgap = 0.0` for optimality, `seconds = [TIME_LIMIT]` for a time limit.
- Call `solver.solve(model, tee=False)` and capture the results object.

### Step 3 - Extract and Validate Results
- Check `results.solver.status` and `results.solver.termination_condition`; only proceed if status is `ok` and termination is `optimal` or `feasible`.
- Retrieve the objective value via `pyo.value(model.objective)`.
- Extract the partition: nodes with `pyo.value(x[i]) > 0.5` are in S; others are in T.
- Verify the cut by iterating over arcs and summing capacities where `x[i] > 0.5` and `x[j] < 0.5`. This sum must equal the objective value.

### Code Usage
```python
import pyomo.environ as pyo

def solve_min_cut_milp(nodes, arcs, source, sink, capacities):
    model = pyo.ConcreteModel()
    model.N = pyo.Set(initialize=nodes)
    model.A = pyo.Set(initialize=arcs, dimen=2)

    model.x = pyo.Var(model.N, domain=pyo.Binary)
    model.y = pyo.Var(model.A, domain=pyo.NonNegativeReals)

    # Fix source and sink
    model.fix_source = pyo.Constraint(expr=model.x[source] == 1)
    model.fix_sink = pyo.Constraint(expr=model.x[sink] == 0)

    # Cut linearization constraints
    def cut_rule(m, i, j):
        return m.y[i, j] >= m.x[i] - m.x[j]
    model.cut_constr = pyo.Constraint(model.A, rule=cut_rule)

    # Objective
    model.obj = pyo.Objective(
        expr=sum(capacities[(i, j)] * model.y[i, j] for (i, j) in model.A),
        sense=pyo.minimize
    )

    solver = pyo.SolverFactory('cbc')
    solver.options['mipgap'] = 0.0
    solver.options['seconds'] = 30
    results = solver.solve(model, tee=False)

    if results.solver.status != pyo.SolverStatus.ok:
        raise RuntimeError(f"Solver failed: {results.solver.status}")
    if results.solver.termination_condition not in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible):
        raise RuntimeError(f"No feasible solution: {results.solver.termination_condition}")

    cut_value = pyo.value(model.obj)
    S = [i for i in model.N if pyo.value(model.x[i]) > 0.5]
    T = [i for i in model.N if pyo.value(model.x[i]) < 0.5]
    cut_arcs = [(i, j) for (i, j) in model.A if pyo.value(model.x[i]) > 0.5 and pyo.value(model.x[j]) < 0.5]

    # Verification
    computed_cut_value = sum(capacities[(i, j)] for (i, j) in cut_arcs)
    if abs(cut_value - computed_cut_value) > 1e-6:
        raise RuntimeError(f"Cut verification failed: objective {cut_value} != computed cut {computed_cut_value}")

    return {"status": "success", "cut_value": cut_value, "S": S, "T": T, "cut_arcs": cut_arcs}
```

### Common Pitfalls
- Not checking solver status before reading results, leading to runtime errors from uninitialized variables.
- Using a solver that does not support binary variables (e.g., pure LP solver) without verifying integrality.
- Setting an overly tight time limit that prevents the solver from reaching optimality for large networks.

# Workflow 2 (Max-Flow Reduction)

## Modeling stage

### Strategy Overview
Apply the max-flow min-cut theorem: the minimum s-t cut capacity equals the maximum flow from source to sink. Model the problem as a flow network and compute the maximum flow using a dedicated max-flow algorithm, avoiding explicit binary variables.

### Step 1 - Define the Flow Network
- Represent the directed graph with nodes indexed from 0 to N-1, where the source is node `source` and the sink is node `sink`.
- Each directed arc `(i, j)` has a capacity `capacity[i,j]`. Only capacities are needed; ignore any extraneous costs.

### Step 2 - Formulate as Maximum Flow
- The objective is to maximize the flow from source to sink subject to capacity constraints and flow conservation at intermediate nodes.
- The maximum flow value directly gives the minimum cut capacity.

### Step 3 - Implicit Partition via Residual Graph
- After computing the maximum flow, the partition (S, T) is determined by reachability from the source in the residual graph.
- Nodes reachable from the source via arcs with positive residual capacity belong to S; all others belong to T.

### Formulation Template
```json
{
  "sets": ["N: set of nodes", "A: set of directed arcs (i,j)"],
  "parameters": ["source: source node index", "sink: sink node index", "capacity[i,j]: capacity of arc (i,j) for (i,j) in A"],
  "decision_variables": ["flow[i,j] >= 0 for (i,j) in A: flow on each arc"],
  "objective": {
    "sense": "max",
    "expression": "net flow out of source"
  },
  "constraints": [
    "flow[i,j] <= capacity[i,j] for all (i,j) in A",
    "sum(flow[i,j] for j) - sum(flow[j,i] for j) == 0 for all i not in {source, sink}"
  ]
}
```

### Common Pitfalls
- Assuming the graph is undirected; the formulation requires directed arcs. For undirected edges, replace each with two directed arcs of equal capacity.
- Forgetting that the max-flow min-cut theorem applies only to a single source-sink pair; multi-source/multi-sink problems require a super-source/super-sink transformation.
- Using a solver that does not handle integer capacities correctly; max-flow algorithms work with integer or floating-point capacities.

## Solving stage

### Strategy Overview
Use a dedicated max-flow solver (e.g., OR-Tools' `SimpleMaxFlow`) to compute the maximum flow efficiently. The solver handles the flow conservation and capacity constraints internally, returning the maximum flow value and enabling partition extraction via residual graph traversal.

### Step 1 - Build the Max-Flow Solver
- Import `SimpleMaxFlow` from `ortools.graph.python.max_flow`.
- Create a `SimpleMaxFlow` object.
- For each directed arc `(i, j)` with capacity `c`, call `solver.add_arc_with_capacity(i, j, c)`.

### Step 2 - Solve and Check Status
- Call `solver.solve(source, sink)`.
- Check that the return status is `solver.OPTIMAL`; otherwise, the problem is infeasible or unbounded.

### Step 3 - Extract Results
- Retrieve the maximum flow value via `solver.optimal_flow()`, which equals the minimum cut capacity.
- Extract the partition by performing a BFS/DFS on the residual graph: start from the source, traverse forward arcs where `solver.capacity(tail, head) - solver.flow(tail, head) > 0` and backward arcs where `solver.flow(head, tail) > 0`. Nodes reachable form S; the rest form T.
- Verify the cut by summing capacities of arcs from S to T; this sum must equal the max flow value.

### Code Usage
```python
from ortools.graph.python.max_flow import SimpleMaxFlow
from collections import deque

def solve_min_cut_maxflow(nodes, arcs, source, sink, capacities):
    smf = SimpleMaxFlow()
    for (i, j) in arcs:
        smf.add_arc_with_capacity(i, j, capacities[(i, j)])

    status = smf.solve(source, sink)
    if status != smf.OPTIMAL:
        raise RuntimeError(f"Max flow solver failed with status {status}")

    max_flow = smf.optimal_flow()

    # Extract partition via BFS on residual graph
    S = set([source])
    queue = deque([source])
    while queue:
        node = queue.popleft()
        for arc in range(smf.num_arcs()):
            tail = smf.tail(arc)
            head = smf.head(arc)
            if tail == node and head not in S:
                if smf.capacity(arc) - smf.flow(arc) > 0:  # residual capacity
                    S.add(head)
                    queue.append(head)
            if head == node and tail not in S:
                if smf.flow(arc) > 0:  # reverse flow
                    S.add(tail)
                    queue.append(tail)

    T = [n for n in nodes if n not in S]
    cut_arcs = [(i, j) for (i, j) in arcs if i in S and j not in S]
    cut_value = sum(capacities[(i, j)] for (i, j) in cut_arcs)

    # Verification: cut value should equal max flow
    if abs(cut_value - max_flow) > 1e-6:
        raise RuntimeError(f"Cut verification failed: cut value {cut_value} != max flow {max_flow}")

    return {"status": "success", "cut_value": cut_value, "S": list(S), "T": T, "cut_arcs": cut_arcs}
```

### Common Pitfalls
- Not handling the case where the source and sink are the same node; the solver may return zero flow.
- Assuming the residual graph traversal is symmetric; always check both forward and backward arcs.
- Using `solver.num_arcs()` incorrectly if arcs were added dynamically; ensure all arcs are added before solving.
