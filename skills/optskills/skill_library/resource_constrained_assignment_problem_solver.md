---
name: Resource-Constrained Assignment Problem Solver
description: |
  Models and solves assignment problems where tasks must be assigned to resources with capacity limits, minimizing total cost using either CP-SAT or MILP solvers.
---

# Workflow 1 (CP-SAT Solver)

## Modeling stage

### Strategy Overview
Use Google OR-Tools CP-SAT solver to model the assignment problem with binary decision variables, exactly-one constraints per task, resource capacity constraints, and a linear cost objective. This approach is well-suited for discrete optimization with binary variables and provides strong performance for moderate-sized instances.

### Step 1 - Define Sets and Parameters
- Define the set of resources and tasks as lists or ranges.
- Prepare dictionaries for resource capacities, task-resource requirements, and task-resource costs, indexed by resource and task identifiers.

### Step 2 - Create Binary Decision Variables
- For each (resource, task) pair, create a `NewBoolVar` indicating whether the task is assigned to that resource.
- Use a nested dictionary structure: `x[resource][task] = model.NewBoolVar(f"x_{resource}_{task}")`.

### Step 3 - Add Each Task Assigned Exactly Once Constraint
- For each task, add a constraint that the sum of assignment variables across all resources equals 1.
- This ensures every task is allocated to exactly one resource and no task is split or left unassigned.

### Step 4 - Add Resource Capacity Constraints
- For each resource, add a constraint that the sum of (requirement * assignment variable) over all tasks is less than or equal to the resource's capacity.
- This ensures the total load on each resource does not exceed its available capacity.

### Step 5 - Define and Minimize Objective
- Compute total cost as the sum of (cost * assignment variable) over all resource-task pairs.
- Set the objective to minimize this total cost using `model.Minimize(total_cost)`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": ["capacity[resource]", "requirement[resource][task]", "cost[resource][task]"],
  "decision_variables": ["x[resource][task] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[resource][task] * x[resource][task] for resource in resources for task in tasks)"
  },
  "constraints": [
    "sum(x[resource][task] for resource in resources) == 1 for each task",
    "sum(requirement[resource][task] * x[resource][task] for task in tasks) <= capacity[resource] for each resource"
  ]
}
```

### Common Pitfalls
- Forgetting to create variables for all resource-task pairs, leading to missing assignments.
- Using integer variables instead of boolean variables, which can slow down solving.
- Not ensuring requirement and cost data are indexed consistently with variable indices.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver with appropriate parameters for reliability and performance, then solve the model. Parse the solver status and extract the assignment solution, outputting results in a structured JSON format for downstream consumption.

### Step 1 - Configure Solver Parameters
- Create a `CpSolver` instance and set key parameters: `max_time_in_seconds` for time limit, `num_search_workers` for parallelism, `random_seed` for reproducibility, and `relative_gap_limit` for optimality tolerance.

### Step 2 - Solve the Model
- Call `solver.Solve(model)` and capture the status code.

### Step 3 - Handle Solver Status
- Check if status is `OPTIMAL` or `FEASIBLE` before reading results.
- For optimal/feasible solutions, extract the assignment by iterating over tasks and finding the resource where the variable value is 1.
- For infeasible cases, output a failure payload with the solver status code.

### Step 4 - Verify Solution Feasibility (Recommended)
- After extracting the assignment, compute resource usage per resource as `sum(requirement[(r, t)] for t assigned to r)` and verify it does not exceed `capacity[r]`.
- Compute total cost manually as `sum(cost[(r, t)] for each assignment)` and confirm it matches the solver's objective value. This guards against silent data indexing errors.

### Step 5 - Output Structured Results
- Build a JSON payload containing status, objective value, and assignment mapping.
- Print the payload with the prefix `RESULT_JSON:` for consistent parsing.

### Code Usage
```python
import json
from ortools.sat.python import cp_model

