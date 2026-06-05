---
name: Multi-Index Flow Allocation
description: |
  Model and solve linear profit maximization problems for allocating flows across multiple origins, types, and destinations with exact demand satisfaction.
---

# Workflow 1 (Google OR-Tools LP)

## Modeling stage

### Strategy Overview
Formulate the allocation problem as a pure Linear Program (LP) using the OR-Tools linear solver wrapper. This approach is suitable for continuous, non-negative flow variables with linear equality constraints and a linear objective.

### Step 1 - Define Data Structures
- Organize input data in nested lists or dictionaries that align with the multi-dimensional nature of the problem (e.g., origins, product types, destinations).
- Store profit coefficients in a 3D structure `profit[origin][type][destination]` and demand requirements in a 2D structure `demand[type][destination]`.

### Step 2 - Create Decision Variables
- Instantiate non-negative continuous variables for each flow path using `solver.NumVar(lb, ub, name)`.
- Use a naming convention that embeds indices (e.g., `f_o_t_d`) for traceability.
- Set lower bound to 0 and upper bound to `solver.infinity()` to enforce non-negativity without explicit capacity.

### Step 3 - Formulate Demand Satisfaction Constraints
- For each product type and destination pair, create a linear equality constraint.
- Use `solver.Add(sum(variables) == demand_value)` to enforce that the total flow from all origins equals the exact demand.
- Iterate over all type-destination combinations to add the full set of constraints.

### Step 4 - Define Linear Objective
- Create the objective expression using `solver.Objective()`.
- Iterate through all variables, setting their coefficients with `objective.SetCoefficient(var, profit_coefficient)`.
- Set the objective sense to maximization.

### Formulation Template
```json
{
  "sets": [
    "origins (O)",
    "types (T)",
    "destinations (D)"
  ],
  "parameters": [
    "profit[o][t][d]: unit profit for flow from origin o of type t to destination d",
    "demand[t][d]: required quantity of type t at destination d"
  ],
  "decision_variables": [
    "x[o][t][d] >= 0: flow quantity from origin o of type t to destination d"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum_{o in O, t in T, d in D} profit[o][t][d] * x[o][t][d]"
  },
  "constraints": [
    "demand_satisfaction[t in T, d in D]: sum_{o in O} x[o][t][d] == demand[t][d]"
  ]
}
```

### Common Pitfalls
- Mismatching indices between profit data and variable creation loops, leading to incorrect objective coefficients.
- Forgetting to set the objective sense, defaulting to minimization.
- Using integer or boolean variable types for a continuous flow problem, unnecessarily complicating the solve.

## Solving stage

### Strategy Overview
Solve the LP model using the OR-Tools GLOP solver, which is designed for linear programming. Implement robust status checking, solution verification, and result extraction.

### Step 1 - Initialize Solver and Solve
- Create the solver instance: `solver = pywraplp.Solver.CreateSolver('GLOP')`.
- Invoke `solver.Solve()` and capture the result status.

### Step 2 - Check Solver Status
- Check the status against `solver.OPTIMAL` first, then `solver.FEASIBLE`.
- If status is not optimal or feasible, handle the error by reporting the status code and terminating gracefully.

### Step 3 - Extract and Verify Solution
- Retrieve the objective value using `solver.Objective().Value()`.
- For each demand constraint, compute the sum of solution values for the relevant variables and compare to the demand parameter within a small tolerance (e.g., 1e-6).
- Optionally, compute a theoretical upper bound (e.g., sum of max profit per demand) to sense-check optimality.

### Step 4 - Report Results
- Extract and print only non-zero flow variables (e.g., `solution_value() > 1e-6`) to reduce output clutter.
- Structure output for easy parsing, clearly stating the objective value and key allocations.

### Code Usage
```python
# build model from formulation
solver = pywraplp.Solver.CreateSolver('GLOP')
if not solver:
    raise Exception('Solver backend not available.')

# Create variables
x = {}
for o in origins:
    for t in types:
        for d in destinations:
            x[o,t,d] = solver.NumVar(0, solver.infinity(), f'x_{o}_{t}_{d}')

# Add constraints
for t in types:
    for d in destinations:
        ct = solver.Constraint(demand[t][d], demand[t][d])
        for o in origins:
            ct.SetCoefficient(x[o,t,d], 1)

# Set objective
objective = solver.Objective()
for o in origins:
    for t in types:
        for d in destinations:
            objective.SetCoefficient(x[o,t,d], profit[o][t][d])
objective.SetMaximization()

# solve with status / termination checks
status = solver.Solve()
if status == solver.OPTIMAL:
    print(f'Optimal objective value = {objective.Value()}')
    # Verification and result extraction
    for t in types:
        for d in destinations:
            total_flow = sum(x[o,t,d].solution_value() for o in origins)
            assert abs(total_flow - demand[t][d]) < 1e-6, f'Demand not met for {t},{d}'
    # Print non-zero flows
    for (o,t,d), var in x.items():
        val = var.solution_value()
        if val > 1e-6:
            print(f'  {var.name()} = {val}')
elif status == solver.FEASIBLE:
    print(f'Feasible solution found, objective = {objective.Value()}')
else:
    print('No optimal or feasible solution found.')
```

### Common Pitfalls
- Assuming the solver status is `OPTIMAL` without checking, leading to errors when accessing `solution_value()` on an unsolved model.
- Not verifying constraint satisfaction numerically, which can mask modeling errors or solver inaccuracies.
- Using a loose tolerance for checking non-zero flows, potentially filtering out small but meaningful values.

