---
name: Supply Allocation Profit Maximization
description: |
  Model and solve linear programming problems that allocate supply quantities across entities to maximize profit while satisfying demand equality and non-negativity constraints.
---

# Workflow 1 (OR-Tools LP Solver)

## Modeling stage

### Strategy Overview
Use Google OR-Tools' pywraplp module to formulate a linear program with continuous decision variables representing supply quantities. Encode profit maximization as a linear objective, demand satisfaction as equality constraints, and enforce non-negativity through variable bounds.

### Step 1 - Define Data Structures
- Create dictionaries to store profit coefficients keyed by tuples of entity combinations (e.g., `(source, product, destination)`).
- Create dictionaries to store demand requirements keyed by tuples of product and destination (e.g., `(product, destination)`).
- Define lists of all entity identifiers (sources, products, destinations) for iteration.

### Step 2 - Create Solver and Variables
- Instantiate solver with `pywraplp.Solver.CreateSolver("GLOP")` for continuous LP problems.
- For each combination of entities, create a decision variable using `solver.NumVar(0, solver.infinity(), name)` to represent the supply quantity.

### Step 3 - Add Demand Constraints
- For each product-destination pair, create an equality constraint using `solver.Constraint(demand, demand)`.
- Add coefficients to the constraint by summing the appropriate decision variables across all sources.

### Step 4 - Build Objective Function
- Create an objective object with `solver.Objective()`.
- Set each variable's coefficient using `objective.SetCoefficient(variable, profit_coefficient)`.
- Set the direction to maximization with `objective.SetMaximization()`.

### Formulation Template
```json
{
  "sets": ["SOURCES", "PRODUCTS", "DESTINATIONS"],
  "parameters": [
    {"name": "profit", "index": ["SOURCE", "PRODUCT", "DESTINATION"], "type": "float"},
    {"name": "demand", "index": ["PRODUCT", "DESTINATION"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["SOURCE", "PRODUCT", "DESTINATION"], "type": "continuous", "lower_bound": 0}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s,p,d] * x[s,p,d] for all s,p,d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["PRODUCT", "DESTINATION"], "type": "equality", "expression": "sum(x[s,p,d] for all s) == demand[p,d]"}
  ]
}
```

### Common Pitfalls
- Forgetting to set the objective direction to maximization (default is minimization).
- Using `NumVar` without specifying lower bound 0, which defaults to negative infinity.
- Mismatching variable indices when adding coefficients to constraints.

## Solving stage

### Strategy Overview
Solve the LP using GLOP solver, verify optimality status, extract solution values, and output results in a structured JSON format for automated parsing.

### Step 1 - Solve and Check Status
- Call `solver.Solve()` and capture the status.
- Check if `status == pywraplp.Solver.OPTIMAL` before proceeding to read results.

### Step 2 - Extract Solution Values
- Retrieve the objective value via `solver.Objective().Value()`.
- Iterate over all decision variables and get their values using `variable.solution_value()`.
- Round values to a reasonable precision (e.g., 4 decimal places) for output.

### Step 3 - Verify Solution Consistency
- After extraction, verify that all demand constraints are satisfied by summing supplies per product-destination and comparing to the original demand data.
- Recompute the objective value manually from the solution to confirm consistency with the solver-reported value.

### Step 4 - Format and Output Results
- Build a dictionary with keys "status", "objective", and "solution".
- Output the dictionary as a JSON string prefixed with `RESULT_JSON:` for reliable parsing.

