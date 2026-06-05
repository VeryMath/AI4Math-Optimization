---
name: Multi-Commodity Flow Allocation
description: |
  Model and solve linear programs for allocating flows from multiple sources of multiple products to multiple destinations to maximize profit, with exact demand satisfaction and non-negative continuous variables.
---

# Workflow 1 (Exact Demand Fulfillment with HiGHS)

## Modeling stage

### Strategy Overview
Model the problem as a multi-source, multi-sink, multi-commodity flow linear program. Enforce exact demand satisfaction via equality constraints and maximize total profit. Use Pyomo's ConcreteModel with explicit set definitions and dictionary-based parameter indexing for clarity and maintainability.

### Step 1 - Define Sets and Indices
- Define the sets of sources (`model.SOURCES`), products (`model.PRODUCTS`), and destinations (`model.DESTINATIONS`) using Pyomo's `Set` component.

### Step 2 - Define Parameters
- Define a profit parameter `profit[source, product, destination]` representing the unit profit for each flow.
- Define a demand parameter `demand[destination, product]` representing the required quantity for each product at each destination.
- Use Pyomo's `Param` component initialized with nested dictionaries for intuitive multi-dimensional indexing.

### Step 3 - Define Decision Variables
- Define a continuous, non-negative decision variable `flow[source, product, destination]` representing the quantity allocated.
- Use `Var` with `domain=pyo.NonNegativeReals` and initialize it over the Cartesian product of the defined sets.

### Step 4 - Formulate Objective Function
- Formulate the objective to maximize total profit: `sum(profit[s, p, d] * flow[s, p, d] for s in SOURCES for p in PRODUCTS for d in DESTINATIONS)`.
- Attach it to the model as `model.obj` with `sense=pyo.maximize`.

### Step 5 - Formulate Demand Constraints
- For each product and destination pair, create a linear equality constraint ensuring the sum of flows from all sources equals the demand.
- Formulate as: `sum(flow[s, p, d] for s in SOURCES) == demand[d, p]`.

### Formulation Template
```json
{
  "sets": ["SOURCES", "PRODUCTS", "DESTINATIONS"],
  "parameters": [
    {"name": "profit", "dimensions": ["SOURCES", "PRODUCTS", "DESTINATIONS"]},
    {"name": "demand", "dimensions": ["DESTINATIONS", "PRODUCTS"]}
  ],
  "decision_variables": [
    {"name": "flow", "dimensions": ["SOURCES", "PRODUCTS", "DESTINATIONS"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s, p, d] * flow[s, p, d] for all s, p, d)"
  },
  "constraints": [
    {"name": "demand_satisfaction", "relation": "==", "expression": "sum(flow[s, p, d] for all s) == demand[d, p]", "for_all": ["d in DESTINATIONS", "p in PRODUCTS"]}
  ]
}
```

### Common Pitfalls
- Using equality constraints (`==`) when the problem allows supply to exceed demand (`<=`), which can make the model infeasible if supply is insufficient.
- Not defining capacity constraints for sources, which may lead to unrealistic solutions if sources have production limits.
- Hardcoding data with nested lists instead of dictionaries, reducing readability and making the model harder to maintain.

## Solving stage

### Strategy Overview
Solve the LP using the HiGHS solver via Pyomo, configured for performance and reliability. Include robust solution status checking, extraction of non-zero results, and a verification step to ensure correctness.

### Step 1 - Initialize Solver and Set Options
- Create a solver instance using `pyo.SolverFactory("highs")`.
- Configure solver options: set a time limit `[TIME_LIMIT]`, optimality gap tolerance to `0.0` for LP, and number of threads for parallel processing.

### Step 2 - Solve and Check Status
- Execute the solve command on the model instance.
- Check if the solver status is `SolverStatus.ok` and the termination condition is `optimal` or `feasible`. Proceed only if both checks pass.

### Step 3 - Extract and Process Solution
- Extract the objective function value using `pyo.value(model.obj)`.
- Iterate through all `model.flow` variables, collecting indices and values where the value exceeds a small tolerance (e.g., `1e-6`) to create a concise solution summary.

### Step 4 - Verify Solution Correctness
- For each product and destination pair, recalculate the total flow from the solution and verify it matches the demand parameter within a small tolerance (e.g., `1e-6`).
- Optionally, recalculate the total profit from the extracted flows to verify against the solver's reported objective.

### Step 5 - Output Results
- Print a human-readable summary including the objective value and key allocation statistics.
- Output a structured, machine-readable payload (e.g., JSON) containing the solve status, objective value, and the non-zero solution dictionary.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code as per Modeling Stage)

# Initialize solver
solver = pyo.SolverFactory('highs')
solver.options['time_limit'] = [TIME_LIMIT]
solver.options['mip_rel_gap'] = 0.0  # For pure LP
solver.options['threads'] = [N_THREADS]

# Solve
results = solver.solve(model, tee=False)  # Set tee=True for solver log

# Check status
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    # Extract non-zero flows
    solution = {}
    for idx in model.flow:
        val = pyo.value(model.flow[idx])
        if val > 1e-6:
            solution[idx] = val
    # Verification
    for d in model.DESTINATIONS:
        for p in model.PRODUCTS:
            calculated_demand = sum(pyo.value(model.flow[s, p, d]) for s in model.SOURCES)
            # Assert or log verification
            # assert abs(calculated_demand - model.demand[d, p]) < 1e-6
    # Output
    print(f"RESULT:{obj_val}")
    # ... output JSON payload
else:
    print(f"Solver failed. Status: {status}, Termination: {term}")
