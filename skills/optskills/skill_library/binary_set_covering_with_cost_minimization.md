---
name: Binary Set Covering with Cost Minimization
description: |
  Model and solve binary set covering problems where a subset of items must be selected to satisfy coverage requirements while minimizing total cost, using either OR-Tools or Pyomo.
---

# Workflow 1 (OR-Tools SCIP Solver)

## Modeling stage

### Strategy Overview
Define binary decision variables for each candidate item, enforce set covering constraints as linear inequalities requiring at least a minimum number of selected items from specified subsets, and formulate a linear cost minimization objective.

### Step 1 - Define Decision Variables
- Create a binary integer variable for each candidate item using `solver.IntVar(0, 1, name)` to represent selection status (1 = selected, 0 = not selected).
- Store variables in a dictionary keyed by item identifiers for easy access during constraint and objective construction.

### Step 2 - Enforce Set Covering Constraints
- For each coverage requirement, construct a linear inequality that sums the binary variables of items in the relevant subset and enforces a lower bound: `solver.Add(sum(variables_in_subset) >= required_count)`.
- When multiple coverage requirements share identical item subsets, include each as a separate constraint; duplicates do not alter the feasible region but ensure completeness.

### Step 3 - Build Minimization Objective
- Create an empty `Objective()` object using `solver.Objective()`.
- For each item, set its cost coefficient with `objective.SetCoefficient(variable, cost)`.
- Call `objective.SetMinimization()` to specify the optimization sense.

### Formulation Template
```json
{
  "sets": ["I: set of candidate items"],
  "parameters": ["c_i: cost of selecting item i", "S_j: subset of items for coverage requirement j", "r_j: minimum number of items to select from S_j"],
  "decision_variables": ["x_i ∈ {0,1}: 1 if item i is selected"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i∈I} c_i * x_i"
  },
  "constraints": ["sum_{i∈S_j} x_i >= r_j, ∀j"]
}
```

### Common Pitfalls
- Forgetting to set the objective sense to minimization, which defaults to maximization in OR-Tools.
- Using `solver.Sum()` instead of Python's built-in `sum()` for small expressions; both work but `sum()` is more readable for simple cases.
- Not storing variables in a dictionary, leading to difficulty when referencing them in constraints.

## Solving stage

### Strategy Overview
Initialize a SCIP solver, configure time limits and parallelism, solve the model, check solution status, and extract binary decisions with a threshold.

### Step 1 - Initialize Solver and Configure Options
- Create solver instance with `pywraplp.Solver.CreateSolver("SCIP")` and verify it is not `None` to handle missing solver gracefully.
- Set a time limit in milliseconds using `solver.SetTimeLimit(milliseconds)` and thread count with `solver.SetNumThreads(n)`.

### Step 2 - Solve and Check Status
- Call `solver.Solve()` and store the result status.
- Check if status is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` before reading solution values.

### Step 3 - Extract Results
- Retrieve variable values using `variable.solution_value()` and compare against a threshold (e.g., `> 0.5`) to determine binary decisions.
- Obtain the objective value with `solver.Objective().Value()`.

### Code Usage
```python
from ortools.linear_solver import pywraplp

def solve_set_covering(items, costs, coverage_requirements):
    """
    items: list of item identifiers
    costs: dict mapping item -> cost
    coverage_requirements: list of (subset_of_items, min_required)
    """
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        return {"status": "failed", "reason": "SCIP solver not available"}

    # Step 1: Decision variables
    x = {i: solver.IntVar(0, 1, f"x_{i}") for i in items}

    # Step 2: Set covering constraints
    for subset, required in coverage_requirements:
        solver.Add(sum(x[i] for i in subset) >= required)

    # Step 3: Objective
    objective = solver.Objective()
    for i in items:
        objective.SetCoefficient(x[i], costs[i])
    objective.SetMinimization()

    # Solving stage
    solver.SetTimeLimit(30000)  # 30 seconds
    solver.SetNumThreads(4)
    status = solver.Solve()

    if status not in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        return {"status": "failed", "reason": f"Solver status: {status}"}

    selected = [i for i in items if x[i].solution_value() > 0.5]
    return {
        "status": "success",
        "objective": solver.Objective().Value(),
        "selected_items": selected
    }
