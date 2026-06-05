---
name: Quadratic Portfolio Optimization
description: |
  Formulate and solve portfolio variance minimization as a quadratic program with linear constraints, handling incomplete covariance data and verifying solution feasibility.

---

# Workflow 1 (Pyomo with Commercial QP Solver)

## Modeling stage

### Strategy Overview
Formulate the portfolio allocation problem as a convex quadratic program (QP) using Pyomo's algebraic modeling. The objective is to minimize portfolio variance (a quadratic function of weights and covariance matrix) subject to linear budget, return target, and diversification constraints.

### Step 1 - Validate Input Data Completeness
- Before any modeling, confirm the problem statement explicitly defines: the number of assets `n`, the covariance matrix `Σ` (or sufficient data to construct one), expected returns vector `r`, budget constraint, per-asset upper bound `w_max`, and minimum return target `R_min`.
- If any of these are missing, request clarification once. If no clarification is provided, use a single documented fallback assumption (see Workflow 2 Step 1). If no fallback is justified, report the deficiency and stop. Do not proceed with fabricated data.

### Step 2 - Define Sets and Parameters
- Define an indexed set for assets: `model.assets = pyo.Set(initialize=range(n))`.
- Store expected returns as a parameter indexed by the asset set.
- Store the covariance matrix as a symmetric parameter indexed by asset pairs.
- Define scalar parameters for the minimum required return `R_min` and maximum allowed weight per asset `w_max`.

### Step 3 - Declare Decision Variables
- Declare continuous, non-negative variables for portfolio weights: `model.w = pyo.Var(model.assets, bounds=(0, w_max))`.

### Step 4 - Formulate Quadratic Objective
- Construct the portfolio variance objective: `model.obj = pyo.Objective(expr=sum(model.w[i] * Σ[i,j] * model.w[j] for i in model.assets for j in model.assets), sense=pyo.minimize)`.

