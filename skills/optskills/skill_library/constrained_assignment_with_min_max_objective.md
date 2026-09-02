---
name: Constrained Assignment with Min-Max Objective
description: |
  Model and solve discrete assignment problems with domain restrictions, pairwise incompatibilities, and a min-max objective using either CP-SAT or MIP solvers.

---

# Workflow 1 (CP-SAT with Integer Assignment Variables)

## Modeling stage

### Strategy Overview
This workflow models the problem using integer decision variables for each entity, directly representing the assigned discrete value. Domain restrictions are enforced via allowed value lists, and incompatibilities are modeled as simple inequalities. The CP-SAT solver is ideal for this discrete, combinatorial formulation.

### Step 1 - Define Core Sets and Parameters
- Define a set of entities (e.g., `items`) to be assigned.
- Define a set of possible discrete values (e.g., `types`).
- For each entity, define a parameter `allowed_types[i]` listing its permitted values.
- Define a list of incompatible entity pairs `incompatible_pairs`.

### Step 2 - Create Integer Decision Variables
- Create an integer variable `x[i]` for each entity `i`, representing its assigned type.
- Set the variable's domain to the overall range of possible types (e.g., `[min_type, max_type]`).

### Step 3 - Enforce Domain Restrictions
- For each entity `i`, add a constraint `AddAllowedAssignments([x[i]], [allowed_types[i]])`. This efficiently restricts the variable's value to its specific allowed list.

### Step 4 - Enforce Pairwise Incompatibilities
- For each incompatible pair `(i, j)`, add a constraint `x[i] != x[j]` to prevent them from receiving the same assignment.

### Step 5 - Model the Min-Max Objective
- Create an auxiliary integer variable `max_assigned` to represent the maximum value assigned to any entity.
- For each entity `i`, add a constraint `max_assigned >= x[i]`.
- Set the objective to `Minimize(max_assigned)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of entities",
    "T: set of all possible discrete values",
    "P: set of incompatible pairs (i,j) where i,j in I"
  ],
  "parameters": [
    "allowed[i]: list of values in T permitted for entity i"
  ],
  "decision_variables": [
    "x[i] in T: assigned value for entity i",
    "y: auxiliary variable for maximum assigned value"
  ],
  "objective": {
    "sense": "min",
    "expression": "y"
  },
  "constraints": [
    "domain[i]: x[i] in allowed[i] for all i in I",
    "incompatibility[(i,j)]: x[i] != x[j] for all (i,j) in P",
    "max_def[i]: y >= x[i] for all i in I"
  ]
}
```

### Common Pitfalls
- Creating inequality constraints for domain restrictions instead of using `AddAllowedAssignments`, which is less efficient.
- Forgetting to bound the auxiliary `max_assigned` variable, which can slow down the solver.
- Generating incompatibility constraints for all entity pairs instead of only the specified incompatible pairs.

## Solving stage

### Strategy Overview
Use the OR-Tools CP-SAT solver. Configure it for a balance of speed and proof of optimality. After solving, rigorously verify the solution against all constraints and, if needed, prove optimality via a feasibility check.

### Step 1 - Configure and Run the Solver
- Instantiate a `CpSolver()` object.
- Set a time limit (`solver.parameters.max_time_in_seconds`).
- Enable parallel search (`solver.parameters.num_search_workers`).
- Set a random seed for reproducibility (`solver.parameters.random_seed`).
- Call `solver.Solve(model)` to obtain the status.

### Step 2 - Check Solver Status and Extract Solution
- Check if `status` is `OPTIMAL` or `FEASIBLE`.
- If successful, retrieve the value of each `x[i]` and the objective `y` using `solver.Value(variable)`.
- If `status` is `INFEASIBLE`, handle the error appropriately without trying to load variable values.

### Step 3 - Verify Solution Feasibility
- Programmatically verify that each entity's assigned value is in its `allowed[i]` list.
- Verify that for every incompatible pair, the assigned values are different.
- Verify that the reported objective `y` equals the maximum of all assigned `x[i]` values.

### Step 4 - Prove Optimality (Optional)
- If the status is `OPTIMAL`, optimality is proven by the solver.
- To manually verify, create a feasibility model: add all constraints plus `y <= k-1`, where `k` is the found objective value. Solve; infeasibility confirms `k` is optimal.

