---
name: Generalized Bin Packing / Container Minimization
description: |
  Model and solve assignment problems where items must be assigned to containers with capacity limits, minimizing the number of containers used, using binary assignment and container usage variables.
---

# Workflow 1 (MILP with Pyomo and CBC/Gurobi)

## Modeling stage

### Strategy Overview
This workflow formulates the problem as a Mixed-Integer Linear Program (MILP) using the Pyomo modeling language, suitable for open-source (CBC) or commercial (Gurobi) solvers. It emphasizes a clear separation of assignment and activation variables with capacity constraints deactivated for unused containers.

### Step 1 - Define Sets and Parameters
- Define the set of items and the set of containers (which can be pre-defined or generated as an upper bound).
- Define parameters for item weights and container capacity.

### Step 2 - Create Decision Variables
- Create binary assignment variables `x[i, j]` for each item `i` and container `j`.
- Create binary container usage variables `y[j]` for each container `j`.

### Step 3 - Formulate Constraints
- Add assignment constraints: each item must be assigned to exactly one container.
- Add capacity constraints: total weight in a container cannot exceed its capacity, multiplied by the container's usage variable.
- Add linking constraints: if an item is assigned to a container, that container must be marked as used.

### Step 4 - Define Objective
- Set the objective to minimize the sum of container usage variables.

### Formulation Template
```json
{
  "sets": [
    "items",
    "containers"
  ],
  "parameters": [
    "weight[items]",
    "capacity"
  ],
  "decision_variables": [
    "x[items, containers] ∈ {0, 1}",
    "y[containers] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in containers)"
  },
  "constraints": [
    "assignment: sum(x[i, j] for j in containers) == 1, for all i in items",
    "capacity: sum(weight[i] * x[i, j] for i in items) <= capacity * y[j], for all j in containers",
    "linking: y[j] >= x[i, j], for all i in items, j in containers"
  ]
}
```

### Common Pitfalls
- Forgetting to multiply capacity by `y[j]` can lead to infeasible models, as unused containers would still enforce a capacity of zero.
- Omitting explicit linking constraints can, in some solvers, lead to fractional solutions where `y[j]` is set to a small fraction instead of 1.
- Using an insufficiently large set of containers (upper bound) can make the problem infeasible; ensure the number of containers is at least the trivial lower bound (ceil(total weight / capacity)).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver, extract the solution, and perform validation checks to ensure feasibility and assess solution quality.

### Step 1 - Instantiate Solver and Set Parameters
- Instantiate the solver factory (e.g., `'cbc'` or `'gurobi'`).
- Configure key parameters: time limit, optimality gap tolerance, number of threads, and random seed for reproducibility.

### Step 2 - Solve and Check Status
- Execute the solve command.
- Check the solver status and termination condition. Accept solutions marked as optimal or feasible.

### Step 3 - Extract and Structure Solution
- Retrieve the objective value.
- Iterate through container usage variables to identify used containers.
- For each used container, iterate through assignment variables to list assigned items and calculate total load.
- Package results into a structured dictionary (e.g., JSON) for downstream use.

### Step 4 - Validate Solution
- Verify each item is assigned exactly once.
- Verify the load in each used container does not exceed capacity.
- Verify the objective value equals the count of used containers.
- Optionally, compare the solution to a simple lower bound (e.g., ceil(total weight / capacity)).

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model defined as per Modeling Stage)
model = pyo.ConcreteModel()
# ... (model construction code)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')  # or 'gurobi'
solver.options['seconds'] = 30
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

# Check status
status = results.solver.termination_condition
if status in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Extract solution
    used_containers = [j for j in model.containers if pyo.value(model.y[j]) > 0.5]
    assignments = {}
    for j in used_containers:
        items_in_j = [i for i in model.items if pyo.value(model.x[i, j]) > 0.5]
        assignments[j] = items_in_j
    # ... (proceed with validation and output)
else:
    raise Exception(f"Solver did not find a feasible solution. Status: {status}")