```

### Common Pitfalls
- Running redundant verification code that duplicates the solver's internal validation, adding unnecessary runtime.
- Not checking for alternative optimal solutions in degenerate problems (common in transportation-type LPs).
- Using Unicode characters in console output, which may cause encoding issues in some environments.

# Workflow 2 (Exact Demand Fulfillment with CBC)

## Modeling stage

### Strategy Overview
This workflow follows the same multi-commodity flow formulation but emphasizes Pyomo's rule-based constraint definitions and parameter initialization with explicit multi-dimensional keys. It is designed for compatibility with the COIN-OR CBC solver.

### Step 1 - Define Model and Sets
- Instantiate a `pyo.ConcreteModel()`.
- Define sets `model.S`, `model.P`, `model.M` for sources, products, and markets using `pyo.Set(initialize=...)`.

### Step 2 - Initialize Parameters with Dictionaries
- Create parameter dictionaries `profit_dict` and `demand_dict` where keys are tuples `(source, product, market)` and `(market, product)` respectively.
- Use `pyo.Param(model.S, model.P, model.M, initialize=profit_dict)` and `pyo.Param(model.M, model.P, initialize=demand_dict, mutable=True)`.

### Step 3 - Declare Variables with Rule-Based Domains
- Declare variable `model.x` indexed over `model.S * model.P * model.M`.
- Specify the domain as `domain=pyo.NonNegativeReals`.

### Step 4 - Build Objective with Summation
- Define the objective rule as `pyo.Objective(expr=sum(model.profit[s,p,m] * model.x[s,p,m] for s in model.S for p in model.P for m in model.M), sense=pyo.maximize)`.

### Step 5 - Build Constraints with Rule Functions
- Define a function `demand_rule(model, m, p)` that returns `sum(model.x[s,p,m] for s in model.S) == model.demand[m,p]`.
- Create the constraint using `pyo.Constraint(model.M, model.P, rule=demand_rule)`.

### Formulation Template
```json
{
  "sets": ["S", "P", "M"],
  "parameters": [
    {"name": "profit", "dimensions": ["S", "P", "M"], "structure": "dictionary with tuple keys"},
    {"name": "demand", "dimensions": ["M", "P"], "mutable": true}
  ],
  "decision_variables": [
    {"name": "x", "dimensions": ["S", "P", "M"], "domain": "NonNegativeReals"}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum(profit[s, p, m] * x[s, p, m] for all s, p, m)"
  },
  "constraints": [
    {"name": "demand_constraint", "relation": "==", "expression": "sum(x[s, p, m] for all s) == demand[m, p]", "for_all": ["m in M", "p in P"], "definition": "rule-based"}
  ]
}
```

### Common Pitfalls
- Assuming unlimited supply from all sources without modeling capacity constraints, which can lead to infeasible or unrealistic solutions if data changes.
- Using equality constraints rigidly; consider if `<=` constraints are more appropriate if oversupply is allowed.
- Not verifying that all indices in constraint rules align perfectly with the dimensions of the variables and parameters.

## Solving stage

### Strategy Overview
Solve the model using the CBC solver, configured via Pyomo. Include explicit handling of solver failures and structured output of results and diagnostics.

### Step 1 - Configure CBC Solver
- Create solver instance with `pyo.SolverFactory("cbc")`.
- Set solver options such as maximum seconds `[TIME_LIMIT]`, optimality gap (ratio) to `0.0`, and number of threads.

### Step 2 - Execute Solve with Diagnostics
- Call `solver.solve(model)`. Consider using `tee=True` for small problems to see the solver log for diagnostics.
- Capture the results object.

### Step 3 - Validate Solution Status
- Check `results.solver.status` and `results.solver.termination_condition`.
- Proceed only if status is `ok` and termination is `optimal` or `feasible`. Otherwise, handle the error.

### Step 4 - Extract and Summarize Solution
- Retrieve the objective value.
- Iterate over the model's variable index set, storing variable values that are significantly greater than zero (e.g., `> 1e-6`).
- Optionally, compute aggregate statistics (e.g., total flow per source).

### Step 5 - Verify and Report
- Perform a post-solve verification by iterating through the demand constraints and ensuring the sum of solution flows matches the demand within a small tolerance.
- Print a formatted summary of the solution, including status, objective, and a sample of allocations.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# ... (model building code as per Modeling Stage)

# Configure solver
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = [TIME_LIMIT]
solver.options['ratio'] = 0.0
solver.options['threads'] = [N_THREADS]

# Solve
results = solver.solve(model, tee=False)

# Validate and process
status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    obj_val = pyo.value(model.obj)
    # Build solution dictionary
    sol = {idx: pyo.value(model.x[idx]) for idx in model.x if pyo.value(model.x[idx]) > 1e-6}
    # Verification loop
    for m in model.M:
        for p in model.P:
            flow_to_market = sum(pyo.value(model.x[s, p, m]) for s in model.S)
            # Optional: print or assert verification
            # print(f"Market {m}, Product {p}: Demand={model.demand[m,p]}, Supplied={flow_to_market}")
    # Output
    print(f"Solver terminated with {term}. Objective: {obj_val:.2f}")
    # ... (structured output)
else:
    print(f"Solve unsuccessful. Status: {status}, Termination: {term}")
    # Handle failure (e.g., return empty result, raise warning)
```

### Common Pitfalls
- Solving the same problem twice in sequence without changing parameters, wasting computational resources.
- Not checking for multiple optimal solutions in degenerate linear programs.
- Hardcoding data structures in a way that makes the model difficult to adapt to different problem scales or data formats.
