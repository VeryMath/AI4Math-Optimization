---
name: 2D Bin Packing with Disjunctive Constraints
description: |
  Models and solves 2D rectangular packing problems with non-overlap, containment, and fixed-orientation constraints, minimizing the number of sheets used via either iterative feasibility or direct MIP optimization.

---
# Workflow 1 (Iterative Feasibility with CP-SAT)

## Modeling stage

### Strategy Overview
Use a constraint programming approach with Boolean indicator variables for pairwise non-overlap. Solve iteratively by checking feasibility for an increasing number of sheets, leveraging CP-SAT's strength in combinatorial feasibility problems.

### Step 1 - Define Placement Variables
- For each item `i`, create integer variables `x[i]` and `y[i]` representing the bottom-left corner coordinates.
- Set variable domains from 0 to the sheet dimensions (width, height) to ensure feasibility.

### Step 2 - Enforce Containment Constraints
- For each item `i` with width `w_i` and height `h_i`, add constraints: `x[i] + w_i <= sheet_width` and `y[i] + h_i <= sheet_height`.
- This ensures the entire item lies within the sheet boundaries.

### Step 3 - Model Non-Overlap with Boolean Indicators
- For each pair of items `(i, j)` with `i < j`, introduce four Boolean variables: `left`, `right`, `below`, `above`.
- Enforce that at least one Boolean is true: `left + right + below + above >= 1`.
- Use `OnlyEnforceIf` to link each Boolean to the corresponding geometric inequality:
  - `left`: `x[i] + w_i <= x[j]`
  - `right`: `x[j] + w_j <= x[i]`
  - `below`: `y[i] + h_i <= y[j]`
  - `above`: `y[j] + h_j <= y[i]`

### Step 4 - Multi-Sheet Assignment (for minimization)
- Introduce binary assignment variables `z[i][k]` indicating which sheet each item is assigned to.
- Add sheet-level containment and non-overlap constraints per sheet, using `OnlyEnforceIf(z[i][s])` to activate constraints only for the assigned sheet.
- Start with `k = ceil(total_item_area / sheet_area)` as a theoretical lower bound, then iterate over sheet count `k` until a feasible solution is found.

### Formulation Template
```json
{
  "sets": ["I: items", "K: sheets (iterative)"],
  "parameters": ["w_i: item width", "h_i: item height", "W: sheet width", "H: sheet height"],
  "decision_variables": [
    "x_i: integer, bottom-left x coordinate",
    "y_i: integer, bottom-left y coordinate",
    "b_{ij}^1, b_{ij}^2, b_{ij}^3, b_{ij}^4: binary, non-overlap indicators",
    "z_{ik}: binary, assignment of item i to sheet k"
  ],
  "objective": {
    "sense": "min",
    "expression": "minimize k (iterative feasibility check)"
  },
  "constraints": [
    "x_i + w_i <= W, y_i + h_i <= H for all i",
    "b_{ij}^1 + b_{ij}^2 + b_{ij}^3 + b_{ij}^4 >= 1 for all i<j",
    "x_i + w_i <= x_j + M*(1-b_{ij}^1) for all i<j",
    "x_j + w_j <= x_i + M*(1-b_{ij}^2) for all i<j",
    "y_i + h_i <= y_j + M*(1-b_{ij}^3) for all i<j",
    "y_j + h_j <= y_i + M*(1-b_{ij}^4) for all i<j",
    "sum_k z_{ik} = 1 for all i",
    "sheet-level containment and non-overlap per k (activated via z_{ik})"
  ]
}
```

### Common Pitfalls
- **Hardcoding sheet count**: Do not fix the number of sheets to 1 when minimization is required; use iterative feasibility checks starting from a theoretical lower bound.
- **Zero objective for minimization**: When minimizing sheets, do not set objective to 0; the iterative approach naturally finds the minimum.
- **Redundant verification**: Trust solver output; do not re-run manual verification after solver confirms feasibility.

## Solving stage

### Strategy Overview
Use OR-Tools CP-SAT solver for efficient handling of Boolean variables and `OnlyEnforceIf` constraints. Solve iteratively for increasing sheet counts, stopping at the first feasible solution.

