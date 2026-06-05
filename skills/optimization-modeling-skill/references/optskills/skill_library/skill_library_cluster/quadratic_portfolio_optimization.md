---
name: Quadratic Portfolio Optimization
description: |
  Formulate and solve portfolio variance minimization as a quadratic program with linear constraints, handling incomplete covariance data and verifying solution feasibility.

---

# Workflow 1 (Pyomo with Commercial QP Solver)

## Modeling stage

### Strategy Overview
Formulate the portfolio allocation problem as a convex quadratic program (QP) using Pyomo's algebraic modeling. The objective is to minimize portfolio variance (a quadratic function of weights and covariance matrix) subject to linear budget, return target, and diversification constraints.

### Step 1 - Define Sets and Parameters
- Define an indexed set for assets.
- Store expected returns as a parameter indexed by the asset set.
- Store the covariance matrix as a symmetric parameter indexed by asset pairs.
- Define scalar parameters for the minimum required return and maximum allowed weight per asset.

### Step 2 - Declare Decision Variables
- Declare continuous, non-negative variables for portfolio weights.
- Enforce upper bounds per asset directly in the variable declaration (e.g., `bounds=(0, max_weight)`).

### Step 3 - Formulate Quadratic Objective
- Construct the portfolio variance objective as the double summation: `sum(weight[i] * covariance[i,j] * weight[j] for i in assets for j in assets)`.
- Set the objective sense to minimize.

### Step 4 - Implement Linear Constraints
- Add a linear equality constraint enforcing the sum of weights equals one (budget constraint).
- Add a linear inequality constraint ensuring the weighted sum of expected returns meets or exceeds the target return.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns[assets]", "covariance[assets, assets]", "min_return", "max_weight"],
  "decision_variables": ["weight[assets] (continuous, >=0, <=max_weight)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} weight[i] * covariance[i,j] * weight[j]"
  },
  "constraints": [
    "budget: sum_{i in assets} weight[i] == 1",
    "return_target: sum_{i in assets} expected_returns[i] * weight[i] >= min_return"
  ]
}
```

### Common Pitfalls
- Assuming missing covariance data is zero without verifying matrix positive definiteness.
- Using inconsistent indexing (e.g., 0-based vs 1-based) between sets and parameter dictionaries.
- Redundantly defining non-negativity via both variable domain (`NonNegativeReals`) and explicit lower bound.

## Solving stage

### Strategy Overview
Solve the QP using a commercial solver (e.g., Gurobi) via Pyomo's `SolverFactory`. Configure solver options for reproducibility and performance, then rigorously check solution status and validate constraint satisfaction.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `SolverFactory("gurobi")`.
- Set options: `TimeLimit`, `MIPGap=0.0` (for continuous QP optimality), `Threads`, and `Seed` for deterministic results.
- Solve the model with `tee=False` to suppress verbose output.

### Step 2 - Check Solver Status
- Verify `results.solver.status == SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `optimal` or `feasible`.
- If status is not acceptable, output a structured JSON error payload instead of the objective value.

### Step 3 - Extract and Validate Solution
- Extract optimal weights: `[pyo.value(model.weight[i]) for i in model.assets]`.
- Compute the achieved portfolio return from optimal weights and expected returns.
- Validate all constraints: sum of weights ≈ 1, return meets target, and weights respect bounds (within a small tolerance, e.g., 1e-6).

### Step 4 - Output Results
- Print the optimal portfolio variance with a prefix for parsing: `print(f"RESULT:{portfolio_variance:.6f}")`.
- Optionally, output weights and validation metrics for debugging.

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# ... model building steps ...

solver = pyo.SolverFactory('gurobi')
solver.options['TimeLimit'] = 30
solver.options['MIPGap'] = 0.0
solver.options['Threads'] = 4
solver.options['Seed'] = 42
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition

if status == SolverStatus.ok and term in {TerminationCondition.optimal, TerminationCondition.feasible}:
    portfolio_variance = float(pyo.value(model.obj))
    weights = [pyo.value(model.weight[i]) for i in model.assets]
    portfolio_return = sum(expected_returns[i] * weights[i] for i in model.assets)
    # Validate constraints here
    print(f"RESULT:{portfolio_variance:.6f}")
