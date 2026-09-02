---
name: Assignment Problem with Surplus Resources
description: |
  Model and solve rectangular assignment problems (more agents than tasks) with binary assignment variables, cardinality limits, and a linear cost minimization objective using either a direct MIP formulation or a network flow transformation.
---

# Workflow 1 (Direct MIP Formulation)

## Modeling stage

### Strategy Overview
Model the problem directly as a Mixed-Integer Program (MIP) using binary decision variables for each potential assignment. This approach is intuitive, flexible, and directly encodes the cardinality constraints on both sets.

### Step 1 - Define Sets and Parameters
- Define the set of agents `A` (e.g., workers, machines) and the set of tasks `T` (e.g., jobs, documents). The cardinality of `A` is greater than that of `T`.
- Define a cost parameter `c_{a,t}` representing the cost of assigning agent `a` to task `t`. Store this as a 2D array or dictionary.

### Step 2 - Create Decision Variables
- Create a binary decision variable `x_{a,t}` for each agent `a` in `A` and each task `t` in `T`.
- `x_{a,t} = 1` indicates agent `a` is assigned to task `t`; `0` otherwise.

### Step 3 - Formulate Task Coverage Constraints
- For each task `t` in `T`, add a constraint `∑_{a ∈ A} x_{a,t} = 1`. This ensures every task is assigned to exactly one agent.

### Step 4 - Formulate Agent Capacity Constraints
- For each agent `a` in `A`, add a constraint `∑_{t ∈ T} x_{a,t} ≤ 1`. This enforces that each agent can be assigned to at most one task.

### Step 5 - Define Objective Function
- Formulate the objective to minimize total assignment cost: `min ∑_{a ∈ A} ∑_{t ∈ T} c_{a,t} * x_{a,t}`.

### Formulation Template
```json
{
  "sets": [
    "A: Set of agents (size n, where n > m).",
    "T: Set of tasks (size m)."
  ],
  "parameters": [
    "c_{a,t}: Cost of assigning agent a to task t."
  ],
  "decision_variables": [
    "x_{a,t} ∈ {0, 1}: Binary assignment variable."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{a ∈ A} ∑_{t ∈ T} c_{a,t} * x_{a,t}"
  },
  "constraints": [
    "Task Coverage: ∑_{a ∈ A} x_{a,t} = 1, ∀ t ∈ T",
    "Agent Capacity: ∑_{t ∈ T} x_{a,t} ≤ 1, ∀ a ∈ A"
  ]
}
```

### Common Pitfalls
- Forgetting that the agent set must be larger than the task set for a valid rectangular assignment; otherwise, the `Agent Capacity` constraints may make the model infeasible.
- Using `== 1` for the agent capacity constraint, which would force all agents to be assigned, incorrectly modeling a perfect matching instead of a surplus resource scenario.

## Solving stage

### Strategy Overview
Solve the MIP model using a dedicated integer programming solver via a modeling library (e.g., OR-Tools, PuLP). Configure solver settings for performance and implement robust solution status checking and result extraction.

