---
name: Generalized Bin Packing / Container Minimization
description: |
  Model and solve assignment problems where items must be assigned to containers with capacity limits, minimizing the number of containers used, using binary assignment and container usage variables.

---
# Workflow 1 (MILP with Pyomo and CBC/Gurobi)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo, suitable for open-source (CBC) or commercial (Gurobi) solvers. The model uses a clear separation of assignment and activation variables with capacity constraints deactivated for unused containers via a big-M formulation.

### Step 1 - Define Sets and Parameters
- Define the set of items `I` and the set of containers `J` (generated as an upper bound, e.g., number of items).
- Define parameters for item weights `weight[i][d]` (for each resource dimension `d`) and container capacity `capacity[d]` per dimension.

### Step 2 - Create Decision Variables
- Create binary assignment variables `x[i, j]` for each item `i` and container `j`.
- Create binary container usage variables `y[j]` for each container `j`.

### Step 3 - Formulate Constraints
- **Assignment**: Each item must be assigned to exactly one container: `sum(x[i, j] for j in J) == 1` for all `i`.
- **Capacity**: For each container `j` and resource dimension `d`, total consumption cannot exceed capacity multiplied by the container's usage variable: `sum(weight[i][d] * x[i, j] for i in I) <= capacity[d] * y[j]`.
- **Linking**: If an item is assigned to a container, that container must be marked as used: `y[j] >= x[i, j]` for all `i, j`. This strengthens the formulation.

### Step 4 - Define Objective
- Minimize the total number of containers used: `minimize sum(y[j] for j in J)`.

### Formulation Template
```json
{
  "sets": [
    "I (items)",
    "J (containers)"
  ],
  "parameters": [
    "weight[I][dimensions]",
    "capacity[dimensions]"
  ],
  "decision_variables": [
    "x[I, J] ∈ {0, 1}",
    "y[J] ∈ {0, 1}"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(y[j] for j in J)"
  },
  "constraints": [
    "assignment: sum(x[i, j] for j in J) == 1, for all i in I",
    "capacity: sum(weight[i][d] * x[i, j] for i in I) <= capacity[d] * y[j], for all j in J, for all dimensions d",
    "linking: y[j] >= x[i, j], for all i in I, j in J"
  ]
}
```

### Common Pitfalls
- Ensure the number of containers in set `J` is at least the trivial lower bound: `ceil(total weight / capacity)` for a single dimension, or the maximum over dimensions for multi-dimensional.
- For multi-dimensional capacity, add a separate capacity constraint for each dimension, each multiplied by `y[j]`.
- Omitting explicit linking constraints can lead to fractional solutions where `y[j]` is set to a small fraction instead of 1.
- Avoid using Pyomo reserved attribute names (e.g., `items`). Use distinct names like `I` for items and `J` for containers.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured MILP solver, extract the solution, and perform validation checks to ensure feasibility and assess solution quality.

### Step 1 - Instantiate Solver and Set Parameters
- Instantiate the solver factory (e.g., `'cbc'` or `'gurobi'`).
- Configure key parameters: time limit (`[TIME_LIMIT]`), optimality gap tolerance (set `ratio` to `0.0` for exact optimum), number of threads, and random seed for reproducibility.

### Step 2 - Solve and Check Status
- Execute the solve command.
- Check the solver termination condition. Accept solutions marked as `optimal` or `feasible`.

### Step 3 - Extract and Structure Solution
- Retrieve the objective value.
- Identify used containers: `[j for j in model.J if pyo.value(model.y[j]) > 0.5]`.
- For each used container, list assigned items and calculate total load per resource dimension.
- Package results into a structured dictionary (e.g., JSON) for downstream use.

### Step 4 - Validate Solution and Assess Quality
- **Feasibility Verification**:
    - Verify each item is assigned exactly once.
    - Verify the load in each used container does not exceed capacity for each resource dimension.
    - Verify the objective value equals the count of used containers.
- **Optimality Assessment**:
    - Compute a theoretical lower bound: for a single dimension, use `ceil(total weight / capacity)`. For multiple dimensions, compute the bound per dimension and take the maximum: `max(ceil(total_dim1 / capacity_dim1), ceil(total_dim2 / capacity_dim2), ...)`.
    - Compare the objective to this bound. An optimal solution meets this bound.

