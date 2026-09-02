---
name: AssignmentFlowWithParticipationRequirements
description: |
  Model and solve mixed-integer linear programs for assignment-flow problems with minimum contributor counts and conditional minimum delivery amounts, using either direct solver APIs or algebraic modeling frameworks.

---
# Workflow 1 (Direct Solver API - OR-Tools)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using a direct solver API. This approach involves manually constructing variables, constraints, and the objective using the solver's native objects, offering fine-grained control and immediate integration with the solver's features.

### Step 1 - Define Data Structures
- Organize problem data into Python dictionaries or lists for easy indexing.
- Create sets for producers and contracts, and define parameters for capacity, demand, cost, minimum delivery amounts, and minimum contributor counts.

### Step 2 - Create Decision Variables
- Instantiate continuous flow variables `x[p][c]` for the amount allocated from producer `p` to contract `c`.
- Instantiate binary assignment variables `y[p][c]` to indicate if producer `p` is assigned to contract `c`.

### Step 3 - Formulate Capacity and Demand Constraints
- Add linear inequality constraints to ensure total flow from each producer does not exceed its capacity.
- Add linear inequality constraints to ensure total flow to each contract meets or exceeds its demand.

### Step 4 - Enforce Minimum Contributor Counts
- For each contract, add a constraint that sums the binary assignment variables to be at least the required minimum number of contributors.

### Step 5 - Link Assignment to Flow with Big-M Constraints
- Add a lower-bound linking constraint: `x[p][c] >= min_delivery[p] * y[p][c]`. This enforces a minimum contribution amount when a producer is active.
- Add an upper-bound linking constraint: `x[p][c] <= capacity[p] * y[p][c]`. This forces the flow to zero when the producer is inactive and provides a tight upper bound.

### Step 6 - Define Linear Cost Objective
- Formulate the objective to minimize the total linear cost, summing `cost[p][c] * x[p][c]` over all producer-contract pairs.

### Formulation Template
```json
{
  "sets": [
    "producers",
    "contracts"
  ],
  "parameters": [
    "capacity[producers]",
    "demand[contracts]",
    "cost[producers][contracts]",
    "min_delivery[producers]",
    "min_contributors[contracts]"
  ],
  "decision_variables": [
    "x[producers][contracts] (continuous, >=0)",
    "y[producers][contracts] (binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[p][c] * x[p][c] for p in producers for c in contracts)"
  },
  "constraints": [
    "capacity_limit[p]: sum(x[p][c] for c in contracts) <= capacity[p]",
    "demand_satisfaction[c]: sum(x[p][c] for p in producers) >= demand[c]",
    "min_contributor_count[c]: sum(y[p][c] for p in producers) >= min_contributors[c]",
    "min_delivery_link[p][c]: x[p][c] >= min_delivery[p] * y[p][c]",
    "max_delivery_link[p][c]: x[p][c] <= capacity[p] * y[p][c]"
  ]
}
```

### Common Pitfalls
- Using an arbitrarily large `M` value in the upper-bound linking constraint, which weakens the linear relaxation and harms solver performance. Use the smallest valid bound (e.g., producer capacity).
- Forgetting to enforce the logical link in both directions (lower and upper bounds), which can lead to solutions where `y=1` but `x=0`.
- Not verifying that the sum of minimum delivery amounts from the required minimum contributors can satisfy the contract demand, potentially causing infeasibility.

## Solving stage

### Strategy Overview
Solve the constructed MILP using an open-source solver like SCIP or CBC via the OR-Tools wrapper. Configure solver parameters for reproducibility and performance, then extract and rigorously validate the solution.

### Step 1 - Initialize Solver and Set Parameters
- Create a solver instance (e.g., `SCIP` or `CBC`).
- Set a time limit, optimality gap tolerance, and number of threads for deterministic and efficient solving.

### Step 2 - Build Model from Formulation
- Use the solver's methods to create variables and add constraints as defined in the modeling stage.

### Step 3 - Solve and Check Status
- Invoke the solver's `Solve()` method.
- Check the result status (`OPTIMAL`, `FEASIBLE`, `INFEASIBLE`, etc.) to determine success.

