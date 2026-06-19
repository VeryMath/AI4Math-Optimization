---
name: Set Covering with Logical OR Constraints
description: |
  Model and solve binary selection problems where elements must be covered by at least one chosen set, minimizing total selection cost.
---

# Workflow 1 (MILP with Pyomo and Highs/CBC)

## Modeling stage

### Strategy Overview
Formulate the problem as a standard Set Covering Integer Program using the Pyomo modeling language. This approach provides a declarative, solver-agnostic model that can be executed with open-source MILP solvers like HiGHS or CBC.

### Step 1 - Define Sets and Parameters
- Identify the collection of available sets (e.g., routes, facilities) and the elements (e.g., points, tasks) that require coverage.
- Define a cost parameter for each set and a coverage mapping parameter that links each element to the list of sets that can cover it.

### Step 2 - Declare Decision Variables
- Create a binary decision variable for each available set, where a value of 1 indicates the set is selected.

### Step 3 - Formulate Coverage Constraints
- For each element, add a linear constraint ensuring the sum of the binary variables for its covering sets is at least 1. This enforces the logical OR condition.

### Step 4 - Define the Objective Function
- Formulate a linear objective to minimize the total cost, defined as the sum of the cost of each selected set.

### Formulation Template
```json
{
  "sets": [
    "S: Collection of available sets.",
    "E: Collection of elements requiring coverage."
  ],
  "parameters": [
    "cost_s: Cost associated with selecting set s ∈ S.",
    "coverage_e: List of sets s ∈ S that can cover element e ∈ E."
  ],
  "decision_variables": [
    "x_s ∈ {0,1}: 1 if set s is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{s ∈ S} cost_s * x_s"
  },
  "constraints": [
    "Coverage: ∑_{s ∈ coverage_e} x_s ≥ 1, ∀ e ∈ E"
  ]
}
```

### Common Pitfalls
- Forgetting to include all relevant sets in the coverage mapping for an element, leading to an infeasible model.
- Using floating-point numbers for costs when integer costs are more appropriate for exact solvers, which can cause precision issues in the solution logic.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MILP solver, configure appropriate termination criteria, and implement robust solution extraction and verification.

### Step 1 - Instantiate Solver and Set Options
- Select a MILP solver (e.g., `highs`, `cbc`). Configure a time limit and set the optimality gap tolerance to zero to guarantee finding the optimal solution.

### Step 2 - Solve and Check Status
- Execute the solve command and capture the results object. Check the solver status and termination condition to confirm an optimal or feasible solution was found.

### Step 3 - Extract and Verify Solution
- Extract the values of the binary variables using a tolerance (e.g., > 0.5). Programmatically verify that all coverage constraints are satisfied by the extracted solution.

### Step 4 - Output Structured Results
- Package the optimal objective value and the list of selected sets into a structured format (e.g., dictionary, JSON) for downstream use.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model from formulation
model = pyo.ConcreteModel()
model.S = pyo.Set(initialize=sets_list)
model.E = pyo.Set(initialize=elements_list)
model.cost = pyo.Param(model.S, initialize=cost_dict)
model.x = pyo.Var(model.S, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(
    expr=sum(model.cost[s] * model.x[s] for s in model.S),
    sense=pyo.minimize
)

# Coverage constraints (using pre-defined coverage_dict)
def cover_rule(m, e):
    covering_sets = coverage_dict[e]
    return sum(m.x[s] for s in covering_sets) >= 1
model.cover = pyo.Constraint(model.E, rule=cover_rule)

# Solve with status / termination checks
solver = pyo.SolverFactory('highs')  # or 'cbc'
solver.options['time_limit'] = 30
solver.options['mip_rel_gap'] = 0.0

results = solver.solve(model, tee=False)

# Check solution status
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition == TerminationCondition.optimal):
    # Extract solution
    selected_sets = [s for s in model.S if pyo.value(model.x[s]) > 0.5]
    total_cost = pyo.value(model.obj)
    # Verification
    for e in model.E:
        cover_sum = sum(pyo.value(model.x[s]) for s in coverage_dict[e])
        assert cover_sum >= 0.99, f"Element {e} not covered."
