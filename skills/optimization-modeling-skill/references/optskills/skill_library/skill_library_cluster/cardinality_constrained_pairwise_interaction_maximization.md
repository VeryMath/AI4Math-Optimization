---
name: Cardinality-Constrained Pairwise Interaction Maximization
description: |
  Model and solve selection problems where exactly K items are chosen to maximize the sum of directed pairwise interaction scores between selected items, using linearized binary variables and logical constraints.
---

# Workflow 1 (Pyomo with Gurobi/Highs)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using binary selection and interaction variables. Linearize the logical relationship between selection and interaction via constraints, enabling solution by standard MILP solvers.

### Step 1 - Define Sets and Parameters
- Define a set `NODES` representing all candidate items (e.g., nodes, elements).
- Define a parameter `SCORE[i, j]` for each ordered pair `(i, j)` where `i != j`, representing the directed interaction score from item `i` to item `j`.
- Define a scalar parameter `K` for the exact number of items to select.

### Step 2 - Define Decision Variables
- Create binary selection variables `x[i]` for each item `i` in `NODES`. `x[i] = 1` if item `i` is selected.
- Create binary interaction variables `y[i, j]` for each ordered pair `(i, j)` where `i != j`. `y[i, j] = 1` if the directed interaction from `i` to `j` is active (i.e., counted in the objective).

### Step 3 - Formulate Constraints
- Add a cardinality constraint: the sum of all `x[i]` must equal `K`.
- Add logical activation constraints: `y[i, j] <= x[i]` and `y[i, j] <= x[j]`. An interaction can only be active if both its source and target items are selected.
- Add a forcing constraint: `y[i, j] >= x[i] + x[j] - 1`. If both items are selected, the interaction variable must be active (equal to 1).

### Step 4 - Define Objective
- Maximize the sum of scores over all active directed interactions: `sum( SCORE[i, j] * y[i, j] for all i, j where i != j )`.

### Formulation Template
```json
{
  "sets": [
    {"name": "NODES", "description": "Set of all candidate items."},
    {"name": "ORDERED_PAIRS", "description": "Set of all ordered pairs (i, j) where i != j, i, j in NODES."}
  ],
  "parameters": [
    {"name": "SCORE", "index": "ORDERED_PAIRS", "description": "Directed interaction score from i to j."},
    {"name": "K", "description": "Exact number of items to select."}
  ],
  "decision_variables": [
    {"name": "x", "index": "NODES", "type": "binary", "description": "1 if item i is selected."},
    {"name": "y", "index": "ORDERED_PAIRS", "type": "binary", "description": "1 if directed interaction from i to j is active."}
  ],
  "objective": {
    "sense": "max",
    "expression": "sum( SCORE[i,j] * y[i,j] for (i,j) in ORDERED_PAIRS )"
  },
  "constraints": [
    {"name": "select_exactly_k", "expression": "sum( x[i] for i in NODES ) == K" },
    {"name": "y_leq_source", "expression": "y[i,j] <= x[i]", "index": "ORDERED_PAIRS"},
    {"name": "y_leq_target", "expression": "y[i,j] <= x[j]", "index": "ORDERED_PAIRS"},
    {"name": "y_geq_both_selected", "expression": "y[i,j] >= x[i] + x[j] - 1", "index": "ORDERED_PAIRS"}
  ]
}
```

### Common Pitfalls
- Assuming symmetric interaction scores without verifying the problem statement. Always clarify if `SCORE[i,j]` is directed or if the objective sums over unordered pairs.
- Creating overly complex formulations with unnecessary auxiliary variables for small problem instances where enumeration is feasible.
- Forgetting the forcing constraint (`y[i,j] >= x[i] + x[j] - 1`), which is necessary to correctly link the interaction variable to the selection variables.

## Solving stage

### Strategy Overview
Implement the MILP formulation in Pyomo and solve it using a high-performance solver like Gurobi or HiGHS. Configure solver parameters for performance and reliability, and implement robust status checking and result extraction.

### Step 1 - Model Construction
- Instantiate a `pyo.ConcreteModel()`.
- Define `pyo.Set` objects for `NODES` and `ORDERED_PAIRS`.
- Define `pyo.Param` objects for `SCORE` and `K`.
- Define `pyo.Var` objects for `x` and `y` with `domain=pyo.Binary`.

### Step 2 - Constraint and Objective Addition
- Add the cardinality constraint using `pyo.Constraint` and `sum()`.
- Add the three families of logical constraints using `pyo.Constraint` with rule functions or indexed constructions.
- Add the objective using `pyo.Objective` with `sense=pyo.maximize`.

### Step 3 - Solver Configuration and Execution
- Create a solver instance (e.g., `pyo.SolverFactory('gurobi')`).
- Set key solver parameters: `TimeLimit`, `MIPGap`, `Threads`, and `Seed` for reproducibility.
- Call `solver.solve(model, tee=False)` to execute the solve.