### Step 1 - Configure Solver Parameters
- Set `max_time_in_seconds` to a reasonable limit (e.g., `[TIME_LIMIT]`, default 30 seconds) for predictable runtime.
- Set `num_search_workers = 8` for parallel search on multi-core machines.
- Set `random_seed` for reproducibility.

### Step 2 - Iterative Feasibility Loop
- Start with `k = ceil(total_item_area / sheet_area)`.
- Build the model with assignment variables for `k` sheets.
- Solve and check status: if `OPTIMAL` or `FEASIBLE`, extract results and break.
- If infeasible, increment `k` and rebuild the model.

### Step 3 - Extract Results
- After a feasible solution is found, extract placement coordinates via `solver.Value(x[i])` and `solver.Value(y[i])`.
- Print results in a structured format (e.g., JSON) for downstream consumption.

### Code Usage
```python
from ortools.sat.python import cp_model
import math

def solve_packing(widths, heights, sheet_w, sheet_h, max_sheets=10, time_limit=30):
    n = len(widths)
    total_area = sum(w * h for w, h in zip(widths, heights))
    sheet_area = sheet_w * sheet_h
    k_start = math.ceil(total_area / sheet_area)  # theoretical lower bound

    for k in range(k_start, max_sheets + 1):
        model = cp_model.CpModel()
        x = [model.NewIntVar(0, sheet_w, f"x_{i}") for i in range(n)]
        y = [model.NewIntVar(0, sheet_h, f"y_{i}") for i in range(n)]
        z = [[model.NewBoolVar(f"z_{i}_{s}") for s in range(k)] for i in range(n)]

        # Each item assigned to exactly one sheet
        for i in range(n):
            model.Add(sum(z[i][s] for s in range(k)) == 1)

        # Containment constraints (conditional on assignment)
        for i in range(n):
            for s in range(k):
                model.Add(x[i] + widths[i] <= sheet_w).OnlyEnforceIf(z[i][s])
                model.Add(y[i] + heights[i] <= sheet_h).OnlyEnforceIf(z[i][s])

        # Non-overlap constraints (conditional on shared sheet assignment)
        for s in range(k):
            for i in range(n):
                for j in range(i + 1, n):
                    left = model.NewBoolVar(f"left_{i}_{j}_s{s}")
                    right = model.NewBoolVar(f"right_{i}_{j}_s{s}")
                    below = model.NewBoolVar(f"below_{i}_{j}_s{s}")
                    above = model.NewBoolVar(f"above_{i}_{j}_s{s}")
                    model.Add(left + right + below + above >= 1)
                    model.Add(x[i] + widths[i] <= x[j]).OnlyEnforceIf([left, z[i][s], z[j][s]])
                    model.Add(x[j] + widths[j] <= x[i]).OnlyEnforceIf([right, z[i][s], z[j][s]])
                    model.Add(y[i] + heights[i] <= y[j]).OnlyEnforceIf([below, z[i][s], z[j][s]])
                    model.Add(y[j] + heights[j] <= y[i]).OnlyEnforceIf([above, z[i][s], z[j][s]])

        solver = cp_model.CpSolver()
        solver.parameters.max_time_in_seconds = time_limit
        solver.parameters.num_search_workers = 8
        solver.parameters.random_seed = 42
        status = solver.Solve(model)

        if status in (cp_model.OPTIMAL, cp_model.FEASIBLE):
            positions = []
            for i in range(n):
                for s in range(k):
                    if solver.Value(z[i][s]) == 1:
                        positions.append({
                            "x": solver.Value(x[i]),
                            "y": solver.Value(y[i]),
                            "w": widths[i],
                            "h": heights[i],
                            "sheet": s
                        })
            return {"status": "optimal", "sheets_used": k, "positions": positions}
    return {"status": "failed", "reason": "infeasible_or_exceeded_max_sheets"}
```

### Common Pitfalls
- **Excessive tool calls for validation**: Do not run separate verification scripts after solver confirms feasibility; extract results directly.
- **Ignoring solver status codes**: Always check for `OPTIMAL` or `FEASIBLE` before reading variable values; handle `INFEASIBLE` or `UNKNOWN` gracefully.

# Workflow 2 (Direct MIP with Pyomo)

## Modeling stage

