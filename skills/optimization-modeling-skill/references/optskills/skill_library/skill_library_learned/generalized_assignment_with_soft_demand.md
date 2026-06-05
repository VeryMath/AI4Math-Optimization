---
name: Generalized Assignment with Soft Demand
description: |
  Model employee-to-shift assignments with skill and availability constraints, minimizing preference costs and penalties for unmet demand, then solve with deterministic configuration and robust verification.

---
# Workflow 1 (CP-SAT with Explicit Soft Constraints)

## Modeling stage

### Strategy Overview
Formulate as a CP-SAT model using binary assignment variables and explicit integer slack variables for unfulfilled demand, enabling direct penalty costs. Constraints are implemented as linear inequalities to filter ineligible assignments and enforce single assignments.

### Step 1 - Define Variables and Parameters
- Use dictionaries to store parameters: `demand[(r, s)]`, `preference_cost[(e, r, s)]`, `availability[(e, s)]`, `has_skill[e]`, `penalty_cost`.
- Create binary decision variables `assign[(e, r, s)]` for each employee-restaurant-shift combination.
- Create integer decision variables `unfulfilled[(r, s)]` to represent slack in demand coverage.

### Step 2 - Implement Demand Coverage as Soft Constraint
- For each (restaurant, shift) pair, add constraint: `sum(assign[(e, r, s)] for e in employees) + unfulfilled[(r, s)] == demand[(r, s)]`.
- This allows demand to be partially met, with `unfulfilled` incurring a penalty.

### Step 3 - Enforce Eligibility via Upper Bounds
- Add constraint `assign[(e, r, s)] <= availability[(e, s)]` for each employee-restaurant-shift.
- Add constraint `assign[(e, r, s)] <= has_skill[e]` for each employee-restaurant-shift.
- These inequalities automatically set assignment to zero where the employee is unavailable or unskilled.

### Step 4 - Limit Employee Assignments
- For each employee, add constraint: `sum(assign[(e, r, s)] for r in restaurants, s in shifts) <= 1`.
- This ensures an employee is assigned at most once.

### Step 5 - Construct Linear Objective
- Minimize `sum(preference_cost[(e, r, s)] * assign[(e, r, s)] for all e, r, s) + penalty_cost * sum(unfulfilled[(r, s)] for all r, s)`.

### Formulation Template
```json
{
  "sets": ["employees", "restaurants", "shifts"],
  "parameters": ["demand", "preference_cost", "availability", "has_skill", "penalty_cost"],
  "decision_variables": ["assign[employees, restaurants, shifts]", "unfulfilled[restaurants, shifts]"],
  "objective": {
    "sense": "min",
    "expression": "sum(preference_cost * assign) + penalty_cost * sum(unfulfilled)"
  },
  "constraints": [
    "demand_coverage: sum(assign[e, r, s]) + unfulfilled[r, s] == demand[r, s] for all r, s",
    "availability: assign[e, r, s] <= availability[e, s] for all e, r, s",
    "skill_requirement: assign[e, r, s] <= has_skill[e] for all e, r, s",
    "one_assignment_per_employee: sum(assign[e, r, s]) <= 1 for all e"
  ]
}
```

### Common Pitfalls
- Forgetting to define `unfulfilled` as a non-negative integer variable, leading to model errors.
- Using equality for availability/skill constraints instead of inequality, which over-constrains the model.
- Not parameterizing the penalty cost, making the model less reusable for different scenarios.

## Solving stage

### Strategy Overview
Configure the CP-SAT solver for deterministic, reproducible search with a time limit. After solving, rigorously check the status and solution feasibility, then extract and verify results.

### Step 1 - Configure Solver Parameters
- Set `solver.parameters.max_time_in_seconds = 30` to bound runtime.
- Set `solver.parameters.num_search_workers = 8` to utilize parallel search.
- Set `solver.parameters.random_seed = 42` for reproducibility.
- Set `solver.parameters.relative_gap_limit = 0.0` to seek proven optimality.

### Step 2 - Solve and Check Status
- Call `solver.Solve(model)`.
- Check if `status` is `OPTIMAL` or `FEASIBLE`. Treat both as successful.
- If status is `UNKNOWN` or `MODEL_INVALID`, log parameters and model details for debugging.

### Step 3 - Extract and Verify Solution
- If solved successfully, use `solver.Value(variable)` to get all assignment and unfulfilled variable values.
- Use `solver.ObjectiveValue()` to get the total cost.
- Programmatically verify all constraints are satisfied using the extracted values.
- Calculate preference cost and penalty cost components separately for reporting.

### Step 4 - Analyze Bottlenecks (If Penalties Exist)
- For any (restaurant, shift) with `unfulfilled > 0`, compare total qualified/available employees against demand to confirm the penalty is structurally necessary.

### Code Usage
```python
# build model from formulation
model = cp_model.CpModel()
# ... build variables, constraints, objective ...
solver = cp_model.CpSolver()
# apply parameter configuration
solver.parameters.max_time_in_seconds = 30
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42
solver.parameters.relative_gap_limit = 0.0

# solve with status / termination checks
status = solver.Solve(model)
if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    # extract solution
    assignments = {(e,r,s): solver.Value(assign_var) for ...}
    unfulfilled = {(r,s): solver.Value(unfulfilled_var) for ...}
    total_cost = solver.ObjectiveValue()
    # verify constraints and calculate cost breakdown
else:
    print(f"Solver failed with status: {status}")
```

