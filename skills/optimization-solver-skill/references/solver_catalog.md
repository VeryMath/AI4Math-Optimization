# Solver Catalog

Use this catalog to route a confirmed model to a solver ecosystem. Prefer the route that preserves the original problem structure, minimizes environment risk, and produces interpretable evidence.

## Primary Backends

### SDPT3

SDPT3 is a MATLAB/Octave solver for semidefinite-quadratic-linear programming. Use it when the problem has semidefinite, second-order-cone, linear-cone, or SQLP structure and MATLAB/Octave access is available or can be approved.

Primary sources:

- Official Toh page: https://blog.nus.edu.sg/mattohkc/softwares/sdpt3/
- Modern GitHub bundle: https://github.com/sqlp/sdpt3
- YALMIP solver note: https://yalmip.github.io/solver/sdpt3/

The direct SDPT3 data interface expects `blk`, `At`, `C`, and `b`. A generated wrapper may call `sdpt3`, `sqlp`, or `HSDsqlp`, but `sdpt3` is the preferred default unless the source repository already uses a lower-level entrypoint.

### CDOpt

CDOpt is a Python package for optimization on Riemannian manifolds through constraint dissolving functions. Use it when the problem has explicit manifold constraints and the user or repository provides an objective function and manifold definition.

Primary sources:

- Documentation: https://cdopt.github.io/md_files/intro.html
- Installation page: https://cdopt.github.io/md_files/installation.html
- Quickstart: https://cdopt.github.io/md_files/tutorials/quick_start.html

CDOpt supports NumPy/SciPy-style, PyTorch, and JAX-adjacent workflows. Treat optional backend installation and GPU/JAX setup as dependency work requiring approval.

## Modeling-Layer Routes

| Layer | Typical use | Solver route |
| --- | --- | --- |
| CVX | MATLAB convex modeling, SDP/SOCP/LP | existing CVX solver settings or approved SDPT3 route |
| YALMIP | MATLAB algebraic modeling, SDP/SOCP/MILP families | approved SDPT3/MOSEK/SeDuMi/SCS route |
| CVXPY | Python convex modeling | installed solver or approved conic backend |
| JuMP | Julia mathematical programming | repository-native solver choice |
| Pyomo | Python algebraic modeling | repository-native solver choice |

Do not add a modeling layer just because it is convenient. Prefer existing source conventions or a direct solver route unless the human approves an adapter.

## Routing Heuristic

| Problem evidence | Prefer | Notes |
| --- | --- | --- |
| `.mat` with `blk`, `At`, `C`, `b` | SDPT3 direct | MATLAB/Octave execution plan required |
| SDP/SOCP cone model in MATLAB | SDPT3 via direct data or existing CVX/YALMIP layer | preserve existing modeling code |
| Stiefel, Grassmann, sphere, oblique, hyperbolic, symplectic Stiefel | CDOpt | requires objective function and backend |
| Orthogonality-constrained neural network | CDOpt or repository-native solver | PyTorch/JAX dependency risk |
| Plain unconstrained smooth objective | SciPy or existing repo solver | CDOpt only if constraint dissolving is meaningful |
| Natural-language or LaTeX only | modeling checkpoint first | confirm the structured model before execution |
| Existing repository reproduces paper result | existing solver route | avoid unnecessary adapter generation |

## Evidence Expectations

- Conic solvers: objective values, primal/dual feasibility, gap, termination code, certificates.
- Manifold solvers: objective value, gradient norm, feasibility/constraint violation, iteration history.
- Modeling layers: model dimensions, selected backend, solver status, raw solver log.
- Repository-native solvers: original metrics, convergence trace, parameters, runtime.