### Code Usage
```python
import pywraplp
import json

# Data preparation
sources = ["source_1", "source_2"]
products = ["product_1", "product_2"]
destinations = ["dest_1", "dest_2"]

profit = {("source_1", "product_1", "dest_1"): 10.0, ...}
demand = {("product_1", "dest_1"): 100.0, ...}

# Create solver
solver = pywraplp.Solver.CreateSolver("GLOP")

# Decision variables
x = {}
for s in sources:
    for p in products:
        for d in destinations:
            x[(s, p, d)] = solver.NumVar(0, solver.infinity(), f"x_{s}_{p}_{d}")

# Demand constraints
for p in products:
    for d in destinations:
        constraint = solver.Constraint(demand[(p, d)], demand[(p, d)])
        for s in sources:
            constraint.SetCoefficient(x[(s, p, d)], 1)

# Objective
objective = solver.Objective()
for (s, p, d), coeff in profit.items():
    objective.SetCoefficient(x[(s, p, d)], coeff)
objective.SetMaximization()

# Solve
status = solver.Solve()

# Extract results
if status == pywraplp.Solver.OPTIMAL:
    result = {
        "status": "OPTIMAL",
        "objective": round(objective.Value(), 4),
        "solution": {str(k): round(v.solution_value(), 4) for k, v in x.items()}
    }
else:
    result = {"status": "NOT_OPTIMAL", "solver_status": status}

print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Not checking solver status before accessing solution values, which can cause runtime errors.
- Using `solver.infinity()` incorrectly in variable bounds (should be method call).
- Forgetting to convert dictionary keys to strings for JSON serialization.

# Workflow 2 (Pyomo with HiGHS Solver)

## Modeling stage

### Strategy Overview
Use Pyomo's algebraic modeling language to define sets, parameters, decision variables, constraints, and objective in a declarative manner. Leverage Pyomo's rule-based constraint and objective definitions for clean separation of model logic.

### Step 1 - Define Index Sets
- Create Pyomo Set objects for each entity category using `pyo.Set(initialize=list_of_items)`.
- Use descriptive set names (e.g., `model.SOURCES`, `model.PRODUCTS`, `model.DESTINATIONS`).

### Step 2 - Declare Parameters
- Define profit and demand as Pyomo Param objects indexed over the appropriate sets.
- Initialize parameters from dictionaries using `pyo.Param(model.SOURCES, model.PRODUCTS, model.DESTINATIONS, initialize=profit_dict, within=pyo.Reals)`.

### Step 3 - Create Decision Variables
- Define a continuous non-negative variable indexed over all sets: `pyo.Var(model.SOURCES, model.PRODUCTS, model.DESTINATIONS, domain=pyo.NonNegativeReals)`.

### Step 4 - Formulate Constraints
- Write a constraint rule function that takes the model and index values, sums over the source index, and returns an equality expression.
- Apply the constraint over product and destination sets: `pyo.Constraint(model.PRODUCTS, model.DESTINATIONS, rule=demand_rule)`.

### Step 5 - Build Objective
- Define the objective as a sum expression: `sum(model.profit[s,p,d] * model.x[s,p,d] for s in model.SOURCES for p in model.PRODUCTS for d in model.DESTINATIONS)`.
- Set the sense to `pyo.maximize`.

### Formulation Template
```json
{
  "sets": ["SOURCES", "PRODUCTS", "DESTINATIONS"],
  "parameters": [
    {"name": "profit", "index": ["SOURCES", "PRODUCTS", "DESTINATIONS"], "type": "float"},
    {"name": "demand", "index": ["PRODUCTS", "DESTINATIONS"], "type": "float"}
  ],
  "decision_variables": [
    {"name": "x", "index": ["SOURCES", "PRODUCTS", "DESTINATIONS"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[s,p,d] * x[s,p,d] for all s,p,d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "index": ["PRODUCTS", "DESTINATIONS"], "type": "equality", "expression": "sum(x[s,p,d] for all s) == demand[p,d]"}
  ]
}
```

### Common Pitfalls
- Variable name conflicts between model object and loop variables in generator expressions (use distinct names like `mod` for model parameter in rule functions).
- Forgetting to import `pyo.environ` or using incorrect module references.
- Not specifying `within=pyo.NonNegativeReals` for parameters that should be non-negative.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the HiGHS solver, check termination conditions, extract solution values, and output results in a structured JSON format with proper error handling.

### Step 1 - Configure and Run Solver
- Instantiate solver with `pyo.SolverFactory("highs")`.
- Set solver options like `time_limit` and `threads` for performance control.
- Call `solver.solve(model, tee=False)` and capture the results object.

### Step 2 - Check Solver Status
- Verify `results.solver.status == SolverStatus.ok` and `results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- For infeasible or error cases, output a failure payload with solver status and termination condition.

### Step 3 - Extract Solution Values
- Get the objective value using `float(pyo.value(model.obj))`.
- Iterate over all variable indices and extract values using `float(pyo.value(model.x[s, p, d]))`.
- Collect results into a dictionary with descriptive keys.

### Step 4 - Verify Solution Consistency
- After extraction, verify that all demand constraints are satisfied by summing supplies per product-destination and comparing to the original demand data.
- Recompute the objective value manually from the solution to confirm consistency with the solver-reported value.

### Step 5 - Format and Output Results
- Build a result dictionary with keys "status", "objective", and "solution".
- Output as JSON string prefixed with `RESULT_JSON:` for automated parsing.

### Code Usage
```python
import pyomo.environ as pyo
import json

# Data preparation
sources = ["source_1", "source_2"]
products = ["product_1", "product_2"]
destinations = ["dest_1", "dest_2"]

profit_data = {("source_1", "product_1", "dest_1"): 10.0, ...}
demand_data = {("product_1", "dest_1"): 100.0, ...}

# Build model
model = pyo.ConcreteModel()
model.SOURCES = pyo.Set(initialize=sources)
model.PRODUCTS = pyo.Set(initialize=products)
model.DESTINATIONS = pyo.Set(initialize=destinations)

model.profit = pyo.Param(model.SOURCES, model.PRODUCTS, model.DESTINATIONS, initialize=profit_data, within=pyo.Reals)
model.demand = pyo.Param(model.PRODUCTS, model.DESTINATIONS, initialize=demand_data, within=pyo.NonNegativeReals)

model.x = pyo.Var(model.SOURCES, model.PRODUCTS, model.DESTINATIONS, domain=pyo.NonNegativeReals)

def demand_rule(mod, p, d):
    return sum(mod.x[s, p, d] for s in mod.SOURCES) == mod.demand[p, d]

model.demand_constraint = pyo.Constraint(model.PRODUCTS, model.DESTINATIONS, rule=demand_rule)

def obj_rule(mod):
    return sum(mod.profit[s, p, d] * mod.x[s, p, d] for s in mod.SOURCES for p in mod.PRODUCTS for d in mod.DESTINATIONS)

model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# Solve
solver = pyo.SolverFactory("highs")
solver.options["time_limit"] = 60
solver.options["threads"] = 4
results = solver.solve(model, tee=False)

# Extract results
if results.solver.status == pyo.SolverStatus.ok and results.solver.termination_condition in {pyo.TerminationCondition.optimal, pyo.TerminationCondition.feasible}:
    solution = {}
    for s in model.SOURCES:
        for p in model.PRODUCTS:
            for d in model.DESTINATIONS:
                solution[f"x_{s}_{p}_{d}"] = round(float(pyo.value(model.x[s, p, d])), 4)
    
    result = {
        "status": str(results.solver.termination_condition),
        "objective": round(float(pyo.value(model.obj)), 4),
        "solution": solution
    }
else:
    result = {
        "status": "FAILURE",
        "solver_status": str(results.solver.status),
        "termination_condition": str(results.solver.termination_condition)
    }

print(f"RESULT_JSON:{json.dumps(result)}")
```

### Common Pitfalls
- Not checking termination condition for feasibility when optimal is not achieved.
- Using `pyo.value()` on uninitialized variables after a failed solve.
- Forgetting to convert Pyomo numeric values to Python floats for JSON serialization.
