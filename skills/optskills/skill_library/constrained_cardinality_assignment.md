---
name: Constrained Cardinality Assignment
description: |
  Model and solve binary assignment problems with cardinality constraints, assignment limits, conditional exclusions, and linear cost minimization using MILP solvers.

---
# Workflow 1 (Pyomo with Commercial Solver)

## Modeling stage

### Strategy Overview
Formulate the problem as a Mixed-Integer Linear Program (MILP) using Pyomo's high-level modeling constructs. This approach leverages the expressive power of algebraic modeling languages to cleanly separate model logic from solver interaction, suitable for integration with commercial solvers like Gurobi or CPLEX.

### Step 1 - Define Sets and Parameters
- Define two index sets, `SET_A` and `SET_B`, representing the source and target elements for assignment.
- Define a parameter `cost[a,b]` as a dictionary or 2D array representing the cost of assigning element `a` to element `b`.
- Define a scalar parameter `K` for the exact number of total assignments required.

### Step 2 - Create Binary Decision Variables
- Create a binary variable `x[a,b]` for each pair `(a,b)` in the Cartesian product of `SET_A` and `SET_B`.
- The variable equals 1 if element `a` is assigned to element `b`, and 0 otherwise.

### Step 3 - Formulate Assignment Limit Constraints
- For each element `a` in `SET_A`, add a constraint: `sum(x[a,b] for b in SET_B) <= 1`. This ensures each source element is assigned to at most one target.
- For each element `b` in `SET_B`, add a constraint: `sum(x[a,b] for a in SET_A) <= 1`. This ensures each target element receives at most one assignment.

### Step 4 - Formulate Global Cardinality Constraint
- Add a single constraint: `sum(x[a,b] for a in SET_A for b in SET_B) == K`. This enforces the exact total number of assignments.

### Step 5 - Formulate Conditional Exclusion Constraints
- For each logical rule "if assignment (a1,b1) is selected, then assignment (a2,b2) cannot be selected", add a linear constraint: `x[a1,b1] + x[a2,b2] <= 1`.
- Compile all such pairwise incompatibilities into a list of tuples for systematic constraint generation.

### Step 6 - Define the Objective Function
- Define the objective to minimize total assignment cost: `minimize sum(cost[a,b] * x[a,b] for a in SET_A for b in SET_B)`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["cost[SET_A, SET_B]", "K"],
  "decision_variables": ["x[SET_A, SET_B] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a,b] * x[a,b] for a in SET_A for b in SET_B)"
  },
  "constraints": [
    "sum(x[a,b] for b in SET_B) <= 1, ∀ a ∈ SET_A",
    "sum(x[a,b] for a in SET_A) <= 1, ∀ b ∈ SET_B",
    "sum(x[a,b] for a in SET_A for b in SET_B) == K",
    "x[a1,b1] + x[a2,b2] <= 1, ∀ (a1,b1,a2,b2) ∈ EXCLUSION_PAIRS"
  ]
}
```

### Common Pitfalls
- Using floating-point numbers directly in the cost parameter for an integer-only solver can cause precision issues; scale and convert to integers if necessary.
- Formulating conditional exclusions as separate `if-then` logic instead of the linear inequality `x[a1,b1] + x[a2,b2] <= 1`.
- Omitting the cardinality constraint (`K`) or mis-specifying it as an inequality, which changes the problem's feasible region.
- Not explicitly defining index sets, leading to less readable and maintainable model code.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a commercial MILP solver (e.g., Gurobi) via the `SolverFactory` interface. Configure the solver for deterministic performance, enforce optimality, and implement robust solution extraction and error handling.

### Step 1 - Instantiate Solver and Set Parameters
- Create a solver object using `SolverFactory('gurobi')`.
- Set solver parameters for reproducibility and performance: `TimeLimit`, `MIPGap=0.0` (for exact optimality), `Threads`, and `Seed`.

### Step 2 - Solve and Check Status
- Execute `solver.solve(model)` and capture the results object.
- Check the high-level solver status (`results.solver.status == SolverStatus.ok`).
- Check the termination condition (`results.solver.termination_condition`). Accept `optimal` or `feasible` as successful.

### Step 3 - Extract and Validate Solution
- If successful, iterate over all `x[a,b]` variables. Collect assignments where `pyo.value(x[a,b]) > 0.5`.
- Recalculate the objective value from the extracted assignments and the `cost` parameter as a sanity check.
- Verify that the number of assignments equals `K` and that all limit and exclusion constraints are satisfied.

### Step 4 - Format and Output Results
- Output a standardized result line, e.g., `RESULT:{objective_value}`.
- Output a detailed list of assignments as tuples `(a, b, cost)`.
- For programmatic use, package results into a structured dictionary or JSON object.

### Step 5 - Handle Failures
- If the status is not `ok` or termination is `infeasible`, `unbounded`, or `invalid`, output a diagnostic payload containing the solver status and termination condition.
- Do not attempt to extract variable values from failed solves.
- Wrap solver execution in a try-except block to catch runtime errors (e.g., solver license issues, timeouts) and output a clear failure message.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

# Build model (model definition code from modeling stage)
model = pyo.ConcreteModel()
# ... populate model with sets, variables, constraints, objective

# Solve
solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = TIME_LIMIT
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = N_THREADS
solver.options['Seed'] = SEED
try:
    results = solver.solve(model)
except Exception as e:
    print(f"FAILURE: solver execution error - {e}")
    exit()

# Check status and extract results
if (results.solver.status == SolverStatus.ok and
    results.solver.termination_condition in [TerminationCondition.optimal, TerminationCondition.feasible]):
    # Extract assignments
    assignments = []
    for idx in model.x:
        if pyo.value(model.x[idx]) > 0.5:
            a, b = idx
            assignments.append((a, b, model.cost[idx]))
    obj_val = sum(c for (_, _, c) in assignments)
    print(f"RESULT:{obj_val}")
    print(f"Assignments: {assignments}")
else:
    # Handle failure
    print(f"FAILURE: status={results.solver.status}, termination={results.solver.termination_condition}")
```