### Code Usage
```python
from ortools.sat.python import cp_model

# Build model from formulation
model = cp_model.CpModel()
# ... create variables and constraints as per modeling steps ...

# Solve with status / termination checks
solver = cp_model.CpSolver()
solver.parameters.max_time_in_seconds = 30.0
solver.parameters.num_search_workers = 8
solver.parameters.random_seed = 42

status = solver.Solve(model)

if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
    assignments = {i: solver.Value(x[i]) for i in items}
    obj_value = solver.Value(max_assigned)
    # ... verification and output ...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Assuming `FEASIBLE` status guarantees optimality; it does not.
- Trying to access `solver.Value(variable)` when the status is not `OPTIMAL` or `FEASIBLE`, causing an error.
- Not verifying the solution, which can catch modeling errors even if the solver returns a status.

# Workflow 2 (MIP with Binary Assignment Variables)

## Modeling stage

### Strategy Overview
This workflow uses a binary variable formulation, common in Mixed-Integer Programming. A binary variable `x[i,t]` indicates if entity `i` is assigned type `t`. This formulation naturally handles domain restrictions and incompatibilities via linear constraints and is suitable for MIP solvers.

### Step 1 - Define Core Sets and Parameters
- Define a set of entities `I` and a set of types `T`.
- Define a parameter `allowed[i]` as a subset of `T` for each entity.
- Define a set of incompatible pairs `P`.

### Step 2 - Create Binary Decision Variables
- Create a binary variable `x[i,t]` for each entity `i` and type `t`.

### Step 3 - Enforce Single Assignment per Entity
- For each entity `i`, add a constraint `sum_{t in T} x[i,t] == 1`.

### Step 4 - Enforce Domain Restrictions
- For each entity `i` and type `t` **not** in `allowed[i]`, fix the variable: `x[i,t] == 0`. This efficiently reduces the problem size.

### Step 5 - Enforce Pairwise Incompatibilities
- For each incompatible pair `(i,j)` and for each type `t`, add a constraint `x[i,t] + x[j,t] <= 1`. This prevents both entities from being assigned the same type.

### Step 6 - Model the Min-Max Objective
- Create a continuous variable `y` to represent the maximum type used.
- For each entity `i`, add a constraint `y >= sum_{t in T} (t * x[i,t])`. This linear expression captures the assigned type for entity `i`.
- Set the objective to `Minimize(y)`.

### Formulation Template
```json
{
  "sets": [
    "I: set of entities",
    "T: set of all possible discrete values",
    "P: set of incompatible pairs (i,j) where i,j in I"
  ],
  "parameters": [
    "allowed[i]: subset of T permitted for entity i"
  ],
  "decision_variables": [
    "x[i,t] binary: 1 if entity i is assigned type t",
    "y continuous: auxiliary variable for maximum assigned value"
  ],
  "objective": {
    "sense": "min",
    "expression": "y"
  },
  "constraints": [
    "assignment[i]: sum_{t in T} x[i,t] == 1 for all i in I",
    "domain[i,t]: x[i,t] == 0 for all i in I, t not in allowed[i]",
    "incompatibility[(i,j),t]: x[i,t] + x[j,t] <= 1 for all (i,j) in P, t in T",
    "max_def[i]: y >= sum_{t in T} (t * x[i,t]) for all i in I"
  ]
}
```

### Common Pitfalls
- Creating the incompatibility constraint for all `t in T` without first fixing `x[i,t]` to zero for disallowed types, which creates unnecessary constraints.
- Using an integer variable for `y` when a continuous variable is sufficient and often performs better.
- Forgetting to add the linear expression `sum_{t in T} (t * x[i,t])` to link the binary variables to the value of the assigned type.

## Solving stage

### Strategy Overview
Use a MIP solver (e.g., CBC, Gurobi, SCIP). Configure it for exact solution finding. After solving, check both the high-level solver status and the detailed termination condition. Extract and verify the assignment from the binary variables.

### Step 1 - Configure and Run the Solver
- Instantiate the appropriate solver (e.g., `pyo.SolverFactory('cbc')`).
- Set a time limit (`options={'seconds': TIMEOUT}`).
- Set `MIPGap=0.0` to search for an optimal solution.
- Configure threads for parallelism if supported.
- Set a random seed for reproducibility if supported.
- Call `solver.solve(model, options=...)`.

### Step 2 - Check Solver Status and Termination
- Check the solver's high-level status (e.g., `pyo.check_optimal_termination(results)`).
- Also check the solver's termination condition from the results object to distinguish between optimal and feasible solutions.
- Do not attempt to load variable values if the termination condition indicates infeasibility.

### Step 3 - Extract and Interpret the Solution
- If the termination is acceptable, retrieve variable values.
- For each entity `i`, find the type `t` where `x[i,t].value > 0.5`. This is the assigned type.
- Retrieve the objective value `y.value`.

### Step 4 - Verify Solution and Prove Optimality
- Verify each assignment is within the entity's `allowed[i]` set.
- Verify no incompatible pair shares the same type.
- To prove optimality, solve a feasibility model with an added constraint `y <= k-1` (where `k` is the found objective). Infeasibility confirms optimality.

### Code Usage
```python
import pyomo.environ as pyo

# build model from formulation
model = pyo.ConcreteModel()
# ... create sets, variables, and constraints as per modeling steps ...

# solve with status / termination checks
solver = pyo.SolverFactory('cbc')
options = {'seconds': 30, 'threads': 8, 'randomSeed': 42}
results = solver.solve(model, options=options)

# Check termination condition
if results.solver.termination_condition == pyo.TerminationCondition.optimal:
    status = "Optimal"
elif results.solver.termination_condition == pyo.TerminationCondition.feasible:
    status = "Feasible"
else:
    status = "Failed"

if status in ("Optimal", "Feasible"):
    # Load solution and process
    # ... extract assignments from x[i,t].value ...
    obj_value = pyo.value(model.y)
    # ... verification and output ...
else:
    print("No feasible solution found.")
```

### Common Pitfalls
- Relying only on `solver.status` being `ok` without checking `termination_condition`, which may mask suboptimal or infeasible results.
- Attempting to access `.value` on variables before ensuring a solution was found and loaded.
- Manually implementing a binary search for the optimal min-max value instead of letting the solver minimize `y` directly.
