---
name: GeneralizedAssignmentSolver
description: |
  Solves assignment problems with capacity constraints by formulating as a Mixed-Integer Linear Program (MILP) with binary decision variables, assignment and knapsack constraints, and a linear objective, then solving with a configured MILP solver.

---
# Workflow 1 (Pyomo-HiGHS)

## Modeling stage

### Strategy Overview
Model the problem as a Generalized Assignment Problem (GAP) using Pyomo's abstract modeling capabilities. Define sets for agents and tasks, binary decision variables for assignment, and linear constraints for assignment and capacity. The objective is to minimize total assignment cost.

### Step 1 - Problem Recognition and Set Definition
- Recognize the core structure as assigning tasks to agents subject to agent capacity limits.
- Define Pyomo Sets: `model.A` for agents (e.g., crews, machines) and `model.T` for tasks (e.g., zones, jobs).

### Step 2 - Parameter Declaration
- Declare parameters using `pyo.Param(model.A, model.T, within=pyo.NonNegativeReals)` for cost and resource consumption matrices (e.g., `model.cost`, `model.resource_use`).
- Declare agent capacity parameters using `pyo.Param(model.A, within=pyo.NonNegativeReals)`.

### Step 3 - Decision Variable Definition
- Define binary decision variables `model.x = pyo.Var(model.A, model.T, within=pyo.Binary)` where `model.x[a, t] = 1` indicates task `t` is assigned to agent `a`.

### Step 4 - Objective Function Formulation
- Formulate a linear objective to minimize total cost: `sum(model.cost[a, t] * model.x[a, t] for a in model.A for t in model.T)`.

### Step 5 - Constraint Formulation
- Add assignment constraints: For each task `t` in `model.T`, enforce `sum(model.x[a, t] for a in model.A) == 1`.
- Add capacity constraints: For each agent `a` in `model.A`, enforce `sum(model.resource_use[a, t] * model.x[a, t] for t in model.T) <= model.capacity[a]`.

### Formulation Template
```json
{
  "sets": ["A", "T"],
  "parameters": ["cost[A,T]", "resource_use[A,T]", "capacity[A]"],
  "decision_variables": ["x[A,T]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a,t] * x[a,t] for a in A for t in T)"
  },
  "constraints": [
    "sum(x[a,t] for a in A) == 1 for all t in T",
    "sum(resource_use[a,t] * x[a,t] for t in T) <= capacity[a] for all a in A"
  ]
}
```

### Common Pitfalls
- Forgetting to initialize all required parameters before model instantiation, leading to runtime errors.
- Incorrectly indexing parameters within constraint rules, causing KeyErrors.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS MILP solver via the `solverfactory`. Configure solver options for performance and reliability, then check the solution status and termination condition before extracting results.

### Step 1 - Solver Selection and Configuration
- Select solver: `solver = SolverFactory('highs')`.
- Configure options: Set `solver.options['time_limit'] = [TIME_LIMIT]`, `solver.options['threads'] = [NUM_THREADS]`, and `solver.options['mip_rel_gap'] = 0.0` for optimality.

### Step 2 - Model Solving and Status Check
- Execute `results = solver.solve(model, tee=False)`.
- Check solution status: `if results.solver.status == SolverStatus.ok`.
- Check termination condition: `if results.solver.termination_condition == TerminationCondition.optimal`.

### Step 3 - Solution Extraction and Validation
- Extract objective value: `pyo.value(model.obj)`.
- Extract assignments by iterating over `model.x` and checking `pyo.value(model.x[a, t]) > 0.5`.
- Compute realized resource usage per agent to verify capacity constraints are satisfied.

### Step 4 - Results Reporting
- Print the optimal cost and assignment mapping.
- Optionally, print agent utilization (total resource used / capacity).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# build model from formulation
model = pyo.ConcreteModel()
# ... define sets, params, variables, objective, constraints

# solve with status / termination checks
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
results = solver.solve(model, tee=False)

if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    # Process solution
    print(f'Optimal cost: {pyo.value(model.obj)}')
    # ... extract assignments
else:
    print('Solver did not find optimal solution.')
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially processing infeasible or suboptimal results.
- Misinterpreting variable values due to solver tolerances; always use a tolerance (e.g., > 0.5) when checking binary variables.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Model the problem using Google's OR-Tools CP-SAT solver. Define linear expressions for the objective and constraints using the solver's native interface. This approach is suitable for medium-sized problems and provides good performance with logical constraints.

### Step 1 - Solver and Model Initialization
- Create a CP-SAT model: `model = cp_model.CpModel()`.

### Step 2 - Variable Creation
- Create binary decision variables using `model.NewBoolVar(name)` for each agent-task pair. Store them in a dictionary `x[(a, t)]`.

### Step 3 - Objective Function Definition
- Create a linear objective expression: `objective = sum(cost[a, t] * x[(a, t)] for all pairs)`.
- Set the model to minimize this objective: `model.Minimize(objective)`.

### Step 4 - Constraint Addition
- Add assignment constraints: For each task `t`, enforce `sum(x[(a, t)] for all a) == 1`.
- Add capacity constraints: For each agent `a`, enforce `sum(resource_use[a, t] * x[(a, t)] for all t) <= capacity[a]`.

### Formulation Template
```json
{
  "sets": ["A", "T"],
  "parameters": ["cost[A,T]", "resource_use[A,T]", "capacity[A]"],
  "decision_variables": ["x[A,T]"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a,t] * x[a,t] for a in A for t in T)"
  },
  "constraints": [
    "sum(x[a,t] for a in A) == 1 for all t in T",
    "sum(resource_use[a,t] * x[a,t] for t in T) <= capacity[a] for all a in A"
  ]
}
```

### Common Pitfalls
- Exceeding the CP-SAT solver's limit on variable or constraint count for very large instances.
- Incorrectly building linear expressions by mixing Python types; ensure all terms are OR-Tools linear expressions.

## Solving stage

### Strategy Overview
Solve the CP-SAT model with configured time and optional solution callback. Check the solver's status and extract the variable assignments if an optimal or feasible solution is found.

### Step 1 - Solver Configuration and Solving
- Create a solver instance: `solver = cp_model.CpSolver()`.
- Set solver parameters: `solver.parameters.max_time_in_seconds = [TIME_LIMIT]`, `solver.parameters.num_search_workers = [NUM_THREADS]`.
- Execute the solve: `status = solver.Solve(model)`.

### Step 2 - Status Verification
- Check the solve status: `if status in (cp_model.OPTIMAL, cp_model.FEASIBLE)`.

### Step 3 - Solution Extraction
- If status is acceptable, extract assignments by evaluating `solver.Value(x[(a, t)]) == 1`.
- Compute the objective value from the solver: `objective_value = solver.ObjectiveValue()`.
- Compute realized resource usage per agent for validation.

### Step 4 - Results Reporting
- Print the status, objective value, and assignment list.
- Optionally, print a summary of agent utilization.

### Code Usage
```python
from ortools.sat.python import cp_model

# build model from formulation
model = cp_model.CpModel()
# ... create variables, objective, constraints

# solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = [TIME_LIMIT]
solver.parameters.num_search_workers = [NUM_THREADS]
status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    print(f'Objective value: {solver.ObjectiveValue()}')
    # ... extract assignments by checking solver.Value(x_var)
else:
    print('Solver did not find a solution.')
```

### Common Pitfalls
- Confusing `cp_model.OPTIMAL` with `cp_model.FEASIBLE`; the former guarantees optimality, the latter only feasibility.
- Not setting `num_search_workers` for parallel search, potentially missing performance gains on multi-core machines.
