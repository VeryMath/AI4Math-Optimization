---
name: MultiCommodityNetworkFlow
description: |
  Model and solve multi-commodity flow problems with shared arc capacities and commodity-specific limits, minimizing linear transportation cost.
---

# Workflow 1 (Pyomo with Commercial/Open-Source MILP Solver)

## Modeling stage

### Strategy Overview
This workflow uses Pyomo's abstract modeling syntax to define a multi-commodity flow problem with three-index variables, separating model logic from data. It is designed for solvers like Gurobi, CPLEX, or HiGHS that accept Pyomo models.

### Step 1 - Define Sets and Parameters
- Define sets for nodes, commodities, and directed arcs (e.g., as tuples `(i, j)` where `i != j`).
- Define parameters for unit cost, total arc capacity, commodity-specific capacity per arc, and net demand per node-commodity pair (negative for supply, positive for demand).

### Step 2 - Create Decision Variables
- Create a non-negative continuous variable `flow[i, j, p]` for the flow of each commodity `p` on each directed arc `(i, j)`.

### Step 3 - Formulate Constraints
- **Flow Conservation**: For each node and commodity, enforce `sum(inflow) - sum(outflow) = net_demand`.
- **Total Arc Capacity**: For each arc, enforce the sum of all commodity flows does not exceed the arc's total capacity.
- **Commodity Capacity**: For each arc and commodity, enforce the flow does not exceed the commodity-specific capacity for that arc.

### Step 4 - Define Objective
- Define a linear objective to minimize total cost: `unit_cost * sum(flow[i, j, p] for all arcs and commodities)`.

### Formulation Template
```json
{
  "sets": [
    "nodes",
    "commodities",
    "arcs (dimen=2)"
  ],
  "parameters": [
    "unit_cost",
    "arc_capacity[arcs]",
    "commodity_capacity[arcs, commodities]",
    "net_demand[nodes, commodities]"
  ],
  "decision_variables": [
    "flow[arcs, commodities] >= 0"
  ],
  "objective": {
    "sense": "min",
    "expression": "unit_cost * sum(flow[i,j,p] for (i,j) in arcs for p in commodities)"
  },
  "constraints": [
    "flow_conservation[n, p]: sum(flow[i,n,p] for (i,n) in arcs) - sum(flow[n,j,p] for (n,j) in arcs) = net_demand[n, p]",
    "total_capacity[i, j]: sum(flow[i,j,p] for p in commodities) <= arc_capacity[i, j]",
    "commodity_capacity[i, j, p]: flow[i,j,p] <= commodity_capacity[i, j, p]"
  ]
}
```

### Common Pitfalls
- Forgetting to exclude self-loops when generating the `arcs` set, which can lead to nonsensical flows.
- Mismatching the sign convention for `net_demand` in the flow conservation rule, causing infeasibility.
- Defining `commodity_capacity` as a scalar instead of a parameter indexed by arc and commodity, which incorrectly applies the same limit everywhere.

## Solving stage

### Strategy Overview
Solve the Pyomo model using a configured solver instance, carefully check the solution status, and load results. Includes validation of the solution against problem constraints.

### Step 1 - Configure and Execute Solver
- Instantiate the solver factory (e.g., `SolverFactory("gurobi")`).
- Set solver options for deterministic performance: `TimeLimit`, `MIPGap` (or `mip_rel_gap`) to 0.0 for LP, `Threads`, and `Seed`.
- Call `solve(model, ...)` with `tee=False` for quiet operation or `tee=True` for logs.

### Step 2 - Check Status and Load Solution
- Check the solver status (`SolverStatus.ok`) and termination condition (`TerminationCondition.optimal` or `.feasible`).
- If using a solver like HiGHS, use `load_solutions=False` and then `model.solutions.load_from(results)` to avoid loading errors.
- If the solve failed, output a structured JSON error message.

