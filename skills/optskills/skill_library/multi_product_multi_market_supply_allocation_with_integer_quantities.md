---
name: Multi-Product Multi-Market Supply Allocation with Integer Quantities
description: |
  Models and solves a profit-maximizing supply allocation problem with integer quantities across multiple products and markets, using either OR-Tools or Pyomo with equality demand constraints.
---

# Workflow 1 (OR-Tools SCIP Solver)

## Modeling stage

### Strategy Overview
Build a mixed-integer programming model using Google OR-Tools' pywraplp interface. Define integer decision variables for each source-product-market triplet, enforce demand fulfillment with equality constraints, and maximize total profit using linear coefficients.

### Step 1 - Define Data Structures
- Organize input data as nested dictionaries: `profit[source][product][market]` for profit per unit, `demand[product][market]` for required quantities.
- Precompute an upper bound for each decision variable as the corresponding demand value to tighten the formulation.

### Step 2 - Create Solver and Decision Variables
- Instantiate a solver with `pywraplp.Solver.CreateSolver("SCIP")`.
- For each combination of source, product, and market, create an integer variable using `solver.IntVar(0, demand[product][market], name)` to enforce non-negativity and integrality.

### Step 3 - Add Demand Fulfillment Constraints
- For each product-market pair, sum all source variables for that pair and set equality to the demand: `solver.Add(sum(variables) == demand[product][market])`.

### Step 4 - Build Objective Function
- Create an empty objective with `solver.Objective()`.
- Iterate over all decision variables, setting their profit coefficients with `objective.SetCoefficient(variable, profit_value)`.
- Call `objective.SetMaximization()` to set the sense.

### Formulation Template
```json
{
  "sets": ["Sources", "Products", "Markets"],
  "parameters": [
    "profit[source, product, market]",
    "demand[product, market]"
  ],
  "decision_variables": [
    "supply[source, product, market] (integer, 0..demand[product, market])"
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[source, product, market] * supply[source, product, market] for all indices)"
  },
  "constraints": [
    "for each (product, market): sum(supply[source, product, market] over sources) == demand[product, market]"
  ]
}
```

### Common Pitfalls
- Using `solver.IntVar` without an upper bound can lead to unbounded search space; always bound by demand.
- Forgetting to call `objective.SetMaximization()` results in a default minimization objective.
- Naming variables with duplicate keys (e.g., same source-product-market) causes solver errors; ensure unique names.

## Solving stage

### Strategy Overview
Configure the SCIP solver with a time limit and optional parallelism, solve the model, and parse results with explicit status checks. Output results in a structured JSON format prefixed with `RESULT_JSON:` for downstream parsing.

### Step 1 - Configure Solver Parameters
- Set a time limit with `solver.SetTimeLimit(30000)` (30 seconds in milliseconds).
- Optionally enable parallel solving with `solver.SetNumThreads(4)`.

### Step 2 - Solve and Check Status
- Call `status = solver.Solve()`.
- Check if status is `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` before extracting results.

### Step 3 - Extract and Format Results
- Retrieve objective value with `objective.Value()`.
- Iterate over all variables, collecting `variable.name()` and `variable.solution_value()` for non-zero values.
- Print a JSON string with keys `"status"`, `"objective_value"`, and `"solution"`, prefixed by `RESULT_JSON:`.

### Step 4 - Handle Failures
- If solver is `None` after creation, print `{"status": "failed", "reason": "Solver not available"}`.
- For infeasible or error statuses, print a JSON with `"status": "failed"` and include the solver status code.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import json

def solve_supply_allocation(profit, demand, sources, products, markets):
    solver = pywraplp.Solver.CreateSolver("SCIP")
    if not solver:
        print('RESULT_JSON:{"status": "failed", "reason": "SCIP solver not available"}')
        return

    # Decision variables
    supply = {}
    for s in sources:
        for p in products:
            for m in markets:
                ub = demand.get(p, {}).get(m, 0)
                supply[(s, p, m)] = solver.IntVar(0, ub, f'supply_{s}_{p}_{m}')

    # Demand constraints
    for p in products:
        for m in markets:
            solver.Add(sum(supply[(s, p, m)] for s in sources) == demand[p][m])

    # Objective
    objective = solver.Objective()
    for s in sources:
        for p in products:
            for m in markets:
                objective.SetCoefficient(supply[(s, p, m)], profit[s][p][m])
    objective.SetMaximization()

    # Solve
    solver.SetTimeLimit(30000)
    solver.SetNumThreads(4)
    status = solver.Solve()

    if status in (pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE):
        result = {
            "status": "optimal" if status == pywraplp.Solver.OPTIMAL else "feasible",
            "objective_value": objective.Value(),
            "solution": {}
        }
        for (s, p, m), var in supply.items():
            val = var.solution_value()
            if val > 0:
                result["solution"][f"{s}_{p}_{m}"] = int(val)
        print(f'RESULT_JSON:{json.dumps(result)}')
    else:
        print(f'RESULT_JSON:{{"status": "failed", "solver_status": {status}}}')