else:
    payload = {
        "status": "failed",
        "reason": "infeasible_or_error",
        "solver_status": str(status),
        "termination_condition": str(term)
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Trusting a solver's `ok` status without checking the termination condition.
- Not validating constraint satisfaction post-solution, especially for the return target.
- Using solver-specific options (like `threads`) that may conflict with the execution environment.

# Workflow 2 (Pyomo with Open-Source NLP/QP Solver)

## Modeling stage

### Strategy Overview
Formulate the same QP structure but target open-source solvers like IPOPT or HiGHS. Emphasize handling of incomplete covariance data by constructing a reasonable, positive definite matrix, and include a pre-solve feasibility check.

### Step 1 - Handle Incomplete Covariance Data
- If the covariance matrix is partially specified, construct a complete, positive definite matrix.
- Set known variance/covariance values.
- For unspecified diagonal entries (variances), use estimated values (e.g., average of known variances).
- For unspecified off-diagonal entries, assume a moderate correlation (e.g., 0.3) and compute covariance as `corr * sqrt(var_i * var_j)`.
- Ensure matrix symmetry and positive definiteness via eigenvalue adjustment if necessary.
- **Alternative construction**: If only expected returns are provided, construct a rank-1 positive semidefinite covariance matrix using the outer product of the return vector (i.e., `cov[i,j] = expected_returns[i] * expected_returns[j]`). This is a valid single-factor model approximation.

### Step 2 - Perform Feasibility Analysis
- Before building the full QP, check if the return target is achievable given the weight bounds.
- Solve a simple linear feasibility problem or compute the maximum possible return by allocating `max_weight` to the highest-return assets.

### Step 3 - Build Pyomo Model
- Similar to Workflow 1: define sets, parameters, variables with bounds, quadratic objective, and linear constraints.
- Provide sensible variable initialization (e.g., equal weights) to aid solver convergence.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["expected_returns[assets]", "covariance[assets, assets]", "min_return", "max_weight"],
  "decision_variables": ["weight[assets] (continuous, >=0, <=max_weight)"],
  "objective": {
    "sense": "min",
    "expression": "sum_{i in assets} sum_{j in assets} weight[i] * covariance[i,j] * weight[j]"
  },
  "constraints": [
    "budget: sum_{i in assets} weight[i] == 1",
    "return_target: sum_{i in assets} expected_returns[i] * weight[i] >= min_return"
  ]
}
```

### Common Pitfalls
- Creating synthetic covariance matrices without documenting assumptions or checking positive definiteness.
- Skipping the feasibility check and wasting time solving an infeasible QP.
- Using nested loops for the quadratic objective instead of Pyomo's efficient expression building.

## Solving stage

### Strategy Overview
Solve using an open-source solver (IPOPT for general NLP, HiGHS for QP). Configure tolerances for precision, implement robust status checking, and include post-solution validation and optional sensitivity analysis.

### Step 1 - Select and Configure Solver
- For general QP: `SolverFactory("ipopt")`. Set options: `tol=1e-8`, `acceptable_tol=1e-6`, `max_iter=1000`, `print_level=0`.
- For convex QP: `SolverFactory("highs")`. Set options: `time_limit=30`, `presolve="on"`.
- Avoid setting options that may cause conflicts (e.g., `threads` in HiGHS if the environment is already configured).

### Step 2 - Solve and Check Status
- Solve the model.
- Check `SolverStatus.ok` and accept termination conditions `optimal`, `locallyOptimal`, or `feasible`.

### Step 3 - Validate and Analyze Solution
- Extract weights and compute portfolio return and variance.
- Verify all constraints are satisfied within tolerance.
- Optionally, perform a local perturbation test to confirm optimality.

### Step 4 - Output Structured Results
- Output a JSON payload containing status, objective value, weights, portfolio return, and constraint satisfaction flags.
- Ensure all values are JSON-serializable (convert numpy types to Python floats/ints).

### Code Usage
```python
import pyomo.environ as pyo
from pyomo.opt import SolverStatus, TerminationCondition
import json

# ... model building steps, including covariance matrix construction ...

solver = pyo.SolverFactory('ipopt')  # or 'highs'
solver.options['tol'] = 1e-8
solver.options['max_iter'] = 1000
solver.options['print_level'] = 0
results = solver.solve(model, tee=False)

status = results.solver.status
term = results.solver.termination_condition
ok_terms = {TerminationCondition.optimal, TerminationCondition.locallyOptimal, TerminationCondition.feasible}

if status == SolverStatus.ok and term in ok_terms:
    weights = [float(pyo.value(model.weight[i])) for i in model.assets]
    portfolio_variance = float(pyo.value(model.obj))
    portfolio_return = sum(expected_returns[i] * weights[i] for i in model.assets)

    # Constraint validation
    budget_sat = abs(sum(weights) - 1.0) < 1e-6
    return_sat = portfolio_return >= min_return - 1e-6
    bounds_sat = all(0.0 <= w <= max_weight + 1e-6 for w in weights)

    payload = {
        "status": "success",
        "portfolio_variance": portfolio_variance,
        "portfolio_return": portfolio_return,
        "weights": weights,
        "constraints_satisfied": {
            "budget": bool(budget_sat),
            "return_target": bool(return_sat),
            "weight_bounds": bool(bounds_sat)
        }
    }
    print(f"RESULT_JSON:{json.dumps(payload)}")
    print(f"RESULT:{portfolio_variance:.6f}")
else:
    payload = {"status": "failed", "solver_status": str(status), "termination_condition": str(term)}
    print(f"RESULT_JSON:{json.dumps(payload)}")
```

### Common Pitfalls
- Not converting numpy types to Python types before JSON serialization.
- Setting overly restrictive solver options that cause convergence failures.
- Accepting solutions without verifying the return target constraint is actually met.