### Code Usage
```python
import pyomo.environ as pyo

# Build model from formulation (model defined as per Modeling Stage)
model = pyo.ConcreteModel()
# ... (model construction code)

# Solve with status / termination checks
solver = pyo.SolverFactory('cbc')  # or 'gurobi'
solver.options['seconds'] = [TIME_LIMIT]
solver.options['ratio'] = 0.0
results = solver.solve(model, tee=False)

# Check status
status = results.solver.termination_condition
if status in [pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible]:
    # Extract solution
    used_containers = [j for j in model.J if pyo.value(model.y[j]) > 0.5]
    assignments = {}
    for j in used_containers:
        items_in_j = [i for i in model.I if pyo.value(model.x[i, j]) > 0.5]
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
Use Google's OR-Tools CP-SAT solver, a constraint programming solver optimized for Boolean and integer variables. Model the problem with binary variables and linear constraints, leveraging efficient search for combinatorial assignments.

### Step 1 - Define Data Structures
- Define lists for items `I` and containers `J`.
- Define a list or dictionary for item weights `weight[i][d]` (for each resource dimension `d`).

### Step 2 - Create CP-SAT Variables
- Create a Boolean variable `assign[i, c]` for each item-container assignment pair.
- Create a Boolean variable `used[c]` for each container to indicate usage.

### Step 3 - Add Constraints to the Model
- **Assignment**: For each item, exactly one container must be selected: `sum(assign[i, c] for c in J) == 1`.
- **Capacity**: For each container `c` and each resource dimension `d`, total weight of assigned items must be less than or equal to capacity: `sum(weight[i][d] * assign[i, c] for i in I) <= capacity[d]`.
- **Linking**: Container usage variable must be greater than or equal to each assignment variable for that container: `used[c] >= assign[i, c]` for all `i, c`. This is crucial for the objective to work properly.

### Step 4 - Define Objective
- Minimize the sum of container usage variables: `minimize sum(used[c] for c in J)`.

### Formulation Template
```json
{
  "sets": [
    "I (items)",
    "J (containers)"
  ],
  "parameters": [
    "weight[I][dimensions]",
    "capacity[dimensions]"
  ],
  "decision_variables": [
    "assign[I, J] ∈ Bool",
    "used[J] ∈ Bool"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(used[c] for c in J)"
  },
  "constraints": [
    "assignment: sum(assign[i, c] for c in J) == 1, for all i in I",
    "capacity: sum(weight[i][d] * assign[i, c] for i in I) <= capacity[d], for all c in J, for all dimensions d",
    "linking: used[c] >= assign[i, c], for all i in I, c in J"
  ]
}
```

### Common Pitfalls
- Creating an excessively large number of containers (the upper bound) can increase model size unnecessarily; balance between feasibility and performance.
- Not using `used[c] >= assign[i, c]` and relying solely on the capacity constraint may be insufficient for the CP-SAT solver's propagation.

## Solving stage

### Strategy Overview
Configure and run the CP-SAT solver, extract the Boolean variable values, and assemble the assignment solution.

### Step 1 - Configure Solver Parameters
- Instantiate `CpSolver()`.
- Set parameters: maximum time allowed (`[TIME_LIMIT]`), number of parallel search workers, random seed, and optionally an absolute or relative optimality gap.

### Step 2 - Solve and Interpret Status
- Execute the solver on the model.
- Check the status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.). Proceed if status indicates a solution was found.

### Step 3 - Extract Solution Values
- Use `solver.Value(variable)` to get the value (0 or 1) of each Boolean variable.
- Build a mapping of used containers and the items assigned to them by iterating through the assignment variables.

### Step 4 - Validate and Report
- **Feasibility Verification**:
    - Verify each item is assigned exactly once.
    - Verify the load in each used container does not exceed capacity for each resource dimension.
    - Verify the objective value equals the count of used containers.
- **Optimality Assessment**:
    - Compute a theoretical lower bound as `ceil(total weight / capacity)` for a single dimension, or the maximum over dimensions for multi-dimensional.
    - Compare the objective to this bound; if equal, the solution is proven optimal.
- Output the solution in a structured format.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
assign = {}
for i in I:
    for c in J:
        assign[(i, c)] = model.NewBoolVar(f'assign_{i}_{c}')
used = [model.NewBoolVar(f'used_{c}') for c in J]

# Constraints
for i in I:
    model.Add(sum(assign[(i, c)] for c in J) == 1)
for c in J:
    for d in dimensions:
        model.Add(sum(weight[i][d] * assign[(i, c)] for i in I) <= capacity[d])
    for i in I:
        model.Add(used[c] >= assign[(i, c)])

# Objective
model.Minimize(sum(used))

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
status = solver.Solve(model)

if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    # Extract solution
    used_containers = [c for c in J if solver.Value(used[c]) == 1]
    assignments = {}
    for c in used_containers:
        items_in_c = [i for i in I if solver.Value(assign[(i, c)]) == 1]
        assignments[c] = items_in_c
    # ... (proceed with validation and output)
else:
    raise Exception("Solver did not find a feasible solution.")
```

### Common Pitfalls
- Not setting `max_time_in_seconds` can lead to indefinite runs on difficult instances.
- Interpreting the status incorrectly; `FEASIBLE` is acceptable when a time limit is set, but `OPTIMAL` is not guaranteed.
- Forgetting that `solver.Value()` returns an integer (0 or 1) for Boolean variables.
