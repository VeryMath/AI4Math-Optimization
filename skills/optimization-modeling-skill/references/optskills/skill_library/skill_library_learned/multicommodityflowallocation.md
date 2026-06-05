---
name: MultiCommodityFlowAllocation
description: |
  Model and solve multi-source, multi-destination, multi-commodity allocation problems with exact demand satisfaction and linear profit maximization using structured LP formulations.
---

# Workflow 1 (OR-Tools GLOP for Dense LP)

## Modeling stage

### Strategy Overview
Formulate the allocation problem as a dense linear program using a three-index continuous variable. Leverage OR-Tools' GLOP solver for efficient solving of continuous LPs with equality constraints, using direct coefficient setting for clarity and control.

### Step 1 - Define Dimensions and Data Structure
- Identify the three fundamental sets: sources (e.g., companies), destinations (e.g., regions), and commodities (e.g., products).
- Organize input parameters as nested lists or dictionaries: `profit[source][destination][commodity]` and `demand[destination][commodity]`. Ensure consistent indexing.

### Step 2 - Create Decision Variables
- Instantiate a three-dimensional decision variable `x[source][destination][commodity]` representing the allocation quantity.
- Use `solver.NumVar(lower_bound, upper_bound, name)` with `lower_bound=0` and `upper_bound=solver.infinity()` to enforce non-negativity implicitly.
- Employ systematic naming (e.g., `f"x_{s}_{d}_{c}"`) for debugging and solution interpretation.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each destination-commodity pair, create an exact equality constraint: `sum(x[s][d][c] for all sources) == demand[d][c]`.
- Use `solver.Constraint(rhs, rhs)` to create a fixed constraint, then add coefficients via `constraint.SetCoefficient(variable, 1.0)` in a loop over sources.

### Step 4 - Define Linear Profit Objective
- Construct the objective to maximize total profit: `sum(profit[s][d][c] * x[s][d][c] for all indices)`.
- Use `solver.Maximize()` or `solver.Minimize()` and set coefficients using `objective.SetCoefficient(variable, coefficient)` in a triple-nested loop.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    "profit[sources][destinations][commodities]",
    "demand[destinations][commodities]"
  ],
  "decision_variables": ["x[sources][destinations][commodities] >= 0"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s][d][c] * x[s][d][c])"
  },
  "constraints": [
    "for each d in destinations, c in commodities: sum(x[s][d][c] for s in sources) == demand[d][c]"
  ]
}
```

### Common Pitfalls
- Inconsistent indexing between profit coefficients and variable creation loops, leading to incorrect objective values.
- Forgetting to set the upper bound to `solver.infinity()` for unbounded variables, which is safe for allocation quantities.
- Creating constraints with incorrect right-hand side values by not matching the demand parameter's indexing.

## Solving stage

### Strategy Overview
Solve the constructed LP model using the GLOP backend, implement robust status checking, extract and verify the solution, and output structured results.

### Step 1 - Initialize Solver and Solve
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Invoke `solver.Solve()` to obtain the solution status.

### Step 2 - Check Solver Status
- Verify the solution status is either `solver.OPTIMAL` or `solver.FEASIBLE` before proceeding.
- If status is `solver.INFEASIBLE` or `solver.ABNORMAL`, handle the error by returning a diagnostic payload with the status code.

### Step 3 - Extract and Validate Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- Iterate through all variables, using `variable.solution_value()` to get allocations. Filter values above a small tolerance (e.g., `1e-6`) to focus on meaningful flows.
- Optionally, verify constraint satisfaction by recomputing total allocation per destination-commodity pair and comparing to original demand within tolerance.

### Step 4 - Output Structured Results
- Package the results into a structured dictionary or JSON object containing the solver status, objective value, and a list of non-zero allocations with their indices and values.

### Code Usage
```python
# build model from formulation
from ortools.linear_solver import pywraplp

solver = pywraplp.Solver.CreateSolver('GLOP')
# ... (variable creation, constraint and objective building as per modeling stage)

# solve with status / termination checks
status = solver.Solve()
result_payload = {}

if status in (solver.OPTIMAL, solver.FEASIBLE):
    result_payload['status'] = 'OPTIMAL' if status == solver.OPTIMAL else 'FEASIBLE'
    result_payload['objective_value'] = solver.Objective().Value()
    allocations = []
    for s in sources:
        for d in destinations:
            for c in commodities:
                var = x[s][d][c]
                val = var.solution_value()
                if val > 1e-6:
                    allocations.append({'source': s, 'dest': d, 'commodity': c, 'value': val})
    result_payload['allocations'] = allocations
    # Optional verification loop
    for d in destinations:
        for c in commodities:
            total = sum(x[s][d][c].solution_value() for s in sources)
            # assert abs(total - demand[d][c]) < 1e-6
else:
    result_payload['status'] = 'FAILED'
    result_payload['solver_status_code'] = status