else:
    # Handle suboptimal or infeasible result
    selected_sets = None
    total_cost = None
```

### Common Pitfalls
- Not checking both the solver status and termination condition, potentially interpreting a suboptimal or infeasible result as optimal.
- Using a naive equality check (`== 1.0`) to interpret binary variable values, which can fail due to solver floating-point precision; always use a tolerance.

# Workflow 2 (Direct API with OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem directly using a solver's API (e.g., OR-Tools). This imperative style offers fine-grained control and is efficient for prototyping or embedding within larger applications.

### Step 1 - Initialize Solver and Create Variables
- Instantiate the MILP solver object. Create a dictionary of binary decision variables, one for each available set.

### Step 2 - Add Coverage Constraints Imperatively
- For each element, create a linear constraint by summing the variables of its covering sets and setting the lower bound to 1.

### Step 3 - Set the Linear Objective
- Define the objective function as the linear sum of each variable multiplied by its cost, and set the optimization sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "S: Collection of available sets.",
    "E: Collection of elements requiring coverage."
  ],
  "parameters": [
    "cost_s: Cost associated with selecting set s ∈ S.",
    "coverage_e: List of sets s ∈ S that can cover element e ∈ E."
  ],
  "decision_variables": [
    "x_s ∈ {0,1}: 1 if set s is selected, 0 otherwise."
  ],
  "objective": {
    "sense": "min",
    "expression": "∑_{s ∈ S} cost_s * x_s"
  },
  "constraints": [
    "Coverage: ∑_{s ∈ coverage_e} x_s ≥ 1, ∀ e ∈ E"
  ]
}
```

### Common Pitfalls
- Manually building large constraint expressions incorrectly, such as omitting a variable from a sum. Using list comprehensions over the coverage mapping is safer.
- Not leveraging the solver's ability to handle mandatory selections (x_s = 1) directly, which can simplify the model.

## Solving stage

### Strategy Overview
Solve the model using the solver's native methods, manage solver resources like time limits, and implement solution extraction with validation.

### Step 1 - Configure Solver Settings
- Set practical limits on solving time and the number of threads to use, balancing speed and resource consumption.

### Step 2 - Execute Solve and Interpret Status
- Call the solver's `Solve()` method. Interpret the returned status code to distinguish between optimal, feasible, and infeasible outcomes.

### Step 3 - Extract and Validate the Solution
- Iterate through all decision variables, using a tolerance threshold to determine if they are selected. Compute the achieved objective value and verify all coverage constraints.

### Step 4 - Handle Edge Cases
- Implement logic for cases where the solver hits the time limit (feasible but not proven optimal) or proves infeasibility, providing informative output.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# Build model from formulation
solver = pywraplp.Solver.CreateSolver('SCIP')  # or 'CBC', 'SAT'
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)

# Create variables
x = {}
for s in sets_list:
    x[s] = solver.IntVar(0, 1, f'x_{s}')

# Add coverage constraints
for e in elements_list:
    covering_vars = [x[s] for s in coverage_dict[e]]
    constraint = solver.Sum(covering_vars) >= 1
    solver.Add(constraint)

# Set objective
objective = solver.Objective()
for s in sets_list:
    objective.SetCoefficient(x[s], cost_dict[s])
objective.SetMinimization()

# Solve with status / termination checks
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    # Extract solution
    selected_sets = [s for s in sets_list if x[s].solution_value() > 0.5]
    total_cost = objective.Value()
    # Verification
    for e in elements_list:
        cover_sum = sum(x[s].solution_value() for s in coverage_dict[e])
        if cover_sum < 0.99:
            raise AssertionError(f"Coverage violation for element {e}")
else:
    # Handle no solution found
    selected_sets = None
    total_cost = None
    if status == solver.INFEASIBLE:
        print("Model is infeasible.")
    elif status == solver.NOT_SOLVED:
        print("Solver did not find a solution within limits.")
```

### Common Pitfalls
- Confusing the `FEASIBLE` status (found a solution, not proven optimal) with `OPTIMAL`. This can lead to reporting suboptimal solutions as optimal.
- Neglecting to set a time limit, potentially allowing the solver to run indefinitely on large or complex instances.