### Common Pitfalls
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or incomplete solves.
- Using a loose tolerance (e.g., `> 0.1`) for extracting binary variable values; use `> 0.5` for robustness.
- Setting an excessive number of parallel threads (`Threads`) for small problems, which can degrade performance.
- Failing to provide informative output for infeasible or error cases, complicating debugging.
- Not wrapping solver execution in a try-except block, causing silent failures on runtime errors.

# Workflow 2 (Python-MIP with CBC)

## Modeling stage

### Strategy Overview
Formulate the problem directly using the Python-MIP library, which provides a lower-level, solver-oriented API for constructing MILP models. This workflow is optimized for the open-source CBC solver, offering fine-grained control and efficient model building with a concise syntax.

### Step 1 - Initialize Model and Add Variables
- Create a `mip.Model` object with `sense=MINIMIZE`.
- In a single loop over the Cartesian product of sets `SET_A` and `SET_B`, add binary variables `x[a,b]` using `model.add_var(var_type=BINARY)`. Store them in a dictionary keyed by `(a,b)`.

### Step 2 - Build Assignment Limit Constraints
- For each `a` in `SET_A`, create a constraint: `mip.xsum(x[a,b] for b in SET_B) <= 1`.
- For each `b` in `SET_B`, create a constraint: `mip.xsum(x[a,b] for a in SET_A) <= 1`.
- Add each constraint directly to the model using `model.add_constr(...)`.

### Step 3 - Build Global Cardinality Constraint
- Create a single constraint: `mip.xsum(x[a,b] for a in SET_A for b in SET_B) == K` and add it to the model.

### Step 4 - Build Conditional Exclusion Constraints
- Iterate through a pre-defined list of incompatible assignment pairs `(a1,b1,a2,b2)`.
- For each pair, add a constraint: `x[a1,b1] + x[a2,b2] <= 1`.

### Step 5 - Set the Objective Function
- Build the objective expression as `mip.xsum(cost[a,b] * x[a,b] for a in SET_A for b in SET_B)`.
- Assign this expression to `model.objective`.

### Formulation Template
```json
{
  "sets": ["SET_A", "SET_B"],
  "parameters": ["cost[SET_A, SET_B]", "K"],
  "decision_variables": ["x[SET_A, SET_B] ∈ {0,1}"],
  "objective": {
    "sense": "min",
    "expression": "sum(cost[a,b] * x[a,b] for a in SET_A for b in SET_B)"
  },
  "constraints": [
    "sum(x[a,b] for b in SET_B) <= 1, ∀ a ∈ SET_A",
    "sum(x[a,b] for a in SET_A) <= 1, ∀ b ∈ SET_B",
    "sum(x[a,b] for a in SET_A for b in SET_B) == K",
    "x[a1,b1] + x[a2,b2] <= 1, ∀ (a1,b1,a2,b2) ∈ EXCLUSION_PAIRS"
  ]
}
```

### Common Pitfalls
- Forgetting to set the model sense (`MINIMIZE`) during initialization.
- Using Python's built-in `sum()` instead of `mip.xsum()` for linear expressions, which is less efficient and can cause performance issues in Python-MIP.
- Storing variable references in a list instead of a dictionary keyed by indices, making constraint construction more error-prone.
- Adding constraints inside deeply nested loops without pre-computing index pairs, hurting model build time.

## Solving stage

### Strategy Overview
Solve the model using the integrated CBC solver via Python-MIP's `optimize()` method. Leverage Python-MIP's direct solution query methods and implement parsing logic that handles the solver's status codes directly.