```

### Common Pitfalls
- Accessing `variable.solution_value()` without checking solver status first, which may cause errors.
- Using an inappropriate tolerance for filtering near-zero values, either missing small allocations or including numerical noise.
- Not providing a fallback error payload, making integration with automated systems difficult.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete model paradigm, defining explicit Sets, Parameters, Variables, Constraints, and Objective. This approach is solver-agnostic and facilitates use with open-source solvers like GLPK or CBC.

### Step 1 - Define Pyomo Sets and Parameters
- Declare Pyomo Set objects for `model.sources`, `model.destinations`, `model.commodities`.
- Define Pyomo Param objects or use standard Python dictionaries for `model.profit` and `model.demand`, ensuring they are indexed by the appropriate Set tuples.

### Step 2 - Create Decision Variables with Domain
- Instantiate a Pyomo Var `model.x` indexed over the three sets: `model.x = pyo.Var(model.sources, model.destinations, model.commodities, domain=pyo.NonNegativeReals)`.
- Using `domain=pyo.NonNegativeReals` enforces non-negativity bounds efficiently.

### Step 3 - Formulate Demand Constraints via Rules
- Define a constraint rule `demand_rule(model, d, c)` that returns the equality: `sum(model.x[s, d, c] for s in model.sources) == model.demand[d, c]`.
- Create a Pyomo Constraint object indexed over destinations and commodities using this rule.

### Step 4 - Construct Linear Objective
- Define the objective expression using a sum over all indices: `sum(model.profit[s, d, c] * model.x[s, d, c] for s in model.sources for d in model.destinations for c in model.commodities)`.
- Use `sense=pyo.maximize` in the Objective constructor.

### Formulation Template
```json
{
  "sets": ["sources", "destinations", "commodities"],
  "parameters": [
    "profit[(sources, destinations, commodities)]",
    "demand[(destinations, commodities)]"
  ],
  "decision_variables": ["x[sources, destinations, commodities] in NonNegativeReals"],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s, d, c] * x[s, d, c])"
  },
  "constraints": [
    "demand_constraint[destinations, commodities]: sum(x[s, d, c] for s in sources) == demand[d, c]"
  ]
}
```

### Common Pitfalls
- Mixing Pyomo Param indexing with Python dictionary lookups, causing key errors during model construction.
- Defining constraint rules with incorrect indentation or scope, leading to uninitialized model components.
- Forgetting to initialize all Sets before using them to index Parameters or Variables.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured open-source solver (GLPK or CBC), perform comprehensive status and termination checks, load the solution, and extract results with validation.

### Step 1 - Configure and Execute Solver
- Create a solver factory: `solver = pyo.SolverFactory('glpk')` (or `'cbc'`).
- Set practical options: `solver.options['tmlim'] = 30` for time limit, `solver.options['mipgap'] = 0.0` for optimality tolerance.
- Solve the model: `results = solver.solve(model, tee=False)`.

### Step 2 - Verify Solver Status and Termination
- Check that `results.solver.status == pyo.SolverStatus.ok`.
- Verify `results.solver.termination_condition` is either `pyo.TerminationCondition.optimal` or `pyo.TerminationCondition.feasible`.
- If checks fail, inspect the termination condition and status for error diagnosis.

### Step 3 - Load Solution and Extract Values
- If `load_solutions=False` was used, call `model.solutions.load_from(results)`.
- Retrieve the objective value via `pyo.value(model.obj)`.
- Iterate through `model.x` to get variable values using `pyo.value(model.x[s, d, c])`, filtering near-zero values.

### Step 4 - Validate and Structure Output
- Optionally, verify constraint satisfaction by recomputing sums per destination-commodity pair.
- Package results into a dictionary containing status, objective value, and a list of non-zero allocations.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

model = pyo.ConcreteModel()
model.sources = pyo.Set(initialize=sources_list)
model.destinations = pyo.Set(initialize=destinations_list)
model.commodities = pyo.Set(initialize=commodities_list)
# ... (define parameters, variables, constraints, objective as per modeling stage)

# solve with status / termination checks
solver = pyo.SolverFactory('glpk')
solver.options['tmlim'] = 30
results = solver.solve(model, tee=False)

result_payload = {}
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible)):
    result_payload['status'] = str(results.solver.termination_condition)
    result_payload['objective_value'] = pyo.value(model.obj)
    allocations = []
    for s in model.sources:
        for d in model.destinations:
            for c in model.commodities:
                val = pyo.value(model.x[s, d, c])
                if val > 1e-6:
                    allocations.append({'source': s, 'dest': d, 'commodity': c, 'value': val})
    result_payload['allocations'] = allocations
else:
    result_payload['status'] = 'FAILED'
    result_payload['solver_status'] = str(results.solver.status)
    result_payload['termination_condition'] = str(results.solver.termination_condition)
```

### Common Pitfalls
- Assuming the solution is automatically loaded into the model; always check if `load_solutions` behavior is as expected.
- Not handling the `feasible` termination condition, which still provides a valid but potentially suboptimal solution.
- Setting solver options incorrectly for the chosen solver (e.g., using `'seconds'` for GLPK instead of `'tmlim'`).