### Step 5 - Implement Linear Constraints
- Add budget constraint: `model.budget = pyo.Constraint(expr=sum(model.w[i] for i in model.assets) == 1)`.
- Add return target constraint: `model.return_target = pyo.Constraint(expr=sum(r[i] * model.w[i] for i in model.assets) >= R_min)`.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["r[assets]", "Σ[assets, assets]", "R_min", "w_max"],
  "decision_variables": ["w[assets] (continuous, >=0, <=w_max)"],
  "objective": {
    "sense": "minimize",
    "expression": "sum_{i in assets} sum_{j in assets} w[i] * Σ[i,j] * w[j]"
  },
  "constraints": [
    "budget: sum_{i in assets} w[i] == 1",
    "return_target: sum_{i in assets} r[i] * w[i] >= R_min"
  ]
}
```

### Common Pitfalls
- Assuming missing covariance data is zero without verifying matrix positive definiteness.
- Using inconsistent indexing (e.g., 0-based vs 1-based) between sets and parameter dictionaries.
- Redundantly defining non-negativity via both variable domain (`NonNegativeReals`) and explicit lower bound.
- Proceeding with modeling when required input data is missing; always validate completeness first.

## Solving stage

### Strategy Overview
Solve the QP using a commercial solver (e.g., Gurobi) via Pyomo's `SolverFactory`. Configure solver options for reproducibility and performance, then rigorously check solution status and validate constraint satisfaction.

### Step 1 - Configure and Execute Solver
- Instantiate the solver: `solver = pyo.SolverFactory("gurobi")`.
- Set options: `solver.options['TimeLimit'] = [TIME_LIMIT]`, `solver.options['MIPGap'] = 0.0`, `solver.options['Threads'] = [N_THREADS]`, `solver.options['Seed'] = [SEED]`.
- Solve the model with `tee=False` to suppress verbose output.

### Step 2 - Check Solver Status
- Verify `results.solver.status == pyo.SolverStatus.ok`.
- Verify `results.solver.termination_condition` is `pyo.TerminationCondition.optimal` or `pyo.TerminationCondition.feasible`.
- If status is not acceptable, output a structured JSON error payload. Do not output any numeric result.

### Step 3 - Extract and Validate Solution
- Extract optimal weights: `weights = [pyo.value(model.w[i]) for i in model.assets]`.
- Compute the achieved portfolio return: `portfolio_return = sum(r[i] * weights[i] for i in model.assets)`.
- Validate all constraints: `abs(sum(weights) - 1) < 1e-6`, `portfolio_return >= R_min - 1e-6`, and `all(0 <= w <= w_max + 1e-6 for w in weights)`.
- **Check constraint binding status**: If dual values are available, verify whether the return target constraint is binding (dual > 0) or non-binding (dual ≈ 0). If duals are not available, compute the difference between achieved return and target to confirm binding status and report it. Accept a non-binding constraint as a valid solution; do not adjust parameters to force it to become binding.

### Step 4 - Output Results
- Compute portfolio variance: `portfolio_variance = pyo.value(model.obj)`.
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
    weights = [pyo.value(model.w[i]) for i in model.assets]
    portfolio_return = sum(r[i] * weights[i] for i in model.assets)
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
- Outputting a numeric result when solver status is not acceptable.

# Workflow 2 (Pyomo with Open-Source NLP/QP Solver)

## Modeling stage

### Strategy Overview
Formulate the same QP structure but target open-source solvers like IPOPT or HiGHS. Emphasize handling of incomplete covariance data by constructing a reasonable, positive definite matrix, and include a pre-solve feasibility check.

### Step 1 - Validate and Source Input Data
- Before any modeling, verify that all required input data (`n`, `Σ`, `r`, `R_min`, `w_max`) are explicitly provided or can be derived from a known, documented source.
- **If the covariance matrix is missing or incomplete**: After one clear request for the missing data, use a single, documented fallback assumption (e.g., identity matrix scaled by a base volatility squared, or equal pairwise correlation of 0.3). State the assumption explicitly. Do not make multiple different assumptions or run multiple trials with different fabricated matrices.
- **If data is fabricated or assumed**: Never output a numeric result as a definitive answer. Instead, qualify the output with a clear statement that the result is illustrative or based on assumed data. Include a `data_quality` field in the output payload.
- **Do not skip the formal clarification request step.** Explicitly request missing data before using any fallback.

### Step 2 - Handle Incomplete Covariance Data (When Justified)
- If the covariance matrix is partially specified and you have a documented basis for filling missing entries, construct a complete, positive definite matrix.
- Set known variance/covariance values.
- For unspecified diagonal entries (variances), use estimated values (e.g., average of known variances, or a typical asset volatility `σ_base` in the range 0.12–0.22).
- For unspecified off-diagonal entries, assume a moderate correlation `ρ` (e.g., 0.3) and compute covariance as `ρ * sqrt(var_i * var_j)`.
- **Ensure matrix symmetry and positive definiteness**: Check eigenvalues. If any are non-positive, add a small regularization term (e.g., `ε * I` with `ε = 1e-6`) to ensure strict positive definiteness. Do not use a rank-deficient covariance matrix (e.g., rank-1 from a single-factor model) without regularization.

### Step 3 - Perform Feasibility Analysis
- Before building the full QP, check if the return target `R_min` is achievable given the weight bounds.
- Compute the maximum possible return: `max_possible_return = sum(sorted(r, reverse=True)[:k] * w_max)`, where `k = ceil(1 / w_max)`. If `R_min > max_possible_return`, the problem is infeasible.
- **If the return target is trivially satisfied (e.g., the global minimum-variance portfolio already exceeds it), the return constraint will be non-binding. Recognize this early to avoid redundant solves.**

### Step 4 - Build Pyomo Model
- Similar to Workflow 1: define sets, parameters, variables with bounds, quadratic objective, and linear constraints.
- **Initialize variables for better convergence**: Provide sensible variable initialization (e.g., equal weights) to aid solver convergence.
- **If data is incomplete**: Still define the decision variables, constraints, and objective structure. Output a partial formulation with placeholders for the missing data, noting what is required to complete the objective.

### Formulation Template
```json
{
  "sets": ["assets"],
  "parameters": ["r[assets]", "Σ[assets, assets]", "R_min", "w_max"],
  "decision_variables": ["w[assets] (continuous, >=0, <=w_max)"],
  "objective": {
    "sense": "minimize",
    "expression": "sum_{i in assets} sum_{j in assets} w[i] * Σ[i,j] * w[j]"
  },
  "constraints": [
    "budget: sum_{i in assets} w[i] == 1",
    "return_target: sum_{i in assets} r[i] * w[i] >= R_min"
  ]
}
```

### Common Pitfalls
- Fabricating missing data (e.g., random covariance matrix) without justification, leading to meaningless results.
- Creating synthetic covariance matrices without documenting assumptions or checking positive definiteness.
- Skipping the feasibility check and wasting time solving an infeasible QP.
- Using nested loops for the quadratic objective instead of Pyomo's efficient expression building.
- Running multiple solver calls with different fabricated data to "verify" the data; the solver only confirms feasibility under the assumed data, not the correctness of the data itself.
- **Ignoring constraint binding status**: When the return constraint is not binding (i.e., the optimal portfolio naturally exceeds the minimum return), do not treat the solution as final without verifying that the constraint is indeed non-binding. Always check dual values or shadow prices to confirm. If duals are not available from the solver, compute the difference between achieved return and target as an alternative check. Accept a non-binding constraint as a valid solution; do not adjust parameters to force it to become binding.
- **Proceeding without all required problem elements**: Do not start modeling or solving if the problem statement specifies constraints but the input data is missing. First locate the correct data or request it once, then use a documented fallback.
- **Leaving the formulation empty when data is incomplete**: Even if the covariance matrix is missing, define the decision variables, constraints, and objective structure. Output a partial formulation with placeholders for the missing data, noting what is required to complete the objective.
- **Using a rank-deficient covariance matrix without regularization**: A rank-1 or otherwise singular covariance matrix can cause solver failures. Always add a small regularization term (e.g., `1e-6 * I`) to ensure strict positive definiteness.
- **Outputting multiple inconsistent `RESULT:` lines**: Execute a single clean solve after data completeness is verified. Do not print multiple variance values from different assumptions; the final output must be unambiguous.

## Solving stage

### Strategy Overview
Solve using an open-source solver (IPOPT for general NLP, HiGHS for QP). Configure tolerances for precision, implement robust status checking, and include post-solution validation and optional sensitivity analysis.

### Step 1 - Select and Configure Solver
- For general QP: `solver = pyo.SolverFactory("ipopt")`. Set options: `solver.options['tol'] = 1e-8`, `solver.options['acceptable_tol'] = 1e-6`, `solver.options['max_iter'] = 1000`, `solver.options['print_level'] = 0`.
- For convex QP: `solver = pyo.SolverFactory("highs")`. Set options: `solver.options['time_limit'] = [TIME_LIMIT]`, `solver.options['presolve'] = 'on'`.
- Avoid setting options that may cause conflicts (e.g., `threads` in HiGHS if the environment is already configured).

### Step 2 - Solve and Check Status
- Solve the model.
- Check `results.solver.status == pyo.SolverStatus.ok` and accept termination conditions `pyo.TerminationCondition.optimal`, `pyo.TerminationCondition.locallyOptimal`, or `pyo.TerminationCondition.feasible`.
- If status is not acceptable, output a structured JSON error payload. Do not output any numeric result.

### Step 3 - Validate and Analyze Solution
- Extract weights and compute portfolio return and variance.
- Verify all constraints are satisfied within tolerance (e.g., 1e-6).
- Optionally, perform a local perturbation test to confirm optimality.
- **Check constraint binding status**: If dual values are available, verify that the return target constraint is binding (dual > 0) or non-binding (dual ≈ 0) as expected. If duals are not available (e.g., HiGHS for QP), compute the difference between achieved return and target to confirm binding status and report it. If the constraint is non-binding, confirm the solution is not artificially constrained by an overly loose target. Accept a non-binding constraint as a valid solution; do not adjust parameters to force it to become binding.

### Step 4 - Output Structured Results
- Output a JSON payload containing status, objective value, weights, portfolio return, and constraint satisfaction flags.
- Ensure all values are JSON-serializable (convert numpy types to Python floats/ints).
- **If input data was assumed or fabricated**: Include a `data_quality` field in the payload stating the assumption and that the result is illustrative, not a definitive answer.
- **If data is incomplete and no fallback was used**: Output a partial formulation or a clear explanation of what is needed to complete the solution. Do not output an empty result.

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
    weights = [float(pyo.value(model.w[i])) for i in model.assets]
    portfolio_variance = float(pyo.value(model.obj))
    portfolio_return = sum(r[i] * weights[i] for i in model.assets)

    # Constraint validation
    budget_sat = abs(sum(weights) - 1.0) < 1e-6
    return_sat = portfolio_return >= R_min - 1e-6
    bounds_sat = all(0.0 <= w <= w_max + 1e-6 for w in weights)

    # Check binding status for return constraint
    return_binding = abs(portfolio_return - R_min) < 1e-6

    payload = {
        "status": "success",
        "portfolio_variance": portfolio_variance,
        "portfolio_return": portfolio_return,
        "weights": weights,
        "constraints_satisfied": {
            "budget": bool(budget_sat),
            "return_target": bool(return_sat),
            "weight_bounds": bool(bounds_sat)
        },
        "return_constraint_binding": bool(return_binding)
    }
    # If data was assumed, add qualification
    # payload["data_quality"] = "illustrative: covariance matrix assumed as identity"
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
- Presenting results from fabricated data as definitive answers without qualification.
- Using the solver to "verify" fabricated data by running multiple trials with different assumed matrices.
- **Failing to check constraint binding status**: Always verify whether the return target constraint is binding or non-binding using dual values when available, or by comparing achieved return to target. A non-binding constraint may indicate the target is too low, and the solution may be suboptimal for the intended problem. Accept a non-binding constraint as a valid solution; do not adjust parameters to force it to become binding.
- **Outputting pseudo numeric answers when execution fails**: If solver status is not acceptable, never output a numeric result. Always output the structured JSON error payload instead.
- **Proceeding without all required problem elements**: Do not start modeling or solving if the problem statement specifies constraints but the input data is missing. First locate the correct data or request it once, then use a documented fallback.
- **Leaving the formulation empty when data is incomplete**: Even if the covariance matrix is missing, define the decision variables, constraints, and objective structure. Output a partial formulation with placeholders for the missing data, noting what is required to complete the objective.
- **Using a rank-deficient covariance matrix without regularization**: A rank-1 or otherwise singular covariance matrix can cause solver failures. Always add a small regularization term (e.g., `1e-6 * I`) to ensure strict positive definiteness.
- **Outputting multiple inconsistent `RESULT:` lines**: Execute a single clean solve after data completeness is verified. Do not print multiple variance values from different assumptions; the final output must be unambiguous.