### Step 1 - Configure and Run Solver
- Set solver parameters via `model.verbose`, `model.max_seconds`, `model.threads`, and `model.max_mip_gap`.
- Call `model.optimize()` to initiate the solve.

### Step 2 - Interpret Solve Status
- Check `model.status`. Accept `Status.OPTIMAL` or `Status.FEASIBLE` as successful.
- For `Status.OPTIMAL`, the best solution found is proven optimal. For `Status.FEASIBLE`, it is a valid but not necessarily optimal solution.

### Step 3 - Extract Solution
- If the status is acceptable, iterate through the dictionary of `x` variables.
- Use `var.x` to get the solution value (approximately 0.0 or 1.0). Collect assignments where `var.x > 0.5`.
- Compute the total cost from the extracted assignments and the `cost` dictionary.

### Step 4 - Output Structured Results
- Output the objective value and list of assignments in a consistent, parseable format.
- Include the solve status and gap information in the output for traceability.

### Step 5 - Manage Infeasibility and Errors
- If `model.status` is `Status.INFEASIBLE` or `Status.ERROR`, output a clear error message with the status.
- Avoid accessing `var.x` when no solution is available.
- Wrap the `model.optimize()` call in a try-except block to catch runtime errors (e.g., solver not found, memory issues) and output a clear failure message.

### Code Usage
```python
from mip import Model, MINIMIZE, BINARY, Status

# Build model
model = Model(sense=MINIMIZE)
x = {}
for a in SET_A:
    for b in SET_B:
        x[(a, b)] = model.add_var(var_type=BINARY)

# Add constraints (constraint addition code from modeling stage)
# ...
# Set objective
model.objective = mip.xsum(cost[a, b] * x[(a, b)] for a in SET_A for b in SET_B)

# Solve
model.verbose = 1  # Set to 0 to suppress solver log
model.max_seconds = TIME_LIMIT
model.threads = N_THREADS
model.max_mip_gap = 0.0
try:
    model.optimize()
except Exception as e:
    print(f"FAILURE: solver execution error - {e}")
    exit()

# Check status and extract results
if model.status in [Status.OPTIMAL, Status.FEASIBLE]:
    assignments = []
    for (a, b), var in x.items():
        if var.x > 0.5:
            assignments.append((a, b, cost[(a, b)]))
    obj_val = sum(c for (_, _, c) in assignments)
    print(f"RESULT:{obj_val}")
    print(f"Assignments: {assignments}")
    print(f"Status: {model.status}, Gap: {model.gap}")
else:
    print(f"FAILURE: status={model.status}")
```

### Common Pitfalls
- Misinterpreting `Status.FEASIBLE` as optimal; check `model.status` explicitly.
- Not setting `model.max_mip_gap = 0.0` when an exact optimal solution is required.
- Accessing `var.x` before checking `model.status`, which may raise an exception if no solution exists.
- Setting `model.verbose = 1` in production code, which can clutter logs; control verbosity based on context.
- Not wrapping solver execution in a try-except block, causing silent failures on runtime errors.

## Prerequisite Checks (Apply Before Any Workflow)

### Step 1 - Perform a Single Comprehensive Environment Check
- In one code block, verify the availability of all candidate solvers and libraries (e.g., `pyomo`, `gurobi`, `mip`, `cbc`).
- Use `import` statements within try-except blocks to detect missing packages.
- For solvers, attempt to instantiate a solver object (e.g., `SolverFactory('gurobi')`) and catch import or licensing errors.
- Based on the results, select the appropriate workflow (Pyomo with Gurobi/CPLEX, or Python-MIP with CBC) and proceed directly to model building without re-checking.

### Step 2 - Validate Input Data Before Modeling
- Ensure `SET_A` and `SET_B` are non-empty lists or sets.
- Ensure `cost` dictionary covers all pairs `(a,b)` in the Cartesian product of `SET_A` and `SET_B`.
- Ensure `K` is an integer between 0 and `min(len(SET_A), len(SET_B))`.
- If any validation fails, output a clear error message and abort.

### Step 3 - Fallback Guidance
- If no solver is available, output a clear diagnostic message listing which solvers were attempted and why they failed.
- Do not attempt to build or solve a model without a confirmed solver.

## Performance and Validation Notes
- For small to medium-sized assignment problems (e.g., up to hundreds of agents/tasks), this MILP formulation solves quickly (often in < 0.1 seconds) and guarantees the global optimum.
- After solving, always verify the extracted assignment count equals `K` and that all assignment limit and exclusion constraints are satisfied as a sanity check.
- When the number of source elements equals the number of target elements, the `<= 1` assignment limit constraints combined with the cardinality constraint `== K` naturally enforce a perfect one-to-one matching. For unbalanced problems, adjust `K` accordingly or add dummy elements with zero cost.