### Step 3 - Validate and Report Solution
- Compute the objective value from the model variable to verify against the solver's reported value.
- Programmatically check flow conservation and capacity constraints with a small tolerance (e.g., 1e-6).
- Print only non-zero flows for clarity and output the final result in a parseable format (e.g., `RESULT:{objective_value}`).

### Code Usage
```python
import pyomo.environ as pyo
import json

def solve_multi_commodity_flow(model):
    # Configure solver
    solver = pyo.SolverFactory("gurobi")  # or "highs", "cplex"
    solver.options["TimeLimit"] = 30
    solver.options["MIPGap"] = 0.0
    solver.options["Threads"] = 4
    solver.options["Seed"] = 42

    # Solve with controlled solution loading
    results = solver.solve(model, tee=False, load_solutions=False)

    # Check status and load
    if (results.solver.status == pyo.SolverStatus.ok and
        results.solver.termination_condition in {pyo.TerminationCondition.optimal,
                                                 pyo.TerminationCondition.feasible}):
        model.solutions.load_from(results)
        # Validate key constraints
        tolerance = 1e-6
        # ... (add validation checks here)
        # Output result
        print(f"RESULT:{pyo.value(model.obj)}")
        # Optional: print non-zero flows
        for idx in model.flow:
            if pyo.value(model.flow[idx]) > tolerance:
                print(f"  flow{idx} = {pyo.value(model.flow[idx])}")
    else:
        error_info = {
            "status": "failed",
            "reason": "infeasible_or_error",
            "solver_status": str(results.solver.status),
            "termination_condition": str(results.solver.termination_condition)
        }
        print(f"RESULT_JSON:{json.dumps(error_info)}")
```

### Common Pitfalls
- Assuming the solution is loaded automatically; some solvers require explicit `load_solutions=False` and manual loading.
- Not checking both `solver.status` and `termination_condition`, leading to misinterpretation of suboptimal or feasible solutions.
- Forgetting to set `MIPGap=0.0` for linear problems, causing unnecessary early stopping.

# Workflow 2 (Google OR-Tools Linear Solver)

## Modeling stage

### Strategy Overview
This workflow uses Google OR-Tools' linear solver API (`pywraplp`) to construct the model imperatively. It is suitable for direct integration and offers fine-grained control over variable and constraint creation.

### Step 1 - Initialize Solver and Create Variables
- Create a solver instance (e.g., `GLOP` for LP, `CBC` for MIP).
- For each arc `(i, j)` and commodity `p`, create a continuous variable with lower bound 0 and upper bound set to the commodity-specific capacity.

### Step 2 - Add Flow Conservation Constraints
- For each node `n` and commodity `p`, create a constraint: `sum(outgoing_flow) - sum(incoming_flow) = net_demand[n, p]`.
- Set coefficients carefully: `+1` for outgoing flows, `-1` for incoming flows.

### Step 3 - Add Total Arc Capacity Constraints
- For each arc `(i, j)`, create a constraint: `sum(flow[i, j, p] for all p) <= total_arc_capacity[i, j]`.

### Step 4 - Define Objective
- Set the objective to minimize `unit_cost * sum(all_flow_variables)`.

### Formulation Template
```json
{
  "sets": [
    "nodes",
    "commodities",
    "arcs (dimen=2)"
  ],
  "parameters": [
    "unit_cost",
    "arc_capacity[arcs]",
    "commodity_capacity[arcs, commodities]",
    "net_demand[nodes, commodities]"
  ],
  "decision_variables": [
    "flow[arcs, commodities] with bounds [0, commodity_capacity]"
  ],
  "objective": {
    "sense": "min",
    "expression": "unit_cost * sum(flow[i,j,p] for (i,j) in arcs for p in commodities)"
  },
  "constraints": [
    "flow_conservation[n, p]: sum(flow[n,j,p] for j) - sum(flow[i,n,p] for i) = net_demand[n, p]",
    "total_capacity[i, j]: sum(flow[i,j,p] for p in commodities) <= arc_capacity[i, j]"
  ]
}
```