```

### Common Pitfalls
- Not checking solver initialization failure, leading to cryptic errors later.
- Using integer comparison (`== 1`) instead of threshold comparison for floating-point solution values.
- Forgetting to cast objective value to float for JSON serialization.

# Workflow 2 (Pyomo with CBC/GLPK)

## Modeling stage

### Strategy Overview
Use Pyomo's abstract modeling framework with binary variables, a ConstraintList for flexible constraint addition, and a linear cost minimization objective. This approach supports systematic constraint generation and easy debugging.

### Step 1 - Define Binary Variables
- Create a Pyomo ConcreteModel and define binary variables using `pyo.Var(domain=pyo.Binary)` for each candidate item.
- Index variables by item identifiers for clean mapping to cost and constraint data.

### Step 2 - Add Set Covering Constraints
- Use `pyo.ConstraintList()` to dynamically add constraints.
- For each coverage requirement, add a constraint expression: `sum(var[i] for i in subset) >= required`.
- When generating constraints systematically (e.g., all non-empty subsets), use `itertools.combinations` to enumerate subsets and feasible minimum requirements.

### Step 3 - Formulate Objective
- Define a linear objective expression: `sum(cost[i] * var[i] for i in items)`.
- Set the objective sense to minimization with `sense=pyo.minimize`.

### Formulation Template
```json
{
  "sets": ["I: set of candidate items"],
  "parameters": ["c_i: cost of selecting item i", "S_j: subset of items for coverage requirement j", "r_j: minimum number of items to select from S_j"],
  "decision_variables": ["x_i ∈ {0,1}: 1 if item i is selected"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i∈I} c_i * x_i"
  },
  "constraints": ["sum_{i∈S_j} x_i >= r_j, ∀j"]
}
```

### Common Pitfalls
- Adding duplicate constraints to ConstraintList unnecessarily; while harmless, it increases model size.
- Forgetting to import itertools when generating subsets systematically.
- Using mutable data structures (lists) in constraint expressions that change after model creation.

## Solving stage

### Strategy Overview
Configure a CBC or GLPK solver with time limits and optimality requirements, solve the model, verify solver status, and extract results in a structured format.

### Step 1 - Configure Solver
- Initialize solver with `pyo.SolverFactory("cbc")` or `pyo.SolverFactory("glpk")`.
- Set solver options: for CBC use `options["seconds"] = 30` and `options["ratio"] = 0.0`; for GLPK use `options["tmlim"] = 30` and `options["mipgap"] = 0.0`.

### Step 2 - Solve and Validate Status
- Call `solver.solve(model, tee=False)` and store results.
- Check `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.

### Step 3 - Extract and Output Results
- Retrieve variable values with `int(pyo.value(var[i]))` and objective with `float(pyo.value(model.obj))`.
- Output results as a JSON payload with a prefix like `RESULT_JSON:` for structured parsing.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import itertools

def solve_set_covering_pyomo(items, costs, coverage_requirements):
    """
    items: list of item identifiers
    costs: dict mapping item -> cost
    coverage_requirements: list of (subset_of_items, min_required)
    """
    model = pyo.ConcreteModel()
    model.items = pyo.Set(initialize=items)

    # Step 1: Decision variables
    model.x = pyo.Var(model.items, domain=pyo.Binary)

    # Step 2: Set covering constraints
    model.constraints = pyo.ConstraintList()
    for subset, required in coverage_requirements:
        model.constraints.add(sum(model.x[i] for i in subset) >= required)

    # Step 3: Objective
    def obj_rule(m):
        return sum(costs[i] * m.x[i] for i in m.items)
    model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

    # Solving stage
    solver = pyo.SolverFactory("cbc")
    solver.options["seconds"] = 30
    solver.options["ratio"] = 0.0

    results = solver.solve(model, tee=False)

    if results.solver.status != SolverStatus.ok:
        return {"status": "failed", "reason": f"Solver status: {results.solver.status}"}
    
    term = results.solver.termination_condition
    if term not in (TerminationCondition.optimal, TerminationCondition.feasible):
        return {"status": "failed", "reason": f"Termination: {term}"}

    selected = [i for i in items if int(pyo.value(model.x[i])) == 1]
    return {
        "status": "success",
        "objective": float(pyo.value(model.obj)),
        "selected_items": selected
    }
```

### Common Pitfalls
- Not checking both solver status and termination condition, leading to acceptance of invalid solutions.
- Using `pyo.value()` without casting to int for binary variables, which may return floating-point values.
- Forgetting to set `tee=False` to suppress solver output in production code.
