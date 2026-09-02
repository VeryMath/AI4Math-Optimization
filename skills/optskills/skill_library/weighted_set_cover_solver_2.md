---
name: Weighted Set Cover Solver
description: |
  Model and solve weighted set cover problems by selecting subsets to cover all elements at minimum cost using binary variables, coverage constraints, and MIP solvers.
---

# Workflow 1 (Matrix-Based MIP with OR-Tools)

## Modeling stage

### Strategy Overview
Model the problem as a classic set cover integer program using a binary coverage matrix. This approach is efficient for dense coverage relationships and leverages direct coefficient setting in a low-level solver API.

### Step 1 - Define Problem Data
- Identify the set of elements to be covered (e.g., projects, customers) and the set of selectable subsets (e.g., consultants, facilities).
- Define a cost parameter for each subset, typically as a list or array.
- Construct a binary coverage matrix where rows correspond to elements and columns correspond to subsets. An entry is 1 if the subset covers the element.

### Step 2 - Create Binary Decision Variables
- Instantiate one binary decision variable for each selectable subset. The variable equals 1 if the subset is selected, 0 otherwise.
- Enforce binary nature by setting variable bounds to 0 and 1.

### Step 3 - Formulate Coverage Constraints
- For each element, create a linear constraint requiring the sum of selected subsets that cover it to be at least 1.
- Use the coverage matrix to efficiently add coefficients only for non-zero entries.

### Step 4 - Define Weighted Objective
- Formulate the objective as the minimization of the total cost, which is the weighted sum of the binary variables using the subset costs as coefficients.

### Formulation Template
```json
{
  "sets": [
    "E: set of elements to cover",
    "S: set of selectable subsets"
  ],
  "parameters": [
    "cost[s ∈ S]: weight/cost of selecting subset s",
    "coverage[e ∈ E][s ∈ S]: binary parameter, 1 if subset s covers element e"
  ],
  "decision_variables": [
    "x[s ∈ S]: binary, 1 if subset s is selected"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_{s in S} cost[s] * x[s]"
  },
  "constraints": [
    "Coverage for each element e in E: sum_{s in S} coverage[e][s] * x[s] >= 1"
  ]
}
```

### Common Pitfalls
- Creating a dense constraint for every (element, subset) pair, even when coverage is 0, leading to unnecessary model bloat.
- Forgetting to verify that the coverage matrix correctly represents the problem's membership relationships.
- Using floating-point equality checks on binary variable solution values; always use a tolerance (e.g., > 0.5).

## Solving stage

### Strategy Overview
Solve the MIP model using the OR-Tools wrapper with the SCIP or CBC backend. This workflow provides fine-grained control over the solver and is suitable for prototyping and deployment in environments where commercial solvers are not available.

### Step 1 - Initialize Solver and Variables
- Create a solver instance (e.g., `SCIP` or `CBC`).
- Declare the list of binary variables using the solver's integer variable method with bounds (0, 1).

### Step 2 - Build Constraints from Matrix
- Iterate over each element. For each element, create a constraint with a lower bound of 1.
- Within the loop for each element, iterate over all subsets and use the coverage matrix to conditionally set the coefficient of the variable to 1.

### Step 3 - Set Objective and Solve
- Define the objective function, set all cost coefficients, and specify minimization.
- Set practical solver parameters like a time limit and number of threads.
- Call the solver's `Solve()` method.

### Step 4 - Extract and Validate Solution
- Check the solver status for `OPTIMAL` or `FEASIBLE`.
- Extract selected subsets by filtering variables with a solution value greater than 0.5.
- Retrieve the objective value as the total cost.
- Optionally, post-solve verification can be performed by checking the coverage of each element against the selected subsets.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Define data (placeholders)
# elements = range(num_elements)
# subsets = range(num_subsets)
# costs = [...]  # cost per subset
# coverage = [...]  # binary matrix [element][subset]

solver = pywraplp.Solver.CreateSolver("SCIP")
if not solver:
    raise Exception("Solver not available.")

# 2. Create variables
x = [solver.IntVar(0, 1, f"x_{s}") for s in subsets]

# 3. Add coverage constraints
for e in elements:
    constraint = solver.Constraint(1, solver.infinity())
    for s in subsets:
        if coverage[e][s] == 1:
            constraint.SetCoefficient(x[s], 1)

# 4. Set objective
objective = solver.Objective()
for s in subsets:
    objective.SetCoefficient(x[s], costs[s])
objective.SetMinimization()

# 5. Configure and solve
solver.SetTimeLimit(30000)  # milliseconds
solver.SetNumThreads(4)
status = solver.Solve()

# 6. Extract results
if status in (solver.OPTIMAL, solver.FEASIBLE):
    selected = [s for s in subsets if x[s].solution_value() > 0.5]
    total_cost = objective.Value()
    # Output or return results