### Common Pitfalls
- Incorrectly mapping data structures (e.g., capacities stored per neighbor list) to the `(i, j, p)` indexing, requiring explicit lookup logic.
- Setting variable upper bounds to `infinity` instead of the commodity capacity, missing an entire layer of constraints.
- Adding the commodity capacity as a separate constraint instead of a variable bound, which is less efficient.

## Solving stage

### Strategy Overview
Solve using OR-Tools' native `Solve()` method, check the result status, extract the solution values, and perform post-solution validation.

### Step 1 - Solve and Check Status
- Call `solver.Solve()`.
- Check the result status: `pywraplp.Solver.OPTIMAL` or `FEASIBLE` indicates a successful solve.

### Step 2 - Extract Solution
- If optimal or feasible, retrieve the objective value via `solver.Objective().Value()`.
- Iterate through all flow variables, extracting their solution values with `var.solution_value()`.

### Step 3 - Validate and Report
- Programmatically verify flow conservation and total capacity constraints using the extracted solution values.
- Filter and print only non-zero flows (above a small tolerance) for interpretability.
- Output the total cost in a consistent format.

### Code Usage
```python
from ortools.linear_solver import pywraplp
import json

def solve_with_ortools(node_data, commodity_data, arc_data):
    # Initialize solver
    solver = pywraplp.Solver.CreateSolver('GLOP')  # Use 'CBC' for MIP
    if not solver:
        raise RuntimeError("Solver not available.")

    # Create variables and store in a dictionary
    flow_vars = {}
    for (i, j) in arc_data['arcs']:
        for p in commodity_data['commodities']:
            ub = commodity_data['capacity'][(i, j, p)]
            flow_vars[(i, j, p)] = solver.NumVar(0.0, ub, f'flow_{i}_{j}_{p}')

    # Add flow conservation constraints
    for n in node_data['nodes']:
        for p in commodity_data['commodities']:
            constraint = solver.Constraint(
                node_data['net_demand'][(n, p)],
                node_data['net_demand'][(n, p)]
            )
            # Outgoing flows: coefficient +1
            for (i, j) in arc_data['arcs']:
                if i == n:
                    constraint.SetCoefficient(flow_vars[(i, j, p)], 1.0)
                if j == n:
                    constraint.SetCoefficient(flow_vars[(i, j, p)], -1.0)

    # Add total arc capacity constraints
    for (i, j) in arc_data['arcs']:
        cap_constraint = solver.Constraint(-solver.infinity(), arc_data['total_capacity'][(i, j)])
        for p in commodity_data['commodities']:
            cap_constraint.SetCoefficient(flow_vars[(i, j, p)], 1.0)

    # Set objective
    objective = solver.Objective()
    for (i, j, p), var in flow_vars.items():
        objective.SetCoefficient(var, arc_data['unit_cost'])
    objective.SetMinimization()

    # Solve
    status = solver.Solve()

    # Process result
    if status in [pywraplp.Solver.OPTIMAL, pywraplp.Solver.FEASIBLE]:
        total_cost = solver.Objective().Value()
        # Validation checks can be added here
        print(f"RESULT:{total_cost}")
        tolerance = 1e-6
        for idx, var in flow_vars.items():
            val = var.solution_value()
            if val > tolerance:
                print(f"  flow{idx} = {val}")
    else:
        error_info = {
            "status": "failed",
            "reason": "infeasible_or_error",
            "solver_status": status
        }
        print(f"RESULT_JSON:{json.dumps(error_info)}")
```

### Common Pitfalls
- Confusing `OPTIMAL` and `FEASIBLE` statuses; both may be acceptable depending on the stopping criteria.
- Not using variable bounds for commodity capacities, which reduces solver performance.
- Failing to set the coefficient sign correctly in flow conservation constraints, leading to incorrect material balance.