def solve_assignment():
    # Define data: resources, tasks, capacities, requirements, costs
    resources = [...]  # e.g., ["R1", "R2"]
    tasks = [...]      # e.g., ["T1", "T2", "T3"]
    capacity = {"R1": 10, "R2": 15}
    requirement = {("R1", "T1"): 3, ("R1", "T2"): 5, ...}
    cost = {("R1", "T1"): 100, ("R1", "T2"): 150, ...}

    model = cp_model.CpModel()
    x = {r: {t: model.NewBoolVar(f"x_{r}_{t}") for t in tasks} for r in resources}

    # Each task assigned exactly once
    for t in tasks:
        model.Add(sum(x[r][t] for r in resources) == 1)

    # Resource capacity constraints
    for r in resources:
        model.Add(sum(requirement[(r, t)] * x[r][t] for t in tasks) <= capacity[r])

    # Minimize total cost
    total_cost = sum(cost[(r, t)] * x[r][t] for r in resources for t in tasks)
    model.Minimize(total_cost)

    solver = cp_model.CpSolver()
    solver.parameters.max_time_in_seconds = 30
    solver.parameters.num_search_workers = 8
    solver.parameters.random_seed = 42
    solver.parameters.relative_gap_limit = 0.0

    status = solver.Solve(model)

    if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
        assignment = {t: next(r for r in resources if solver.Value(x[r][t]) == 1) for t in tasks}
        # Optional: verify feasibility
        # for r in resources:
        #     usage = sum(requirement[(r, t)] for t in tasks if assignment[t] == r)
        #     assert usage <= capacity[r], f"Capacity violated for {r}"
        payload = {
            "status": "optimal" if status == cp_model.OPTIMAL else "feasible",
            "objective": float(solver.ObjectiveValue()),
            "assignment": assignment
        }
        print(f"RESULT_JSON:{json.dumps(payload)}")
    else:
        payload = {"status": "failed", "solver_status": int(status)}
        print(f"RESULT_JSON:{json.dumps(payload)}")

if __name__ == "__main__":
    solve_assignment()