else:
    # Handle no solution found
    pass
```

### Common Pitfalls
- Not checking if the solver backend is available, causing runtime errors.
- Misinterpreting the solver status codes; `FEASIBLE` is acceptable for a satisficing solution.
- Ignoring the solver's time limit, which can lead to indefinite hangs on large instances.

# Workflow 2 (Declarative Modeling with Pyomo and Gurobi)

## Modeling stage

### Strategy Overview
Model the problem declaratively using Pyomo's abstract or concrete modeling components. This approach separates problem definition from solver interaction, improves readability, and facilitates integration with high-performance commercial solvers like Gurobi.

### Step 1 - Define Abstract Sets and Parameters
- Declare Pyomo `Set` objects for the elements and subsets.
- Define a `Param` for subset costs, indexed by the subset set.
- Define a binary `Param` for the coverage relationship, indexed by the element and subset sets. This can be initialized from a sparse data structure.

### Step 2 - Declare Binary Variables and Objective
- Declare a `Var` object for the selection variables, indexed by subsets, with domain `Binary`.
- Define the objective as a `sum_product` of costs and variables, to be minimized.

### Step 3 - Express Coverage Constraints Rule-Based
- Define a Pyomo `Constraint` list indexed by the element set.
- For each element, the constraint rule returns the sum of variables for subsets that cover that element, enforcing it to be >= 1. The rule uses the coverage parameter for lookup.

### Formulation Template
```json
{
  "sets": [
    "model.E: Pyomo Set of elements",
    "model.S: Pyomo Set of subsets"
  ],
  "parameters": [
    "model.cost: Pyomo Param, indexed by model.S",
    "model.coverage: Pyomo Param, indexed by model.E x model.S, domain=Binary"
  ],
  "decision_variables": [
    "model.x: Pyomo Var, indexed by model.S, domain=Binary"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[s] * model.x[s] for s in model.S)"
  },
  "constraints": [
    "model.cover_rule: for each e in model.E, sum(model.coverage[e,s] * model.x[s] for s in model.S) >= 1"
  ]
}
```

### Common Pitfalls
- Using concrete model initialization with large, dense data structures, which consumes excessive memory. Prefer sparse data formats.
- Incorrectly defining constraint rules that cause scope errors by not passing the model instance.
- Overlooking the need to pre-process data into the specific formats (e.g., dictionaries) required by Pyomo `Param` initialization.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the Gurobi solver via the `SolverFactory`. This workflow leverages commercial solver performance, advanced MIP tuning, and robust status reporting, suitable for production systems requiring high reliability and speed.

### Step 1 - Instantiate Model and Load Data
- Create a concrete Pyomo model instance.
- Populate the sets and parameters with the problem-specific data, using dictionaries for efficient sparse data loading.

### Step 2 - Configure and Execute Solver
- Create a solver object using `SolverFactory('gurobi')`.
- Set solver options such as time limit, optimality gap tolerance, thread count, and a random seed for reproducibility.
- Call the `solve` method on the model instance with the solver.

### Step 3 - Inspect Solution Status
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- Proceed only if the solution is valid.

### Step 4 - Retrieve and Verify Solution
- Extract the objective function value using `pyo.value(model.obj)`.
- Iterate over the selection variables to collect indices where the variable value exceeds 0.5.
- Implement a verification function to confirm all elements are covered by the selected subsets.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# 1. Create a concrete model and define data (placeholders)
model = pyo.ConcreteModel()
# model.S = pyo.Set(initialize=subsets_indices)
# model.E = pyo.Set(initialize=elements_indices)
# model.cost = pyo.Param(model.S, initialize=cost_dict)
# model.coverage = pyo.Param(model.E, model.S, initialize=coverage_dict, default=0)

# 2. Declare variables and objective
model.x = pyo.Var(model.S, domain=pyo.Binary)
def obj_rule(model):
    return sum(model.cost[s] * model.x[s] for s in model.S)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

# 3. Declare coverage constraints
def cover_rule(model, e):
    return sum(model.coverage[e, s] * model.x[s] for s in model.S) >= 1
model.cover = pyo.Constraint(model.E, rule=cover_rule)

# 4. Solve
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model)

# 5. Check status and extract solution
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal,
                                             TerminationCondition.feasible)):
    total_cost = pyo.value(model.obj)
    selected = [s for s in model.S if pyo.value(model.x[s]) > 0.5]
    # Output or return results
else:
    # Handle infeasible or error status
    pass
```

### Common Pitfalls
- Assuming the solver is installed and licensed; always have a fallback plan (e.g., CBC).
- Not setting a `MIPGap` or time limit, which can cause the solver to run indefinitely on difficult instances.
- Failing to handle the case where the solver finds a feasible but not proven optimal solution, which is often acceptable for set cover problems.
