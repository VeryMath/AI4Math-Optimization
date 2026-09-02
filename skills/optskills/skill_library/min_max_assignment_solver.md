---
name: Min-Max Assignment Solver
description: |
  Solves one-to-one matching problems with a min-max (makespan) objective by formulating it as a Mixed-Integer Linear Program (MILP) and using a high-performance solver, with verification via feasibility checks.

---
# Workflow 1 (CP-SAT with Big-M Linearization)

## Modeling stage

### Strategy Overview
Formulate the min-max assignment problem for a CP-SAT solver by linearizing the maximum cost constraint using a big-M formulation. This approach is effective for solvers that handle linear constraints well but do not natively support variable multiplication.

### Step 1 - Define Core Variables
- Declare binary assignment variables `x[i][j]` for each agent i and task j.
- Declare an integer variable `max_cost` to represent the objective value to minimize. Set its lower bound to 0 and upper bound to a sufficiently large constant `M`.

### Step 2 - Enforce Assignment Constraints
- Add constraints `sum(x[i][j] for j in tasks) == 1` for each agent i.
- Add constraints `sum(x[i][j] for i in agents) == 1` for each task j.

### Step 3 - Link Max Cost to Assignments via Big-M
- For each pair (i, j), add a linear constraint: `max_cost >= cost[i][j] - M * (1 - x[i][j])`.
- Choose `M` as a sufficiently large number (e.g., `max(cost_matrix) + 1`) to deactivate the constraint when `x[i][j] = 0`. Setting `M` too small may cut off valid solutions; setting it excessively large can cause numerical instability.

### Formulation Template
```json
{
  "sets": ["agents", "tasks"],
  "parameters": ["cost[agents][tasks]"],
  "decision_variables": [
    {"name": "x", "indices": ["agents", "tasks"], "type": "binary"},
    {"name": "max_cost", "type": "integer", "bounds": [0, "M"]}
  ],
  "objective": {
    "sense": "min",
    "expression": "max_cost"
  },
  "constraints": [
    "assignment_agent[i in agents]: sum(x[i][j] for j in tasks) == 1",
    "assignment_task[j in tasks]: sum(x[i][j] for i in agents) == 1",
    "max_cost_link[i in agents][j in tasks]: max_cost >= cost[i][j] - M * (1 - x[i][j])"
  ]
}
```

### Common Pitfalls
- Setting `M` too small, which may cut off valid solutions.
- Setting `M` excessively large, which can cause numerical instability in the solver.
- Forgetting to define `max_cost` as an integer variable when costs are integral, leading to unnecessary continuous relaxation.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver to find the optimal min-max assignment. Configure it for optimality and use a secondary feasibility model to verify the optimality gap.

### Step 1 - Configure Solver for Optimality
- Set `solver.parameters.max_time_in_seconds` to control runtime.
- Set `solver.parameters.num_search_workers` for parallelism.
- Set `solver.parameters.random_seed` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to enforce optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check the status is `OPTIMAL` or `FEASIBLE`. Handle `INFEASIBLE` or `UNKNOWN` statuses with appropriate logging.

### Step 3 - Verify Optimality via Feasibility Check
- Let `V` be the objective value from the solution.
- Create a new feasibility model with the same assignment constraints.
- Add constraints `cost[i][j] * x[i][j] <= V - 1` for all i, j (or use the big-M form: `max_cost >= cost[i][j] - M * (1 - x[i][j])` and set `max_cost <= V - 1`).
- Solve the feasibility model. If it is infeasible, `V` is proven optimal.

### Step 4 - Extract and Validate Solution
- Retrieve the assignment by iterating over `x[i][j]` variables and checking if `solver.Value(x[i][j]) == 1`.
- Compute the actual maximum cost from the assignment and verify it matches the solver's `max_cost` value.

### Code Usage
```python
# Build model from formulation
model = cp_model.CpModel()
x = {}
for i in agents:
    for j in tasks:
        x[i, j] = model.NewBoolVar(f"x_{i}_{j}")
max_cost = model.NewIntVar(0, M, "max_cost")

# Assignment constraints
for i in agents:
    model.Add(sum(x[i, j] for j in tasks) == 1)
for j in tasks:
    model.Add(sum(x[i, j] for i in agents) == 1)

# Big-M linking constraints
for i in agents:
    for j in tasks:
        model.Add(max_cost >= cost[i][j] - M * (1 - x[i, j]))

# Objective
model.Minimize(max_cost)

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
solver.parameters.relative_gap_limit = 0.0
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    assignment = {i: j for i in agents for j in tasks if solver.Value(x[i, j]) == 1}
    # Verification and output
else:
    # Handle infeasible or unknown status
```

### Common Pitfalls
- Not checking solver status before extracting values, leading to runtime errors.
- Using an incorrect threshold (e.g., `V - epsilon` with inappropriate `epsilon`) in the feasibility check, causing false infeasibility.
- Assuming the solver's objective value is integral; use integer variable for `max_cost` when costs are integers.