### Step 4 - Extract and Validate Solution
- If the solution is optimal or feasible, retrieve the objective value and variable values.
- Programmatically verify all constraints (capacity, demand, contributor counts, minimum deliveries) to ensure the solution is correct and meets all business rules.

### Step 5 - Report Results
- Format the allocation details (active assignments and flows) in a human-readable structure.
- Output key metrics like total cost, capacity utilization, and constraint satisfaction status.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('SCIP')
if not solver:
    raise Exception('Solver not available.')

# Set parameters
solver.SetTimeLimit(60000)  # milliseconds
solver.SetNumThreads(4)

# Create variables
x = {}
y = {}
for p in producers:
    for c in contracts:
        x[p, c] = solver.NumVar(0, solver.infinity(), f'x_{p}_{c}')
        y[p, c] = solver.IntVar(0, 1, f'y_{p}_{c}')

# Add constraints (example: capacity)
for p in producers:
    solver.Add(sum(x[p, c] for c in contracts) <= capacity[p])

# ... Add all other constraints (demand, min contributors, big-M links)

# Set objective
objective = solver.Objective()
for p in producers:
    for c in contracts:
        objective.SetCoefficient(x[p, c], cost[p][c])
objective.SetMinimization()

# solve with status / termination checks
status = solver.Solve()

if status in (solver.OPTIMAL, solver.FEASIBLE):
    print(f'Objective value: {objective.Value()}')
    # Extract and validate solution
    solution_flows = {(p,c): x[p,c].solution_value() for p in producers for c in contracts if x[p,c].solution_value() > 1e-6}
    solution_assignments = {(p,c): y[p,c].solution_value() for p in producers for c in contracts if y[p,c].solution_value() > 0.5}
    # ... Perform validation checks
else:
    print('No optimal or feasible solution found.')
    # Handle infeasibility (e.g., analyze constraints)