### Strategy Overview
Formulate the packing problem as a Mixed-Integer Program (MIP) using Big-M linearization for disjunctive non-overlap constraints. Minimize the number of sheets directly using binary sheet-usage variables.

### Step 1 - Define Continuous Placement Variables
- For each item `i`, define continuous variables `x[i]` and `y[i]` representing the bottom-left corner coordinates.
- Use `NonNegativeReals` domain with upper bounds set to sheet dimensions.

### Step 2 - Enforce Containment Constraints
- Add explicit constraints: `x[i] + width[i] <= sheet_width` and `y[i] + height[i] <= sheet_height`.
- Do not rely solely on variable bounds; use explicit constraints for clarity and solver robustness.

### Step 3 - Model Non-Overlap with Big-M
- For each pair `(i, j)` with `i < j`, introduce four binary variables: `left[i,j]`, `right[i,j]`, `below[i,j]`, `above[i,j]`.
- Enforce at least one holds: `left + right + below + above >= 1`.
- Use a sufficiently large `M` (e.g., `sheet_width + sheet_height`) to linearize:
  - `left`: `x[i] + w_i <= x[j] + M * (1 - left[i,j])`
  - `right`: `x[j] + w_j <= x[i] + M * (1 - right[i,j])`
  - `below`: `y[i] + h_i <= y[j] + M * (1 - below[i,j])`
  - `above`: `y[j] + h_j <= y[i] + M * (1 - above[i,j])`

### Step 4 - Multi-Sheet Objective
- Introduce binary variable `u[s]` for each sheet `s` indicating if the sheet is used.
- Assign each item to exactly one sheet using binary assignment variables `z[i,s]`.
- Add sheet-specific containment and non-overlap constraints, activated via `z[i,s]`.
- Minimize `sum(u[s])` to find the minimum number of sheets.

### Formulation Template
```json
{
  "sets": ["I: items", "S: sheets (predefined max)"],
  "parameters": ["w_i: item width", "h_i: item height", "W: sheet width", "H: sheet height", "M: large constant"],
  "decision_variables": [
    "x_i: continuous, bottom-left x coordinate",
    "y_i: continuous, bottom-left y coordinate",
    "b_{ij}^1, b_{ij}^2, b_{ij}^3, b_{ij}^4: binary, non-overlap indicators",
    "z_{is}: binary, assignment of item i to sheet s",
    "u_s: binary, whether sheet s is used"
  ],
  "objective": {
    "sense": "min",
    "expression": "sum_s u_s"
  },
  "constraints": [
    "x_i + w_i <= W, y_i + h_i <= H for all i",
    "b_{ij}^1 + b_{ij}^2 + b_{ij}^3 + b_{ij}^4 >= 1 for all i<j",
    "x_i + w_i <= x_j + M*(1-b_{ij}^1) for all i<j",
    "x_j + w_j <= x_i + M*(1-b_{ij}^2) for all i<j",
    "y_i + h_i <= y_j + M*(1-b_{ij}^3) for all i<j",
    "y_j + h_j <= y_i + M*(1-b_{ij}^4) for all i<j",
    "sum_s z_{is} = 1 for all i",
    "z_{is} <= u_s for all i, s",
    "sheet-level containment and non-overlap per s (activated via z_{is})"
  ]
}
```

### Common Pitfalls
- **Using zero objective for minimization**: Always include a meaningful objective (e.g., `sum(u_s)`) when minimizing sheets; do not set objective to 0.
- **Hardcoding sheet count**: Use binary sheet-usage variables and let the solver determine the minimum; do not fix the number of sheets.
- **Insufficient Big-M value**: Ensure `M` is large enough to not cut off feasible solutions; use `sheet_width + sheet_height` as a safe default.

## Solving stage

### Strategy Overview
Use Pyomo with HiGHS solver for efficient MIP solving. Set time limits and MIP gap tolerances for predictable runtime. Handle solver status explicitly.

### Step 1 - Configure Solver
- Use `pyomo.SolverFactory("highs")` for high-performance MIP solving.
- Set `time_limit` (e.g., `[TIME_LIMIT]`, default 30 seconds) and `mip_rel_gap` (e.g., 0.01) options.