# Workflow 2 (Pyomo with Direct Multiplication)

## Modeling stage

### Strategy Overview
Formulate the problem in Pyomo using direct multiplication of binary variables and cost parameters within constraints. This declarative approach leverages Pyomo's ability to handle bilinear terms (binary * parameter) and is suitable for MILP solvers.

### Step 1 - Define Model Structure
- Create a `ConcreteModel()`.
- Define sets for `agents` and `tasks`.
- Define a `Param` for the `cost` matrix.

### Step 2 - Declare Decision Variables
- Define binary variables `x[i, j]` over the cross product of agents and tasks.
- Define a continuous, non-negative variable `max_cost`.

### Step 3 - Enforce Assignment and Max Cost Constraints
- Add constraints ensuring each agent is assigned to exactly one task and each task gets exactly one agent.
- Add constraints `max_cost >= cost[i, j] * x[i, j]` for all i, j. Pyomo will linearize this product for MILP solvers.

### Formulation Template
```json
{
  "sets": ["agents", "tasks"],
  "parameters": ["cost[agents][tasks]"],
  "decision_variables": [
    {"name": "x", "indices": ["agents", "tasks"], "type": "binary"},
    {"name": "max_cost", "type": "continuous", "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "min",
    "expression": "max_cost"
  },
  "constraints": [
    "assign_agent[i in agents]: sum(x[i, j] for j in tasks) == 1",
    "assign_task[j in tasks]: sum(x[i, j] for i in agents) == 1",
    "max_cost_def[i in agents][j in tasks]: max_cost >= cost[i, j] * x[i, j]"
  ]
}
```

### Common Pitfalls
- Forgetting to initialize the `cost` parameter, leading to an incomplete model.
- Defining `max_cost` without a proper domain, which may allow negative values.
- Assuming the solver automatically linearizes the product; some solvers may require explicit linearization hints.

## Solving stage

### Strategy Overview
Use a high-performance MILP solver (e.g., Gurobi, HiGHS) via Pyomo's `SolverFactory`. Configure for deterministic optimization and use a binary search on cost thresholds for optimality verification.

### Step 1 - Select and Configure Solver
- Instantiate the solver: `solver = SolverFactory('solver_name')`.
- Set options: `time_limit` for runtime, `mip_gap=0.0` for optimality, `threads` for parallelism, and `seed` for reproducibility.

### Step 2 - Solve and Inspect Termination Condition
- Call `results = solver.solve(model, tee=False)`.
- Check `results.solver.status` and `results.solver.termination_condition`. Proceed only if status is `ok` and termination is `optimal` or `feasible`.

### Step 3 - Verify Optimality via Binary Search
- Let `candidate_value` be the objective value from the solution.
- Perform a binary search on the discrete set of possible cost values.
- For a test threshold `T`, create a feasibility model with assignment constraints and additional constraints: `x[i, j] == 0` for all pairs where `cost[i][j] > T`.
- Solve the feasibility model. The smallest `T` for which a feasible assignment exists is the optimal makespan.

### Step 4 - Extract and Present Solution
- Retrieve the assignment by iterating over `x[i, j]` and checking `pyo.value(x[i, j]) > 0.5`.
- Output the assignment mapping and the confirmed optimal makespan.

### Code Usage
```python
# Build model from formulation
import pyomo.environ as pyo
model = pyo.ConcreteModel()
model.agents = pyo.Set(initialize=agents)
model.tasks = pyo.Set(initialize=tasks)
model.cost = pyo.Param(model.agents, model.tasks, initialize=cost_data)
model.x = pyo.Var(model.agents, model.tasks, domain=pyo.Binary)
model.max_cost = pyo.Var(domain=pyo.NonNegativeReals)

def assign_agent_rule(m, i):
    return sum(m.x[i, j] for j in m.tasks) == 1
model.assign_agent = pyo.Constraint(model.agents, rule=assign_agent_rule)

def assign_task_rule(m, j):
    return sum(m.x[i, j] for i in m.agents) == 1
model.assign_task = pyo.Constraint(model.tasks, rule=assign_task_rule)

def max_cost_rule(m, i, j):
    return m.max_cost >= m.cost[i, j] * m.x[i, j]
model.max_cost_def = pyo.Constraint(model.agents, model.tasks, rule=max_cost_rule)

model.obj = pyo.Objective(expr=model.max_cost, sense=pyo.minimize)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
solver.options['mip_rel_gap'] = 0.0
results = solver.solve(model, tee=False)

if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition == pyo.TerminationCondition.optimal:
    # Extract solution
    assignment = {i: j for i in model.agents for j in model.tasks if pyo.value(model.x[i, j]) > 0.5}
    # Verification and output
else:
    # Handle other statuses
```

### Common Pitfalls
- Not setting `load_solutions=False` when performing feasibility checks, which can cause errors if the model is infeasible.
- Using `pyo.value()` on variables before ensuring a solution is loaded.
- Overlooking the need to convert the cost matrix into a Pyomo `Param` dictionary correctly.
