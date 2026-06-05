---
name: Cutting Stock - Pattern-Based Integer Optimization
description: |
  Model and solve one-dimensional cutting stock problems by enumerating feasible patterns, formulating a pattern-based integer program to minimize total stock items used, and solving with a MIP solver.

---
# Workflow 1 (Pyomo with CBC/Highs)

## Modeling stage

### Strategy Overview
Use Pyomo for model definition, separating pattern generation from optimization. Employ a set-based formulation for clarity and scalability, suitable for problems with a moderate number of feasible patterns.

### Step 1 - Generate Feasible Patterns
- For each item type `i`, compute `max_count_i = stock_length // item_length_i`.
- Use `itertools.product` over ranges `[0, max_count_i]` to generate all candidate combinations.
- Filter combinations where the total used length is positive (`> 0`) and does not exceed the stock capacity (`<= stock_length`).
- Store each valid pattern as a list of item counts and index them.

### Step 2 - Define Model Sets and Parameters
- Define a set `P` for pattern indices and a set `I` for item types.
- Create a parameter `a[i, p]` mapping pattern `p` to the number of items of type `i` it produces.
- Initialize this parameter from the pre-generated pattern data using a dictionary comprehension.

### Step 3 - Define Variables and Objective
- Define non-negative integer variables `x[p]` representing the usage count of each pattern `p`.
- Set the objective to minimize the sum of all `x[p]` (total stock items used).

### Step 4 - Formulate Demand Constraints
- For each item type `i`, add a constraint ensuring total production meets or exceeds demand: `sum(a[i, p] * x[p] for p in P) >= demand[i]`.

### Formulation Template
```json
{
  "sets": [
    "P: set of pattern indices",
    "I: set of item types"
  ],
  "parameters": [
    "demand[i]: demand for item type i",
    "a[i, p]: number of items of type i produced by pattern p"
  ],
  "decision_variables": [
    "x[p]: integer, non-negative, usage count of pattern p"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(x[p] for p in P)"
  },
  "constraints": [
    "demand_satisfaction[i]: sum(a[i, p] * x[p] for p in P) >= demand[i], for all i in I"
  ]
}
```

### Common Pitfalls
- Generating an excessive number of patterns for large problems, leading to intractable model size.
- Forgetting to filter out patterns with zero total used length, which are trivially feasible but useless.
- Using float equality checks (`==`) for demand constraints; use `>=` to allow overproduction.
- Not defining `x[p]` as `pyo.Integers` or `pyo.NonNegativeIntegers`, leading to a relaxed LP.

## Solving stage

### Strategy Overview
Solve the Pyomo model using the CBC or Highs solver via the `SolverFactory`. Configure solver options for performance, verify solution status, and extract results with robust post-solution verification.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory('cbc')` or `pyo.SolverFactory('highs')`.
- Set key options: `time_limit`, `mip_rel_gap` (e.g., `0.0` for exact), and `threads`.
- Solve the model with `results = solver.solve(model, tee=False)`.

### Step 2 - Verify Solution Status
- Check `results.solver.status` and `results.solver.termination_condition`.
- Accept solutions marked as `optimal` or `feasible`. Handle `infeasible` or `unbounded` statuses with appropriate error messages.

### Step 3 - Extract and Verify Solution
- Iterate over pattern variables `x[p]` and collect those with value > 0.5 (accounting for solver tolerance).
- For each used pattern, record its composition and usage count.
- Recalculate total production per item type from the solution and verify it meets all demands.
- Compute secondary metrics:
  - **Total Waste**: `sum(pattern_count * (stock_length - pattern_used_length))`.
  - **Utilization Efficiency**: `(total_length_used / (total_stock_items_used * stock_length)) * 100`.
  - **Theoretical Lower Bound**: `ceil(total_required_length / stock_length)` where `total_required_length = sum(demand[i] * item_lengths[i])`. Compare to the solution's total items used.

### Step 4 - Output Interpretable Results
- Print a summary of used patterns, their counts, and associated waste.
- Compare the total items used to the theoretical lower bound to assess optimality.
- Use plain text markers (e.g., "(OK)") for robust output across environments.

### Code Usage
```python
import pyomo.environ as pyo
import itertools

# 1. Generate patterns (example structure)
patterns = []  # list of pattern lists
max_counts = [stock_length // length for length in item_lengths]
for counts in itertools.product(*[range(mc+1) for mc in max_counts]):
    total = sum(c*l for c,l in zip(counts, item_lengths))
    if 0 < total <= stock_length:
        patterns.append(list(counts))

# 2. Build model
model = pyo.ConcreteModel()
model.P = pyo.Set(initialize=range(len(patterns)))
model.I = pyo.Set(initialize=range(num_item_types))

def a_init(model, i, p):
    return patterns[p][i]
model.a = pyo.Param(model.I, model.P, initialize=a_init)

model.x = pyo.Var(model.P, domain=pyo.NonNegativeIntegers)

def obj_rule(model):
    return sum(model.x[p] for p in model.P)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.minimize)

def demand_rule(model, i):
    return sum(model.a[i, p] * model.x[p] for p in model.P) >= demand[i]
model.demand_con = pyo.Constraint(model.I, rule=demand_rule)

# 3. Solve
solver = pyo.SolverFactory('cbc')
solver.options['seconds'] = 30
results = solver.solve(model)

# 4. Check status and extract
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    for p in model.P:
        if pyo.value(model.x[p]) > 0.5:
            print(f"Pattern {p}: Use {pyo.value(model.x[p])} times")
