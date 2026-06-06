# Implementation Templates

Use this file only after the model and solver route are reviewed. Templates are references for adaptation, not prompts and not automatically approved code.

## CVXPY Template

Use for convex LP, QP, SOCP, SDP, and some MILP models when the solver ecosystem is Python and CVXPY supports the required atoms.

Expected agent work:

- define dimensions and data explicitly
- choose variable domains such as continuous, boolean, integer, PSD
- select installed solvers such as CLARABEL, SCS, OSQP, ECOS_BB, HiGHS, CBC, GLPK_MI, Gurobi, or MOSEK when available
- report solver status, objective, residuals, and gap when exposed

## Pyomo Template

Use for algebraic LP, MILP, MIQP, and scheduling/operations-research models where sets, indices, and constraints are clearer in an algebraic modeling layer.

Expected agent work:

- define sets, parameters, variables, objective, constraints
- choose a backend such as HiGHS, CBC, GLPK, Gurobi, SCIP, or CPLEX according to availability
- preserve integer and binary variable declarations
- report termination condition, objective, gap, and incumbent information

## SciPy Template

Use for unconstrained or smooth constrained NLP, least squares, and small custom objectives.

Expected agent work:

- determine whether derivatives are available
- choose `minimize`, `least_squares`, or a repository-native routine
- state method choice such as L-BFGS-B, SLSQP, trust-constr, BFGS, CG, or least_squares
- report stationarity, feasibility, iterations, and status

## SDPT3 Template

Use for confirmed SQLP data or MATLAB/YALMIP/CVX conic workflows.

Expected agent work:

- confirm `blk`, `At`, `C`, and `b` data when using direct SDPT3
- preserve CVX/YALMIP source code when already present
- avoid fabricating conic data from natural language without review
- report primal/dual feasibility, gap, termcode, and warnings

## CDOpt Template

Use for confirmed manifold or Riemannian models.

Expected agent work:

- run or propose the CDOpt smoke test before solving
- identify backend: NumPy, PyTorch, JAX, or repository-native
- identify manifold constructor and shape
- define objective module/function or neural-network constrained layer adapter
- report objective, stationarity, feasibility, iterations, and backend/API failures

## Repository-Native Template

Use when existing code already implements the model, data loading, derivatives, benchmark harness, or paper reproduction path.

Expected agent work:

- read repository instructions before inventing an adapter
- preserve original command-line flags and output metrics
- make minimal local changes only when approved
- parse logs into a durable evidence summary

## Template Rule

Templates are selected after modeling. They are not substitutes for variables, objective, constraints, dimensions, and human model confirmation.