```

### Common Pitfalls
- Accepting a `FEASIBLE` status without checking the optimality gap, which may lead to suboptimal solutions in time-limited runs.
- Not filtering near-zero values (e.g., `< 1e-6`) when extracting flows, resulting in cluttered output.
- Failing to implement post-solve validation, which can miss subtle constraint violations due to numerical tolerances.

# Workflow 2 (Algebraic Modeling - Pyomo)

## Modeling stage

### Strategy Overview
Formulate the problem using an algebraic modeling language (Pyomo). This approach separates the abstract model definition from the solver interface, promoting readability, maintainability, and easier modification of the problem structure.

### Step 1 - Declare Abstract Sets and Parameters
- Define Pyomo `Set` objects for producers and contracts.
- Define Pyomo `Param` objects for all numerical data, indexed by the appropriate sets.

### Step 2 - Declare Decision Variables
- Declare a continuous, non-negative `Var` for flow amounts, indexed by producer and contract.
- Declare a binary `Var` for assignment decisions, indexed by producer and contract.

### Step 3 - Construct Constraints via Rules
- Define Python functions (rules) that return constraint expressions for each index in a set.
- Implement capacity, demand, minimum contributor count, and Big-M linking constraints using these rules.

### Step 4 - Define the Objective Function
- Construct the objective expression as the sum of cost-weighted flows.
- Declare it as a minimization objective.

### Step 5 - Instantiate the Concrete Model
- Create a `ConcreteModel()` and populate it with the defined components.
- Load the specific data (sets and parameters) into the model instance.

### Formulation Template
```json
{
  "sets": [
    "model.P (producers)",
    "model.C (contracts)"
  ],
  "parameters": [
    "model.capacity[P]",
    "model.demand[C]",
    "model.cost[P, C]",
    "model.min_delivery[P]",
    "model.min_contributors[C]"
  ],
  "decision_variables": [
    "model.x[P, C] (NonNegativeReals)",
    "model.y[P, C] (Binary)"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(model.cost[p, c] * model.x[p, c] for p in model.P for c in model.C)"
  },
  "constraints": [
    "model.capacity_con[P]: sum(model.x[p, c] for c in model.C) <= model.capacity[p]",
    "model.demand_con[C]: sum(model.x[p, c] for p in model.P) >= model.demand[c]",
    "model.min_contributors_con[C]: sum(model.y[p, c] for p in model.P) >= model.min_contributors[c]",
    "model.min_delivery_con[P, C]: model.x[p, c] >= model.min_delivery[p] * model.y[p, c]",
    "model.max_delivery_con[P, C]: model.x[p, c] <= model.capacity[p] * model.y[p, c]"
  ]
}
```

### Common Pitfalls
- Defining constraints with incorrect index ordering in rule functions, leading to `KeyError` or wrong constraint application.
- Using mutable default arguments (like lists) within Pyomo rule functions, which can cause unexpected behavior.
- Not leveraging Pyomo's ability to define sparse sets or parameters, which can unnecessarily increase model size for problems with many potential but inactive connections.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a solver factory, which provides a clean interface to various backends (e.g., CBC, GLPK, Gurobi). Configure solver options and implement robust checks for solution status and termination conditions.

### Step 1 - Select and Configure Solver
- Use `SolverFactory` to instantiate a solver interface (e.g., `'cbc'`).
- Pass a dictionary of solver options (time limit, MIP gap, threads) to the `solve` call.

### Step 2 - Execute Solve and Capture Results
- Call the solver's `solve` method on the model instance.
- Capture the returned `SolverResults` object for detailed inspection.

### Step 3 - Verify Solution Status
- Check both the solver status (`results.solver.status`) and model termination condition (`results.solver.termination_condition`).
- Proceed only if the status is `ok` and termination is `optimal` or `feasible`.

### Step 4 - Extract and Process Solution
- Load the solution into the model instance.
- Iterate over model variables to extract flow values and active assignments, applying a tolerance for binary variables (e.g., `> 0.5`).

### Step 5 - Validate and Report
- Perform the same programmatic validation of constraints as in Workflow 1.
- Summarize the solution, including active assignments, flows, costs, and constraint slack.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()

# Sets
model.P = pyo.Set(initialize=producers)
model.C = pyo.Set(initialize=contracts)

# Parameters
model.capacity = pyo.Param(model.P, initialize=capacity_data)
model.demand = pyo.Param(model.C, initialize=demand_data)
model.cost = pyo.Param(model.P, model.C, initialize=cost_data)
model.min_delivery = pyo.Param(model.P, initialize=min_delivery_data)
model.min_contributors = pyo.Param(model.C, initialize=min_contributors_data)

# Variables
model.x = pyo.Var(model.P, model.C, domain=pyo.NonNegativeReals)
model.y = pyo.Var(model.P, model.C, domain=pyo.Binary)

# Objective
model.obj = pyo.Objective(expr=sum(model.cost[p,c] * model.x[p,c] for p in model.P for c in model.C), sense=pyo.minimize)

# Constraints (example: capacity rule)
def capacity_rule(m, p):
    return sum(m.x[p, c] for c in m.C) <= m.capacity[p]
model.capacity_con = pyo.Constraint(model.P, rule=capacity_rule)

# ... Define all other constraint rules

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
results = solver.solve(model, options={'seconds': 30, 'threads': 4})

if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition in (pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible)):
    print(f'Objective value: {pyo.value(model.obj)}')
    # Extract solution
    for p in model.P:
        for c in model.C:
            if model.y[p,c].value > 0.5:
                flow_val = model.x[p,c].value
                # ... record active assignment and flow
    # ... Perform validation checks
else:
    print('Solver failed to find an optimal/feasible solution.')
    print(f'Status: {results.solver.status}, Termination: {results.solver.termination_condition}')
```

### Common Pitfalls
- Assuming `pyo.value(model.obj)` is valid without first checking the solver status, which may raise an error if the model was not solved.
- Not setting a seed for the solver when using stochastic algorithms, leading to non-reproducible results.
- Overlooking the need to explicitly load the solution into the model with `model.solutions.load_from(results)` when using certain solver managers or for advanced post-processing.