### Step 2 - Build and Solve Model
- Construct the Pyomo model with all sets, parameters, variables, constraints, and objective.
- Call `solver.solve(m, tee=False)` to suppress solver output.

### Step 3 - Parse Results
- Check `results.solver.status == SolverStatus.ok` and `termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}`.
- Extract variable values using `pyo.value()` for placement coordinates and sheet assignments.
- Print results as structured JSON with status, objective value, and positions.

### Code Usage
```python
import json
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition

def solve_packing_mip(widths, heights, sheet_w, sheet_h, max_sheets=5, time_limit=30):
    items = list(range(len(widths)))
    sheets = list(range(max_sheets))
    M = sheet_w + sheet_h

    m = pyo.ConcreteModel()
    m.I = pyo.Set(initialize=items)
    m.S = pyo.Set(initialize=sheets)
    m.pairs = pyo.Set(initialize=[(i, j) for i in items for j in items if i < j])

    m.x = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=(0, sheet_w))
    m.y = pyo.Var(m.I, domain=pyo.NonNegativeReals, bounds=(0, sheet_h))
    m.left = pyo.Var(m.pairs, domain=pyo.Binary)
    m.right = pyo.Var(m.pairs, domain=pyo.Binary)
    m.below = pyo.Var(m.pairs, domain=pyo.Binary)
    m.above = pyo.Var(m.pairs, domain=pyo.Binary)
    m.z = pyo.Var(m.I, m.S, domain=pyo.Binary)
    m.u = pyo.Var(m.S, domain=pyo.Binary)

    # Containment
    m.contain_x = pyo.Constraint(m.I, rule=lambda m, i: m.x[i] + widths[i] <= sheet_w)
    m.contain_y = pyo.Constraint(m.I, rule=lambda m, i: m.y[i] + heights[i] <= sheet_h)

    # Non-overlap
    m.non_overlap = pyo.Constraint(m.pairs, rule=lambda m, i, j: m.left[i, j] + m.right[i, j] + m.below[i, j] + m.above[i, j] >= 1)
    m.left_con = pyo.Constraint(m.pairs, rule=lambda m, i, j: m.x[i] + widths[i] <= m.x[j] + M * (1 - m.left[i, j]))
    m.right_con = pyo.Constraint(m.pairs, rule=lambda m, i, j: m.x[j] + widths[j] <= m.x[i] + M * (1 - m.right[i, j]))
    m.below_con = pyo.Constraint(m.pairs, rule=lambda m, i, j: m.y[i] + heights[i] <= m.y[j] + M * (1 - m.below[i, j]))
    m.above_con = pyo.Constraint(m.pairs, rule=lambda m, i, j: m.y[j] + heights[j] <= m.y[i] + M * (1 - m.above[i, j]))

    # Assignment and sheet usage
    m.assign = pyo.Constraint(m.I, rule=lambda m, i: sum(m.z[i, s] for s in m.S) == 1)
    m.sheet_use = pyo.Constraint(m.I, m.S, rule=lambda m, i, s: m.z[i, s] <= m.u[s])

    # Objective
    m.obj = pyo.Objective(expr=sum(m.u[s] for s in m.S), sense=pyo.minimize)

    solver = pyo.SolverFactory("highs")
    solver.options["time_limit"] = time_limit
    solver.options["mip_rel_gap"] = 0.01
    results = solver.solve(m, tee=False)

    if results.solver.status == SolverStatus.ok and results.solver.termination_condition in {TerminationCondition.optimal, TerminationCondition.feasible}:
        positions = []
        for i in items:
            for s in sheets:
                if pyo.value(m.z[i, s]) > 0.5:
                    positions.append({
                        "x": pyo.value(m.x[i]),
                        "y": pyo.value(m.y[i]),
                        "w": widths[i],
                        "h": heights[i],
                        "sheet": s
                    })
        return {"status": "optimal", "objective": pyo.value(m.obj), "positions": positions}
    else:
        return {"status": "failed", "reason": "infeasible_or_error"}
```

### Common Pitfalls
- **Trusting non-zero return codes**: Always check solver status and termination condition explicitly; do not assume success from non-zero exit codes.
- **Outputting pseudo-numeric answers on failure**: When execution fails, output a clear failure message with reason; do not fabricate numeric results.