### Step 1 - Initialize Solver and Model
- Instantiate a MIP solver (e.g., `SCIP`, `CBC` via OR-Tools' `pywraplp`).
- Optionally set performance parameters: time limit, relative optimality gap, and number of threads.

### Step 2 - Instantiate Variables and Add Constraints
- Create binary variables using loops over sets `A` and `T`.
- Add the task coverage and agent capacity constraints using summation over the created variables.

### Step 3 - Set Objective and Solve
- Build the linear objective function by setting coefficients for each variable.
- Call the solver's `Solve()` method.

### Step 4 - Check Status and Extract Solution
- Check the solver status (`OPTIMAL`, `FEASIBLE`). Handle non-optimal statuses (e.g., `INFEASIBLE`, `UNBOUNDED`) with appropriate error messages.
- If optimal or feasible, extract the objective value.
- Iterate over all variables, collecting assignments where the solution value is greater than a threshold (e.g., 0.5).

### Code Usage
```python
# Example using OR-Tools
from ortools.linear_solver import pywraplp

# Data placeholders
agents = list(range(num_agents))  # n
tasks = list(range(num_tasks))    # m (n > m)
cost = {(a, t): cost_value for a in agents for t in tasks}  # Define your cost matrix

# 1. Initialize Solver
solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver not available.")

# Optional: Set solver parameters
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# 2. Create Variables
x = {}
for a in agents:
    for t in tasks:
        x[a, t] = solver.IntVar(0, 1, f"x_{a}_{t}")

# 3. Add Constraints
# Task coverage: each task assigned to exactly one agent
for t in tasks:
    solver.Add(solver.Sum([x[a, t] for a in agents]) == 1)
# Agent capacity: each agent assigned to at most one task
for a in agents:
    solver.Add(solver.Sum([x[a, t] for t in tasks]) <= 1)

# 4. Set Objective
objective = solver.Objective()
for a in agents:
    for t in tasks:
        objective.SetCoefficient(x[a, t], cost[a, t])
objective.SetMinimization()

# 5. Solve
status = solver.Solve()

# 6. Check Status and Extract Solution
if status in (solver.OPTIMAL, solver.FEASIBLE):
    total_cost = objective.Value()
    assignments = []
    for a in agents:
        for t in tasks:
            if x[a, t].solution_value() > 0.5:
                assignments.append((a, t))
    print(f"Total cost: {total_cost}")
    print(f"Assignments: {assignments}")
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Using a loose optimality gap (`mip_rel_gap`) when an exact optimal solution is required; set it to `0.0` for exact MIP solving.

# Workflow 2 (Network Flow Transformation)

## Modeling stage

### Strategy Overview
Reformulate the assignment problem as a minimum-cost flow problem on a bipartite network. This leverages specialized, often more efficient, network flow algorithms and provides an alternative solving pathway.

### Step 1 - Define Network Structure
- Model the problem as a directed graph with nodes: a source (`S`), agent nodes (`A`), task nodes (`T`), and a sink (`K`).
- Define arcs: `S → A` (capacity 1, cost 0), `A → T` (capacity 1, cost = `c_{a,t}`), `T → K` (capacity 1, cost 0).

### Step 2 - Define Supplies and Demands
- Set the supply at the source node equal to the number of tasks `|T|` (or `m`).
- Set the demand at the sink node equal to `-|T|`.
- Set the supply/demand for all other nodes (agents and tasks) to 0.

### Step 3 - Map Flow to Assignment
- The flow on arc `(a, t)` from the agent layer to the task layer corresponds to the binary assignment variable `x_{a,t}`. A flow of 1 indicates assignment.

### Formulation Template
```json
{
  "sets": [
    "A: Set of agent nodes.",
    "T: Set of task nodes."
  ],
  "parameters": [
    "c_{a,t}: Cost per unit flow on arc from agent a to task t."
  ],
  "decision_variables": [
    "f_{a,t}: Flow on arc from agent a to task t (integer, 0 or 1)."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{a ∈ A} ∑_{t ∈ T} c_{a,t} * f_{a,t}"
  },
  "constraints": [
    "Flow Conservation at Agent a: f_{S→a} = ∑_{t ∈ T} f_{a,t}, ∀ a ∈ A",
    "Flow Conservation at Task t: ∑_{a ∈ A} f_{a,t} = f_{t→K}, ∀ t ∈ T",
    "Source Supply: ∑_{a ∈ A} f_{S→a} = |T|",
    "Sink Demand: ∑_{t ∈ T} f_{t→K} = |T|",
    "Arc Capacities: 0 ≤ f_{a,t} ≤ 1, 0 ≤ f_{S→a} ≤ 1, 0 ≤ f_{t→K} ≤ 1"
  ]
}
```

### Common Pitfalls
- Incorrectly setting node supplies/demands, which can lead to infeasibility. The total supply must equal total demand.
- Forgetting that the `S→A` and `T→K` arcs also have capacity 1, which enforces the agent and task cardinality limits.

## Solving stage

### Strategy Overview
Use a dedicated minimum-cost flow solver (e.g., OR-Tools `SimpleMinCostFlow`) to find the optimal flow. Construct the network by adding arcs with capacities and costs, set node supplies, and solve.

### Step 1 - Initialize Flow Solver and Graph
- Create an instance of a min-cost flow solver.
- Prepare data structures to map your original agent/task indices to the solver's internal node indices.

### Step 2 - Add Arcs and Set Parameters
- Add arcs in three layers: source-to-agents, agents-to-tasks, and tasks-to-sink.
- For each arc, specify its start node, end node, capacity, and unit cost.
- Set the supply for each node (positive for source, negative for sink, zero for others).

### Step 3 - Solve and Check Optimality
- Invoke the solver's `Solve()` or equivalent method.
- Verify the solver status is `OPTIMAL`. Handle other statuses (e.g., `INFEASIBLE`) appropriately.

### Step 4 - Extract Assignments from Flow
- Iterate over all arcs. Identify arcs that carry positive flow (flow > 0.5) and connect an agent node to a task node.
- Map these arcs back to the original agent and task indices to obtain the assignment pairs.
- Calculate the total cost from the solver's objective or by summing `cost * flow` for the assignment arcs.

### Code Usage
```python
# Example using OR-Tools MinCostFlow
from ortools.graph.python import min_cost_flow

# Data placeholders
agents = list(range(num_agents))
tasks = list(range(num_tasks))
cost = {(a, t): cost_value for a in agents for t in tasks}

# 1. Initialize Solver
smcf = min_cost_flow.SimpleMinCostFlow()

# Define node indices
source = 0
sink = 1
agent_nodes = {a: 2 + a for a in agents}          # e.g., 2, 3, ...
task_nodes = {t: 2 + len(agents) + t for t in tasks} # e.g., 2+n, 2+n+1, ...

# 2. Add Arcs and Set Supplies
# Arcs from source to each agent (capacity 1, cost 0)
for a in agents:
    smcf.add_arc_with_capacity_and_unit_cost(
        source, agent_nodes[a], 1, 0
    )

# Arcs from each agent to each task (capacity 1, cost = c[a,t])
for a in agents:
    for t in tasks:
        smcf.add_arc_with_capacity_and_unit_cost(
            agent_nodes[a], task_nodes[t], 1, cost[a, t]
        )

# Arcs from each task to sink (capacity 1, cost 0)
for t in tasks:
    smcf.add_arc_with_capacity_and_unit_cost(
        task_nodes[t], sink, 1, 0
    )

# Set node supplies
smcf.set_node_supply(source, len(tasks))   # Supply = number of tasks
smcf.set_node_supply(sink, -len(tasks))    # Demand = - (number of tasks)
for a in agents:
    smcf.set_node_supply(agent_nodes[a], 0)
for t in tasks:
    smcf.set_node_supply(task_nodes[t], 0)

# 3. Solve
status = smcf.solve()

# 4. Check Status and Extract Solution
if status == smcf.OPTIMAL:
    total_cost = smcf.optimal_cost()
    assignments = []
    for arc in range(smcf.num_arcs()):
        if smcf.flow(arc) > 0:
            tail = smcf.tail(arc)
            head = smcf.head(arc)
            # Check if arc connects an agent node to a task node
            if tail in agent_nodes.values() and head in task_nodes.values():
                # Map node indices back to original IDs
                a = [k for k, v in agent_nodes.items() if v == tail][0]
                t = [k for k, v in task_nodes.items() if v == head][0]
                assignments.append((a, t))
    print(f"Total cost: {total_cost}")
    print(f"Assignments: {assignments}")
else:
    print(f"Solver returned non-optimal status: {status}")
```

### Common Pitfalls
- Mismatching node indices when adding arcs or setting supplies, leading to an incorrect network topology.
- Assuming all arcs with positive flow are assignment arcs; must filter for arcs connecting the agent and task layers only, ignoring source-agent and task-sink arcs.