```

### Common Pitfalls
- Not checking for `FEASIBLE` status in addition to `OPTIMAL`, missing valid solutions when optimality is not proven.
- Using `solver.Value()` on variables that were not part of the solution, causing runtime errors.
- Forgetting to convert objective value to float for JSON serialization.

# Workflow 2 (Pyomo MILP Solver)

## Modeling stage

### Strategy Overview
Use Pyomo with a MILP solver (e.g., CBC or GLPK) to model the assignment problem. Define sets and parameters explicitly, create binary decision variables, enforce assignment and capacity constraints, and minimize total cost. This approach provides flexibility for extensions and access to a wide range of open-source and commercial solvers.

### Step 1 - Define Sets and Parameters
- Create a `ConcreteModel` and define `Set` objects for tasks and resources.
- Store input data (costs, requirements, capacities) as `Param` objects indexed by the appropriate sets, using dictionaries for initialization.

### Step 2 - Create Binary Decision Variables
- Define a binary `Var` indexed by (resource, task) pairs using `within=pyo.Binary`.
- Use a nested indexing approach: `model.x = pyo.Var(model.resources, model.tasks, within=pyo.Binary)`.

### Step 3 - Add Each Task Assigned Exactly Once Constraint
- For each task, add a constraint that the sum of assignment variables across all resources equals 1.
- Use a constraint rule with a lambda or function that iterates over tasks.

### Step 4 - Add Resource Capacity Constraints
- For each resource, add a constraint that the sum of (requirement * assignment variable) over all tasks is less than or equal to the resource's capacity.
- Ensure the requirement parameter is indexed consistently with the variable indices.

### Step 5 - Define and Minimize Objective
- Compute total cost as the sum of (cost * assignment variable) over all resource-task pairs.
- Set the objective with `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["resources", "tasks"],
  "parameters": ["capacity[resource]", "requirement[resource][task]", "cost[resource][task]"],
  "decision_variables": ["x[resource][task] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[resource][task] * x[resource][task] for resource in resources for task in tasks)"
  },
  "constraints": [
    "sum(x[resource][task] for resource in resources) == 1 for each task",
    "sum(requirement[resource][task] * x[resource][task] for task in tasks) <= capacity[resource] for each resource"
  ]
}
```

### Common Pitfalls
- Using `pyo.Set(initialize=...)` with lists that contain duplicate entries, causing indexing errors.
- Forgetting to use `mutable=True` for parameters that may need to be updated after model creation.
- Defining constraints with incorrect indexing, leading to missing or extra constraints.

## Solving stage

### Strategy Overview
Configure a MILP solver (CBC or GLPK) with appropriate options, solve the model, and check solver status before extracting results. Parse the solution to build an assignment mapping and output structured JSON results.

### Step 1 - Configure Solver
- Create a solver instance using `pyo.SolverFactory("cbc")` or `pyo.SolverFactory("glpk")`.
- Set solver options: time limit (`"seconds"` or `"tmlim"`), MIP gap tolerance (`"ratio"` or `"mipgap"`), and other relevant parameters.

### Step 2 - Solve the Model
- Call `solver.solve(model, tee=False)` and capture the results object.

### Step 3 - Check Solver Status
- Verify `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition` is `TerminationCondition.optimal` or `TerminationCondition.feasible`.
- Only proceed to extract variable values if the status is acceptable.

### Step 4 - Extract Assignment and Output Results
- Iterate over all (resource, task) pairs and check if `pyo.value(model.x[resource, task]) > 0.5` to determine assignments.
- Build a JSON payload with status, objective value, and assignment mapping.
- Print the payload with the prefix `RESULT_JSON:` for consistent parsing.

### Code Usage
```python
import json
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_assignment():
    # Define data
    resources = ["R1", "R2"]
    tasks = ["T1", "T2", "T3"]
    capacity = {"R1": 10, "R2": 15}
    requirement = {("R1", "T1"): 3, ("R1", "T2"): 5, ("R1", "T3"): 4,
                   ("R2", "T1"): 2, ("R2", "T2"): 6, ("R2", "T3"): 3}
    cost = {("R1", "T1"): 100, ("R1", "T2"): 150, ("R1", "T3"): 120,
            ("R2", "T1"): 110, ("R2", "T2"): 140, ("R2", "T3"): 130}

    model = pyo.ConcreteModel()
    model.resources = pyo.Set(initialize=resources)
    model.tasks = pyo.Set(initialize=tasks)
    model.capacity = pyo.Param(model.resources, initialize=capacity, mutable=True)
    model.requirement = pyo.Param(model.resources, model.tasks, initialize=requirement, mutable=True)
    model.cost = pyo.Param(model.resources, model.tasks, initialize=cost, mutable=True)
    model.x = pyo.Var(model.resources, model.tasks, within=pyo.Binary)

    # Each task assigned exactly once
    def assign_rule(m, t):
        return sum(m.x[r, t] for r in m.resources) == 1
    model.assign_constraint = pyo.Constraint(model.tasks, rule=assign_rule)

    # Resource capacity constraints
    def capacity_rule(m, r):
        return sum(m.requirement[r, t] * m.x[r, t] for t in m.tasks) <= m.capacity[r]
    model.capacity_constraint = pyo.Constraint(model.resources, rule=capacity_rule)

    # Objective: minimize total cost
    def obj_rule(m):
        return sum(m.cost[r, t] * m.x[r, t] for r in m.resources for t in m.tasks)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solve
    solver = pyo.SolverFactory("cbc")
    solver.options["seconds"] = 30
    solver.options["ratio"] = 0.0
    results = solver.solve(model, tee=False)

    # Check status
    if (results.solver.status == SolverStatus.ok and
        results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
        assignment = {}
        for t in tasks:
            for r in resources:
                if pyo.value(model.x[r, t]) > 0.5:
                    assignment[t] = r
                    break
        payload = {
            "status": "optimal" if results.solver.termination_condition == TerminationCondition.optimal else "feasible",
            "objective": float(pyo.value(model.obj)),
            "assignment": assignment
        }
        print(f"RESULT_JSON:{json.dumps(payload)}")
    else:
        payload = {"status": "failed", "solver_status": str(results.solver.status)}
        print(f"RESULT_JSON:{json.dumps(payload)}")

if __name__ == "__main__":
    solve_assignment()
```

### Common Pitfalls
- Not checking `SolverStatus.ok` before accessing termination condition, leading to attribute errors.
- Using `pyo.value()` on the objective before solving, which returns the initial expression rather than the solved value.
- Forgetting to break out of the inner loop when finding an assignment, potentially assigning the same task to multiple resources.