```

### Common Pitfalls
- Not checking solver status can lead to using invalid solutions.
- Using a loose optimality gap (`ratio` > 0) may return suboptimal solutions when an exact optimum is required.
- Forgetting to set a time limit for large instances can cause excessively long runtimes.

# Workflow 2 (CP-SAT with OR-Tools)

## Modeling stage

### Strategy Overview
This workflow uses Google's OR-Tools CP-SAT solver, a constraint programming solver optimized for problems with Boolean and integer variables. It models the problem with binary variables and linear constraints, leveraging the solver's efficient search for combinatorial assignments.

### Step 1 - Define Data Structures
- Define lists for items and containers.
- Define a list or dictionary for item weights.

### Step 2 - Create CP-SAT Variables
- Create a Boolean (binary) variable for each item-container assignment pair.
- Create a Boolean variable for each container to indicate usage.

### Step 3 - Add Constraints to the Model
- Add exactly-one constraints for each item across all containers.
- Add knapsack constraints for each container: sum of weights of assigned items must be less than or equal to capacity.
- Add linking constraints: container usage variable must be greater than or equal to each assignment variable for that container.

### Step 4 - Define Objective
- Set the objective to minimize the sum of container usage variables.

### Formulation Template
```json
{
  "sets": [
    "items",
    "containers"
  ],
  "parameters": [
    "weight[items]",
    "capacity"
  ],
  "decision_variables": [
    "assign[items, containers] ∈ Bool",
    "used[containers] ∈ Bool"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[c] for c in containers)"
  },
  "constraints": [
    "assignment: sum(assign[i, c] for c in containers) == 1, for all i in items",
    "capacity: sum(weight[i] * assign[i, c] for i in items) <= capacity, for all c in containers",
    "linking: used[c] >= assign[i, c], for all i in items, c in containers"
  ]
}
```

### Common Pitfalls
- Using `model.Add(sum(...) <= capacity)` without linking constraints can allow items to be assigned to a container marked as unused (`used[c]=0`), contradicting the objective.
- Creating an excessively large number of containers (the upper bound) can increase model size unnecessarily; balance between feasibility and performance.
- Not using `used[c] >= assign[i,c]` and relying solely on the capacity constraint may be insufficient for the CP-SAT solver's propagation.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver, extract the Boolean variable values, and assemble the assignment solution. CP-SAT is designed for fast resolution of feasibility and optimization problems with Boolean variables.

### Step 1 - Configure Solver Parameters
- Instantiate the `CpSolver()`.
- Set parameters: maximum time allowed, number of parallel search workers, random seed, and optionally an absolute or relative optimality gap.

### Step 2 - Solve and Interpret Status
- Execute the solver on the model.
- Check the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.). Proceed if status indicates a solution was found.

### Step 3 - Extract Solution Values
- Use `solver.Value(variable)` to get the value (0 or 1) of each Boolean variable.
- Build a mapping of used containers and the items assigned to them by iterating through the assignment variables.

### Step 4 - Validate and Report
- Perform the same feasibility checks as in Workflow 1 (assignment, capacity, objective).
- Output the solution in a structured format.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
assign = {}
for i in items:
    for c in containers:
        assign[(i, c)] = model.NewBoolVar(f'assign_{i}_{c}')
used = [model.NewBoolVar(f'used_{c}') for c in containers]

# Constraints
for i in items:
    model.Add(sum(assign[(i, c)] for c in containers) == 1)
for c in containers:
    model.Add(sum(weight[i] * assign[(i, c)] for i in items) <= capacity)
    for i in items:
        model.Add(used[c] >= assign[(i, c)])

# Objective
model.Minimize(sum(used))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    used_containers = [c for c, var in enumerate(used) if solver.Value(var) == 1]
    assignments = {}
    for c in used_containers:
        items_in_c = [i for i in items if solver.Value(assign[(i, c)]) == 1]
        assignments[c] = items_in_c
    # ... (proceed with validation and output)
else:
    raise Exception("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting `max_time_in_seconds` can lead to indefinite runs on difficult instances.
- Interpreting the status incorrectly; `FEASIBLE` is acceptable when a time limit is set, but `OPTIMAL` is not guaranteed.
- Forgetting that `solver.Value()` returns an integer (0 or 1) for Boolean variables.