### Step 4 - Status Verification and Result Extraction
- Check the solver status (`pyo.SolverStatus`) and model termination condition (`pyo.TerminationCondition`).
- If the solution is optimal or feasible, extract the objective value using `pyo.value(model.obj)`.
- Iterate over the `x` and `y` variables to list selected items and active interactions.
- If the solve fails or is infeasible, return a structured error message.

### Code Usage
```python
import pyomo.environ as pyo

# 1. Build Model
model = pyo.ConcreteModel()
model.NODES = pyo.Set(initialize=NODES_LIST)
model.ORDERED_PAIRS = pyo.Set(initialize=ORDERED_PAIRS_LIST, dimen=2)

def score_init(model, i, j):
    return SCORE_DICT[(i, j)]
model.SCORE = pyo.Param(model.ORDERED_PAIRS, initialize=score_init)
model.K = pyo.Param(initialize=K_VALUE)

model.x = pyo.Var(model.NODES, domain=pyo.Binary)
model.y = pyo.Var(model.ORDERED_PAIRS, domain=pyo.Binary)

# 2. Add Constraints
def cardinality_rule(model):
    return sum(model.x[i] for i in model.NODES) == model.K
model.select_exactly_k = pyo.Constraint(rule=cardinality_rule)

def y_le_source_rule(model, i, j):
    return model.y[i, j] <= model.x[i]
model.y_le_source = pyo.Constraint(model.ORDERED_PAIRS, rule=y_le_source_rule)

def y_le_target_rule(model, i, j):
    return model.y[i, j] <= model.x[j]
model.y_le_target = pyo.Constraint(model.ORDERED_PAIRS, rule=y_le_target_rule)

def y_ge_both_rule(model, i, j):
    return model.y[i, j] >= model.x[i] + model.x[j] - 1
model.y_ge_both = pyo.Constraint(model.ORDERED_PAIRS, rule=y_ge_both_rule)

# 3. Add Objective
def obj_rule(model):
    return sum(model.SCORE[i, j] * model.y[i, j] for (i, j) in model.ORDERED_PAIRS)
model.obj = pyo.Objective(rule=obj_rule, sense=pyo.maximize)

# 4. Solve
solver = pyo.SolverFactory('gurobi') # or 'highs'
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42

results = solver.solve(model, tee=False)

# 5. Check Status and Extract Results
if (results.solver.status == pyo.SolverStatus.ok and
    results.solver.termination_condition == pyo.TerminationCondition.optimal):
    # Solution is optimal
    objective_value = pyo.value(model.obj)
    selected_items = [i for i in model.NODES if pyo.value(model.x[i]) > 0.5]
    # ... extract other results
else:
    # Handle non-optimal status (e.g., feasible, infeasible, error)
    # Return structured output with status info
```

### Common Pitfalls
- Not checking solver status and termination condition before extracting results, leading to errors on infeasible or failed solves.
- Using excessive tool calls or solving the same core problem multiple times with minor variations instead of clarifying the problem interpretation first.
- Mixing analysis code (e.g., manual enumeration) with solver code in the same execution flow, creating maintenance complexity.

# Workflow 2 (OR-Tools CP-SAT)

## Modeling stage

### Strategy Overview
Formulate the problem using the OR-Tools CP-SAT solver, which natively handles Boolean logic and linear constraints. This approach leverages the solver's efficient propagation and search algorithms for combinatorial problems.

### Step 1 - Define Model and Data Structures
- Create a `cp_model.CpModel()` object.
- Store the list of items and the directed interaction scores in a dictionary or 2D list.
- Define the cardinality parameter `K`.

### Step 2 - Define Boolean Selection Variables
- Create Boolean (0-1) selection variables `x[i]` for each item `i` using `model.NewBoolVar(f'x_{i}')`.

### Step 3 - Define Boolean Interaction Variables
- Create Boolean interaction variables `y[i, j]` for each ordered pair `(i, j)` where `i != j` using `model.NewBoolVar(f'y_{i}_{j}')`.

### Step 4 - Formulate Constraints via Linear Expressions
- Add a cardinality constraint: `sum(x[i] for all i) == K`. Use `model.Add(sum(x) == K)`.
- Add logical activation constraints using `model.Add(y[i,j] <= x[i])` and `model.Add(y[i,j] <= x[j])`.
- Add the forcing constraint using `model.Add(y[i,j] >= x[i] + x[j] - 1)`.

### Step 5 - Define Objective
- Create a linear expression for the objective: `sum(score[i,j] * y[i,j] for all i,j)`.
- Maximize this expression using `model.Maximize(objective_expr)`.