```

### Common Pitfalls
- Not checking if solver creation returns `None` leads to runtime errors on systems without SCIP.
- Using `solver.SetTimeLimit` with milliseconds instead of seconds; 30000 = 30 seconds.
- Forgetting to convert `solution_value()` to native Python types before JSON serialization.

# Workflow 2 (Pyomo with CBC Solver)

## Modeling stage

### Strategy Overview
Construct a Pyomo ConcreteModel with separate Set objects for sources, products, and markets. Define a 3-index integer decision variable, enforce demand equality constraints using constraint rules, and maximize profit with a linear objective expression.

### Step 1 - Define Index Sets
- Create Pyomo Set objects: `model.SOURCES = pyo.Set(initialize=sources)`, `model.PRODUCTS = pyo.Set(initialize=products)`, `model.MARKETS = pyo.Set(initialize=markets)`.
- Use distinct variable names for model attributes and loop variables to avoid name conflicts (e.g., use `mk` for market index, not `m`).

### Step 2 - Declare Decision Variables
- Define `model.supply = pyo.Var(model.SOURCES, model.PRODUCTS, model.MARKETS, domain=pyo.NonNegativeIntegers)` for integer supply quantities.

### Step 3 - Add Demand Fulfillment Constraints
- Write a constraint rule: `def demand_rule(model, p, mk): return sum(model.supply[s, p, mk] for s in model.SOURCES) == demand[p][mk]`.
- Add the constraint with `model.demand_con = pyo.Constraint(model.PRODUCTS, model.MARKETS, rule=demand_rule)`.

### Step 4 - Build Objective Function
- Define the objective expression: `model.obj = pyo.Objective(expr=sum(profit[s][p][mk] * model.supply[s, p, mk] for s in model.SOURCES for p in model.PRODUCTS for mk in model.MARKETS), sense=pyo.maximize)`.

### Formulation Template
```json
{
  "sets": ["SOURCES", "PRODUCTS", "MARKETS"],
  "parameters": [
    "profit[source, product, market]",
    "demand[product, market]"
  ],
  "decision_variables": [
    "supply[source, product, market] (NonNegativeIntegers)"
  ],
  "objective": {
    "sense": "maximize",
    "expression": "sum(profit[s, p, m] * supply[s, p, m] for all indices)"
  },
  "constraints": [
    "for each (product, market): sum(supply[source, product, market] over sources) == demand[product, market]"
  ]
}
```

### Common Pitfalls
- Reusing the model variable name (e.g., `m`) as a loop variable inside constraint rules or generator expressions causes attribute errors; use distinct names like `mk` for market.
- Forgetting to import `pyo.environ` or using incorrect domain names (e.g., `NonNegativeIntegers` vs `NonNegativeInteger`).
- Using mutable data structures (e.g., lists) as set elements; Pyomo requires hashable types.

## Solving stage

### Strategy Overview
Use the CBC solver via Pyomo's SolverFactory with optimality gap and time limit settings. Check solver status and termination condition before extracting results, and output the objective value in a parseable format.

### Step 1 - Configure Solver
- Create solver instance: `solver = pyo.SolverFactory("cbc")`.
- Set options: `solver.options["seconds"] = 30` for time limit, `solver.options["ratio"] = 0.0` for zero MIP gap (optimality required).

### Step 2 - Solve Model
- Call `result = solver.solve(model, tee=False)` to suppress solver output.

### Step 3 - Check Status and Extract Results
- Verify `result.solver.status == SolverStatus.ok` and `result.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Extract objective value: `obj_val = float(pyo.value(model.obj))`.
- Print in format: `print(f"RESULT:{obj_val}")`.
- For solution inspection, iterate over `model.supply` indices and collect non-zero values: `{str(idx): int(pyo.value(var)) for idx, var in model.supply.items() if pyo.value(var) > 0}`.

### Step 4 - Handle Failures
- If status is not ok or termination condition is unexpected, print a JSON payload: `{"status": "failed", "reason": str(result.solver.termination_condition)}`.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_supply_allocation_pyomo(profit, demand, sources, products, markets):
    model = pyo.ConcreteModel()
    model.SOURCES = pyo.Set(initialize=sources)
    model.PRODUCTS = pyo.Set(initialize=products)
    model.MARKETS = pyo.Set(initialize=markets)

    model.supply = pyo.Var(model.SOURCES, model.PRODUCTS, model.MARKETS, domain=pyo.NonNegativeIntegers)

    def demand_rule(model, p, mk):
        return sum(model.supply[s, p, mk] for s in model.SOURCES) == demand[p][mk]
    model.demand_con = pyo.Constraint(model.PRODUCTS, model.MARKETS, rule=demand_rule)

    model.obj = pyo.Objective(
        expr=sum(profit[s][p][mk] * model.supply[s, p, mk]
                 for s in model.SOURCES for p in model.PRODUCTS for mk in model.MARKETS),
        sense=pyo.maximize
    )

    solver = pyo.SolverFactory("cbc")
    solver.options["seconds"] = 30
    solver.options["ratio"] = 0.0
    result = solver.solve(model, tee=False)

    if result.solver.status == SolverStatus.ok and \
       result.solver.termination_condition in (TerminationCondition.optimal, TerminationCondition.feasible):
        obj_val = float(pyo.value(model.obj))
        print(f"RESULT:{obj_val}")
        # Optional: detailed solution
        solution = {str(idx): int(pyo.value(var))
                    for idx, var in model.supply.items() if pyo.value(var) > 0}
        print(f"SOLUTION:{solution}")
    else:
        print(f'{{"status": "failed", "reason": "{result.solver.termination_condition}"}}')
```

### Common Pitfalls
- Not importing `SolverStatus` and `TerminationCondition` from `pyomo.opt` leads to NameError in status checks.
- Setting `ratio` to 0.0 may cause long solve times for large instances; consider relaxing to 0.01 for practical use.
- Forgetting to convert `pyo.value()` results to native Python types before printing or serialization.