else:
    print(f"Solver terminated with status: {results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking solver status before extracting variable values, leading to errors.
- Using a loose MIP gap (`mip_rel_gap`) when an exact integer solution is required.
- Misinterpreting variable values due to solver tolerance; use a threshold (e.g., `> 0.5`) for integer variables.
- Forgetting to set `tee=True` during development for debugging solver progress.

# Workflow 2 (OR-Tools with SCIP/CBC)

## Modeling stage

### Strategy Overview
Use Google's OR-Tools CP-SAT or MPSolver for a more procedural API. It is well-suited for integration into larger applications and offers fine-grained control over the solving process.

### Step 1 - Generate Feasible Patterns
- Identical to Workflow 1: enumerate all item count combinations within stock capacity.
- Store patterns in a list-of-lists structure for efficient coefficient access.

### Step 2 - Initialize Solver and Variables
- Create a solver instance: `solver = pywraplp.Solver.CreateSolver('SCIP')` or `'CBC'`.
- Define integer variables `x[j]` for each pattern `j` with a lower bound of 0 and no upper bound (`solver.IntVar` or `solver.NumVar` with integer=True).

### Step 3 - Build Demand Constraints
- For each item type `i`, create a constraint object: `constraint = solver.Constraint(demand[i], solver.infinity())`.
- For each pattern `j`, set the coefficient: `constraint.SetCoefficient(x[j], pattern_item_count[i][j])`.

### Step 4 - Define Objective Function
- Create the objective: `objective = solver.Objective()`.
- Set all variable coefficients in the objective to 1.
- Set the optimization sense to minimization.

### Formulation Template
```json
{
  "sets": [
    "P: set of pattern indices",
    "I: set of item types"
  ],
  "parameters": [
    "demand[i]: demand for item type i",
    "a[i][p]: number of items of type i produced by pattern p (list of lists)"
  ],
  "decision_variables": [
    "x[p]: integer, non-negative, usage count of pattern p"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum(x[p] for p in P)"
  },
  "constraints": [
    "demand_satisfaction[i]: sum(a[i][p] * x[p] for p in P) >= demand[i], for all i in I"
  ]
}
```

### Common Pitfalls
- Using `solver.NumVar` without setting `integer=True`, resulting in a continuous relaxation.
- Incorrectly setting constraint bounds; the lower bound should be the demand, and the upper bound `solver.infinity()` for a `>=` constraint.
- Not leveraging OR-Tools' pattern for efficient model construction (e.g., building constraints in loops).
- Assuming the solver automatically finds integer solutions; always specify the variable domain.

## Solving stage

### Strategy Overview
Solve the model using OR-Tools' solver, which provides a simple `Solve()` call. The focus is on efficient model construction, solution extraction, and verification.

### Step 1 - Execute Solver
- Call `solver.Solve()` and capture the result status.

### Step 2 - Interpret Solver Result
- Check the result status: `pywraplp.Solver.OPTIMAL` or `pywraplp.Solver.FEASIBLE` indicate a valid solution.
- Handle `INFEASIBLE` or `UNBOUNDED` statuses appropriately.

### Step 3 - Extract Solution and Verify
- For each pattern variable `x[j]`, get its solution value using `x[j].solution_value()`.
- Filter patterns with value > 0.5.
- Recalculate total production per item type and verify against demands.
- Compute total waste and utilization efficiency (as defined in Workflow 1).

### Step 4 - Output Production Instructions
- Print a detailed report listing each used pattern, its composition, usage count, and waste per unit.
- Summarize total stock items used and overall waste.
- Use plain text markers for robust output.

### Code Usage
```python
from ortools.linear_solver import pywraplp

# 1. Generate patterns (example structure)
patterns = []  # list of pattern lists
max_counts = [stock_length // length for length in item_lengths]
for counts in itertools.product(*[range(mc+1) for mc in max_counts]):
    total = sum(c*l for c,l in zip(counts, item_lengths))
    if 0 < total <= stock_length:
        patterns.append(list(counts))

# 2. Initialize solver and variables
solver = pywraplp.Solver.CreateSolver('SCIP')
x = []
for j in range(len(patterns)):
    x.append(solver.IntVar(0, solver.infinity(), f'x_{j}'))

# 3. Add demand constraints
for i in range(num_item_types):
    constraint = solver.Constraint(demand[i], solver.infinity())
    for j in range(len(patterns)):
        constraint.SetCoefficient(x[j], patterns[j][i])

# 4. Set objective
objective = solver.Objective()
for j in range(len(patterns)):
    objective.SetCoefficient(x[j], 1)
objective.SetMinimization()

# 5. Solve
status = solver.Solve()

# 6. Extract and verify
if status == pywraplp.Solver.OPTIMAL or status == pywraplp.Solver.FEASIBLE:
    used_patterns = []
    for j in range(len(patterns)):
        val = x[j].solution_value()
        if val > 0.5:
            used_patterns.append((j, val, patterns[j]))
    # ... verification and output ...
else:
    print(f"Solver did not find a solution. Status: {status}")
```

### Common Pitfalls
- Not checking the solver status, assuming `Solve()` always returns an optimal solution.
- Forgetting that `solution_value()` returns a float; use a tolerance when checking for integer usage.
- Building the model inefficiently in nested loops for large problems; pre-compute coefficients where possible.
- Misusing `solver.infinity()` for constraint upper bounds when a finite bound exists.