### Formulation Template
```json
{
  "sets": [
    {"name": "NODES", "description": "List of all candidate items."},
    {"name": "ORDERED_PAIRS", "description": "List of all ordered pairs (i, j) where i != j."}
  ],
  "parameters": [
    {"name": "SCORE", "index": "ORDERED_PAIRS", "description": "Directed interaction score from i to j."},
    {"name": "K", "description": "Exact number of items to select."}
  ],
  "decision_variables": [
    {"name": "x", "index": "NODES", "type": "BoolVar", "description": "1 if item i is selected."},
    {"name": "y", "index": "ORDERED_PAIRS", "type": "BoolVar", "description": "1 if directed interaction from i to j is active."}
  ],
  "objective": {
    "sense": "max",
    "expression": "LinearExpr.Sum( [SCORE[i,j] * y[i,j] for (i,j) in ORDERED_PAIRS] )"
  },
  "constraints": [
    {"name": "select_exactly_k", "expression": "LinearExpr.Sum(x) == K" },
    {"name": "y_leq_source", "expression": "y[i,j] <= x[i]", "index": "ORDERED_PAIRS"},
    {"name": "y_leq_target", "expression": "y[i,j] <= x[j]", "index": "ORDERED_PAIRS"},
    {"name": "y_geq_both_selected", "expression": "y[i,j] >= x[i] + x[j] - 1", "index": "ORDERED_PAIRS"}
  ]
}
```

### Common Pitfalls
- Misinterpreting the interaction score data structure, leading to incorrect objective coefficients. Ensure the score dictionary keys match the ordered pair variable indices.
- Overlooking the need for the forcing constraint, which is as critical in CP-SAT as in MILP for this linearization.
- Creating an unnecessarily large number of interaction variables for problems where the score matrix is very sparse; consider generating variables only for pairs with non-zero scores.

## Solving stage

### Strategy Overview
Build the CP-SAT model using the `ortools.sat.python.cp_model` API. Configure the solver with appropriate time limits and optional logging. Solve the model and implement comprehensive checks on the solver response before parsing the solution.

### Step 1 - Model and Variable Instantiation
- Instantiate `cp_model.CpModel()`.
- Create dictionaries or lists to store `x[i]` and `y[(i,j)]` Boolean variables.

### Step 2 - Constraint Addition
- Use `model.Add( sum(x.values()) == K )` for the cardinality constraint.
- Use loops over ordered pairs to add the three families of logical constraints via `model.Add()`.

### Step 3 - Objective Definition and Solving
- Build the objective as a `LinearExpr` by summing `score[i,j] * y[i,j]`.
- Call `model.Maximize(objective)`.
- Create a `cp_model.CpSolver()` instance.
- Set solver parameters like `solver.parameters.max_time_in_seconds` and `solver.parameters.num_search_workers`.
- Execute the solve with `solver.Solve(model)`.

### Step 4 - Solution Status Checking and Extraction
- Check the solver status: `cp_model.OPTIMAL`, `cp_model.FEASIBLE`, or `cp_model.INFEASIBLE`.
- For optimal or feasible status, retrieve the objective value via `solver.ObjectiveValue()`.
- Evaluate each variable using `solver.Value(var)` to determine selected items and active interactions.
- For infeasible or unknown status, return a clear status message without attempting to extract variable values.

### Code Usage
```python
from ortools.sat.python import cp_model

# 1. Instantiate Model and Data
model = cp_model.CpModel()
items = ITEM_LIST
ordered_pairs = ORDERED_PAIRS_LIST
score = SCORE_DICT
K = K_VALUE

# 2. Create Variables
x = {i: model.NewBoolVar(f'x_{i}') for i in items}
y = {(i, j): model.NewBoolVar(f'y_{i}_{j}') for (i, j) in ordered_pairs}

# 3. Add Cardinality Constraint
model.Add(sum(x[i] for i in items) == K)

# 4. Add Logical Constraints
for (i, j) in ordered_pairs:
    model.Add(y[i, j] <= x[i])
    model.Add(y[i, j] <= x[j])
    model.Add(y[i, j] >= x[i] + x[j] - 1)

# 5. Define and Set Objective
objective_expr = sum(score[i, j] * y[i, j] for (i, j) in ordered_pairs)
model.Maximize(objective_expr)

# 6. Configure and Run Solver
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 4
# Optional: Enable logging
# solver.parameters.log_search_progress = True

status = solver.Solve(model)

# 7. Process Results
if status in [cp_model.OPTIMAL, cp_model.FEASIBLE]:
    objective_value = solver.ObjectiveValue()
    selected_items = [i for i in items if solver.Value(x[i]) == 1]
    active_interactions = [(i, j) for (i, j) in ordered_pairs if solver.Value(y[i, j]) == 1]
    # ... proceed with results
else:
    # status is INFEASIBLE or UNKNOWN
    # Return structured output indicating status
```

### Common Pitfalls
- Ignoring solver error messages or status codes. Always check the status and handle `INFEASIBLE` and `UNKNOWN` cases explicitly.
- Implementing complex, solver-specific linearization when the problem size is trivial; for very small `N` and `K`, consider simple enumeration as a verification step.
- Making multiple solver calls with minor formulation changes without first resolving ambiguity in the problem's interpretation of interaction scores.
