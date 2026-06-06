# Solver Catalog

Use this catalog to route a confirmed model to a solver ecosystem. Prefer the route that preserves the original problem structure, minimizes environment risk, and produces interpretable evidence.

Important: not all listed routes have automatic code generation. Some routes are modeling recommendations, some are repository-native execution paths, and only a bounded subset currently has generated wrappers.

## Coverage By Problem Family

| Problem family | Common routes | Notes |
| --- | --- | --- |
| LP | CVXPY, SciPy/HiGHS, Pyomo, Gurobi, MOSEK, GLPK, CBC, repository-native | Check scale, sparsity, and license availability. |
| MILP | Pyomo, CVXPY, HiGHS, CBC, GLPK, Gurobi, SCIP, CPLEX, repository-native | Report incumbent, bound, integrality gap, and time-limit status. |
| QP | CVXPY, OSQP, SciPy, Gurobi, MOSEK, IPOPT, repository-native | Confirm convexity; nonconvex QP changes route and guarantees. |
| SOCP | CVXPY, CVX, YALMIP, MOSEK, SCS, ECOS, repository-native | Preserve cone form and scaling diagnostics. |
| SDP | CVX, YALMIP, CVXPY, SDPT3, MOSEK, SeDuMi, SCS, repository-native | Direct SDPT3 requires SQLP data or reviewed MATLAB construction. |
| NLP | SciPy, IPOPT, CasADi, Knitro, repository-native | Check derivatives, constraints, scaling, and local/global claims. |
| least squares | SciPy `least_squares`, CVXPY, Ceres-style repository code, custom Gauss-Newton/LM | Report residual norms and convergence status. |
| manifold | CDOpt, Manopt, Pymanopt, Geoopt, repository-native | Requires explicit manifold, objective, and backend. |
| Neural-network constrained | CDOpt, Geoopt, repository-native PyTorch/JAX code | Treat training as resource-dependent and approval-gated. |

## Primary Solver Notes

### CVXPY

Use CVXPY for Python convex modeling: LP, QP, SOCP, SDP, and some MILP models. Solver availability depends on installed backends such as CLARABEL, SCS, OSQP, HiGHS, CBC, GLPK_MI, ECOS_BB, Gurobi, and MOSEK.

### Pyomo

Use Pyomo for algebraic LP/MILP/MIQP models, especially operations-research problems with sets, indices, and many constraints. Candidate solvers include HiGHS, CBC, GLPK, Gurobi, SCIP, CPLEX, and MOSEK depending on model class and installation.

### SciPy And HiGHS

Use SciPy for `linprog` with HiGHS, smooth unconstrained or constrained NLP through `minimize`, and least-squares problems through `least_squares`. It is a good first route for small local checks when the mathematical guarantees are appropriate.

### Commercial MILP/Conic Solvers

Gurobi, MOSEK, CPLEX, and Knitro can be excellent routes when installed and licensed. Always mention license and environment risk and provide an open-source fallback when possible.

### CVX And YALMIP

Use CVX and YALMIP for MATLAB modeling. They are strong routes for SDP, SOCP, LP, and some MILP workflows when the source already uses MATLAB or the user wants MATLAB-compatible modeling.

### SDPT3

SDPT3 is a MATLAB/Octave solver for semidefinite-quadratic-linear programming. Use it when the problem has semidefinite, second-order-cone, linear-cone, or SQLP structure and MATLAB/Octave access is available or can be approved.

Primary sources:

- Official Toh page: https://blog.nus.edu.sg/mattohkc/softwares/sdpt3/
- Modern GitHub bundle: https://github.com/sqlp/sdpt3
- YALMIP solver note: https://yalmip.github.io/solver/sdpt3/

The direct SDPT3 data interface expects `blk`, `At`, `C`, and `b`. Current generated support creates direct MATLAB/Octave wrappers for confirmed SQLP data in `.mat` files.

### IPOPT And CasADi

Use IPOPT or CasADi for smooth constrained NLP when derivatives or automatic differentiation are available. Avoid global optimality claims unless the model and solver support them.

### CDOpt

CDOpt is a Python package for optimization on Riemannian manifolds through constraint dissolving functions. Use it when the problem has explicit manifold constraints and the user or repository provides an objective function and manifold definition.

Primary sources:

- Documentation: https://cdopt.github.io/md_files/intro.html
- Installation page: https://cdopt.github.io/md_files/installation.html
- Quickstart: https://cdopt.github.io/md_files/tutorials/quick_start.html

Before solving a CDOpt problem, use the local post-install manifold smoke test when available:

```bash
cd /Users/conanxu/cdopt_manifold_tests
python run_all_notebooks.py
```

This suite is installation/API validation, not an application benchmark. If it fails, diagnose the CDOpt environment before generating or running application-level CDOpt examples.

Current generated support: Python wrappers for confirmed manifold specs using CDOpt's constraint-dissolving problem object and SciPy `optimize.minimize`. Supported generated manifold families include sphere, oblique, Stiefel, Grassmann, generalized Stiefel, hyperbolic, and symplectic Stiefel variants for `torch`, `numpy`/`np`, or `jax` backends. The objective must be supplied as an importable module/function pair.

### Manopt, Pymanopt, And Geoopt

Use Manopt for MATLAB manifold optimization, Pymanopt for Python Riemannian optimization, and Geoopt for PyTorch-native manifold-aware optimization. These are route candidates when the model is manifold-constrained but CDOpt is not the best fit.

### Repository-Native

Use repository-native code when it preserves the original experiment, data loaders, derivatives, benchmark protocol, or solver configuration. This route often produces the best evidence for reproduction tasks.

## Routing Heuristic

| Problem evidence | Prefer | Notes |
| --- | --- | --- |
| `.mat` with `blk`, `At`, `C`, `b` | SDPT3 direct | MATLAB/Octave execution plan required. |
| Algebraic LP/MILP in prose | Pyomo or CVXPY | Stop at reviewed model if data is incomplete. |
| Small LP with arrays | SciPy/HiGHS or CVXPY | Good for quick local checks. |
| SDP/SOCP cone model in MATLAB | CVX/YALMIP/SDPT3 | Preserve existing modeling code. |
| Convex conic model in Python | CVXPY/MOSEK/SCS/CLARABEL | Solver depends on installed backend. |
| Stiefel, Grassmann, sphere, oblique, hyperbolic, symplectic Stiefel | CDOpt, Manopt, Pymanopt, Geoopt | Requires objective and backend. |
| Orthogonality-constrained neural network | CDOpt, Geoopt, or repository-native | Training is resource-dependent. |
| Smooth constrained NLP | IPOPT, CasADi, SciPy, repository-native | Check derivatives and scaling. |
| Plain unconstrained smooth objective | SciPy or existing repo solver | Use CDOpt only if manifold constraints are real. |
| Natural-language or LaTeX only | modeling checkpoint first | Confirm the structured model before execution. |
| Existing repository reproduces paper result | repository-native | Avoid unnecessary adapter generation. |

## Evidence Expectations

- LP/QP/SOCP/SDP/conic: objective values, primal/dual feasibility, gap, residuals, termination code, certificates when available.
- MILP: incumbent objective, best bound, integrality gap, node/time limit status, feasibility.
- NLP: objective value, constraint violation, stationarity, iteration count, local optimality status.
- Least squares: residual norm, gradient norm, robust loss if used, status.
- Manifold solvers: CDOpt preflight status when applicable, objective value, gradient norm, feasibility/constraint violation, iteration history.
- Modeling layers: dimensions, selected backend, solver status, raw solver log.
- Repository-native solvers: original metrics, convergence trace, parameters, runtime.