### Common Pitfalls
- Assuming `OPTIMAL` is the only acceptable status; `FEASIBLE` is also valid for satisficing.
- Not verifying the solution against original constraints, potentially missing solver errors.
- Misinterpreting floating-point objective values; round to nearest integer if necessary.

# Workflow 2 (Pyomo with MIP Solver)

## Modeling stage

### Strategy Overview
Build a Pyomo `ConcreteModel` using `Var`, `Constraint`, and `Objective` components. Use `Param` objects for data to separate model logic from instance values. Structure constraints in a logical hierarchy for clarity.

### Step 1 - Declare Sets and Parameters
- Define Pyomo `Set` objects for `employees`, `restaurants`, `shifts`.
- Define `Param` objects for `demand`, `preference_cost`, `availability`, `has_skill`, `penalty_cost`, initialized from data dictionaries.

### Step 2 - Define Decision Variables
- Create `Var(..., domain=Binary)` for `model.x[employee, restaurant, shift]`.
- Create `Var(..., domain=NonNegativeIntegers)` for `model.u[restaurant, shift]`.

### Step 3 - Build Constraint Rules
- Implement `demand_coverage` rule returning `sum(model.x[e,r,s] for e in employees) + model.u[r,s] == demand[r,s]`.
- Implement `availability` rule returning `model.x[e,r,s] <= availability[e,s]`.
- Implement `skill_requirement` rule returning `model.x[e,r,s] <= has_skill[e]`.
- Implement `one_assignment` rule returning `sum(model.x[e,r,s] for r in restaurants, s in shifts) <= 1`.

### Step 4 - Define the Objective
- Create an `Objective` rule minimizing `sum(preference_cost[e,r,s] * model.x[e,r,s] for all e,r,s) + penalty_cost * sum(model.u[r,s] for all r,s)`.

### Step 5 - Return Model and Data for Post-Processing
- Structure the model-building function to return the `model` object and the data dictionaries to avoid scope issues during solution analysis.

### Formulation Template
```json
{
  "sets": ["employees", "restaurants", "shifts"],
  "parameters": ["demand", "preference_cost", "availability", "has_skill", "penalty_cost"],
  "decision_variables": ["x[employees, restaurants, shifts]", "u[restaurants, shifts]"],
  "objective": {
    "sense": "minimize",
    "expression": "sum(preference_cost * x) + penalty_cost * sum(u)"
  },
  "constraints": [
    "demand_coverage: sum(x[e, r, s]) + u[r, s] == demand[r, s] for all r, s",
    "availability: x[e, r, s] <= availability[e, s] for all e, r, s",
    "skill_requirement: x[e, r, s] <= has_skill[e] for all e, r, s",
    "one_assignment_per_employee: sum(x[e, r, s]) <= 1 for all e"
  ]
}
```

### Common Pitfalls
- Defining `Param` objects without initializing them, causing build errors.
- Using Python's global variables inside Pyomo rule functions, leading to unpredictable behavior.
- Not defining variable domains correctly (e.g., `NonNegativeIntegers` for slack variables).

## Solving stage

### Strategy Overview
Solve the Pyomo model using a MIP solver (e.g., Gurobi, CBC) with deterministic settings. Check termination condition and solution status rigorously, then extract and verify results.

### Step 1 - Configure Solver for Deterministic Optimality
- Instantiate the solver (e.g., `SolverFactory('gurobi')`).
- Set options: `'TimeLimit'=30`, `'MIPGap'=0.0`, `'Threads'=4`, `'Seed'=42` to ensure reproducibility and a push for proven optimality.

### Step 2 - Solve and Check Termination Status
- Call `results = solver.solve(model, tee=True)` to solve with log output.
- Check `results.solver.status` is `SolverStatus.ok`.
- Check `results.solver.termination_condition` is `optimal` or `feasible`. Handle other conditions as failures.

### Step 3 - Extract Solution and Verify
- If solved successfully, load solution into model: `model.solutions.load_from(results)`.
- Extract variable values via `model.x[emp, rest, shift].value` and `model.u[rest, shift].value`.
- Programmatically verify all constraints are satisfied using the extracted values.
- Calculate total cost and its breakdown (preference vs. penalty) for reporting.

### Step 4 - Perform Bottleneck Analysis
- If any `model.u[...].value > 0`, analyze the corresponding demand and qualified/available employee count to confirm infeasibility is structural.

### Step 5 - Output Structured Results
- Print a summary table of assignments by shift and restaurant.
- Print employee assignment details including cost contribution.
- Print constraint checks to confirm model correctness.

### Code Usage
```python
# build model from formulation
def build_model(data_dict):
    model = ConcreteModel()
    # ... define sets, params, variables, constraints, objective ...
    return model, data_dict

model, data = build_model(instance_data)
solver = SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

# solve with status / termination checks
results = solver.solve(model, tee=True)
if results.solver.status == SolverStatus.ok and results.solver.termination_condition in ['optimal', 'feasible']:
    model.solutions.load_from(results)
    # extract solution and verify
    assignments = {(e,r,s): model.x[e,r,s].value for ...}
    unfulfilled = {(r,s): model.u[r,s].value for ...}
    # perform verification and analysis
else:
    print(f"Solver failed: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, potentially accepting incomplete solutions.
- Forgetting to load the solution before accessing variable values, resulting in `None`.
- Using `tee=False` in final runs, missing solver logs that confirm optimality and zero MIP gap.