# Workflow 2 (Pyomo with Open-Source Solver)

## Modeling stage

### Strategy Overview
Model the problem using Pyomo's abstract or concrete modeling paradigm, defining sets, parameters, variables, and constraints in a declarative style. This separates the model definition from the solver interface, enhancing reusability.

### Step 1 - Define Pyomo Sets and Parameters
- Create Pyomo `Set` objects for origins, product types, and destinations.
- Define `Param` components for profit and demand, indexed over the appropriate sets. Use dictionaries for initialization.

### Step 2 - Declare Decision Variables
- Instantiate a `Var` component indexed over the Cartesian product of the sets.
- Specify `domain=pyo.NonNegativeReals` to enforce non-negativity.
- Optionally, set bounds here if capacity constraints exist.

### Step 3 - Construct Demand Constraints
- Use Pyomo's `Constraint` component with a rule function.
- The rule should, for each fixed type and destination, return the equality expression: `sum(model.x[o,t,d] for o in model.origins) == model.demand[t,d]`.

### Step 4 - Formulate the Objective
- Define an `Objective` component with a rule that sums `model.profit[o,t,d] * model.x[o,t,d]` over all indices.
- Set the `sense` to maximize.

### Formulation Template
```json
{
  "sets": [
    "O: set of origins",
    "T: set of product types",
    "D: set of destinations"
  ],
  "parameters": [
    "profit[o in O, t in T, d in D]: unit profit",
    "demand[t in T, d in D]: required quantity"
  ],
  "decision_variables": [
    "x[o in O, t in T, d in D] >= 0: flow quantity"
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( profit[o,t,d] * x[o,t,d] for o in O, t in T, d in D )"
  },
  "constraints": [
    "forall t in T, d in D: sum( x[o,t,d] for o in O ) == demand[t,d]"
  ]
}
```

### Common Pitfalls
- Defining parameters as plain Python dictionaries instead of Pyomo `Param` objects, which prevents proper indexing in constraints.
- Incorrectly nesting summation loops in constraint rules, leading to scalar constraints instead of indexed ones.
- Not initializing all set elements before using them in parameter or variable declarations.

## Solving stage

### Strategy Overview
Solve the Pyomo model using an open-source LP solver (e.g., CBC, GLPK) via Pyomo's `SolverFactory`. Configure solver options, check termination conditions rigorously, and extract solution values safely.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory('solver_name')`.
- Set options like time limit (`seconds`) and optimality tolerance (`ratio` for CBC).
- Call `results = solver.solve(model, tee=False)`.

### Step 2 - Inspect Solver Status and Termination Condition
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `TerminationCondition.optimal` (or `.feasible` for a sub-optimal but valid solution).
- If checks fail, output diagnostic information and do not proceed to value extraction.

### Step 3 - Validate Solution and Extract Values
- Use `pyo.value(model.objective)` to get the objective value.
- Programmatically verify each demand constraint by summing `pyo.value(model.x[o,t,d])` for fixed t,d and comparing to the demand parameter.
- Iterate through variables to collect non-zero allocations.

### Step 4 - Report and Handle Errors
- Print results in a structured format (e.g., key-value pairs or JSON) for automated parsing.
- In case of solver failure, output a JSON payload containing the status, termination condition, and any error messages.

### Code Usage
```python
# build model from formulation
import pyomo.environ as pyo

model = pyo.ConcreteModel()
model.O = pyo.Set(initialize=origins_list)
model.T = pyo.Set(initialize=types_list)
model.D = pyo.Set(initialize=destinations_list)

model.profit = pyo.Param(model.O, model.T, model.D, initialize=profit_dict)
model.demand = pyo.Param(model.T, model.D, initialize=demand_dict)

model.x = pyo.Var(model.O, model.T, model.D, domain=pyo.NonNegativeReals)

def demand_rule(model, t, d):
    return sum(model.x[o, t, d] for o in model.O) == model.demand[t, d]
model.demand_con = pyo.Constraint(model.T, model.D, rule=demand_rule)

def obj_rule(model):
    return sum(model.profit[o, t, d] * model.x[o, t, d] for o in model.O for t in model.T for d in model.D)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

if results.solver.status == pyo.SolverStatus.ok:
    if results.solver.termination_condition == pyo.TerminationCondition.optimal:
        print(f'RESULT:{pyo.value(model.obj)}')
        # Verification
        for t in model.T:
            for d in model.D:
                total = sum(pyo.value(model.x[o, t, d]) for o in model.O)
                assert abs(total - model.demand[t, d]) < 1e-6
        # Print non-zero flows
        for index in model.x.index_set():
            val = pyo.value(model.x[index])
            if val > 1e-6:
                print(f'  x{index} = {val}')
    elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
        print(f'Feasible solution found: {pyo.value(model.obj)}')
    else:
        print('Solver did not converge to an optimal solution.')
        payload = {'status': str(results.solver.status),
                   'termination': str(results.solver.termination_condition)}
        print(f'RESULT_JSON:{json.dumps(payload)}')
else:
    print('Solver failed.')
```

### Common Pitfalls
- Accessing `pyo.value()` on variables or objectives without first confirming a feasible solution exists, causing exceptions.
- Not setting a time limit for the solver, risking long runtimes on large instances.
- Confusing `SolverStatus` (ok/error) with `TerminationCondition` (optimal/feasible/infeasible). Both must be checked.
