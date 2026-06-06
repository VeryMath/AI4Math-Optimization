# Problem Type Taxonomy

Use this taxonomy after reading the concrete optimization problem and before selecting a solver route.

## Linear And Integer Models

- **LP:** continuous variables, linear objective, linear equalities/inequalities.
- **MILP:** at least one binary or integer variable, linear objective, linear constraints.
- **QP:** quadratic objective and linear constraints; convexity depends on the Hessian.
- **MIQP/MIQCP:** integer variables plus quadratic objective or quadratic constraints.

Typical signals: budgets, assignments, flows, set cover, facility location, scheduling, portfolio allocation, unit commitment, production planning.

## Conic And Semidefinite Models

- **SOCP:** second-order cone or norm constraints such as `||Ax+b||_2 <= c^T x + d`.
- **SDP:** symmetric matrix variables, positive semidefinite constraints, LMIs, trace objectives.
- **Conic LP/SQLP:** LP, SOCP, and SDP represented through cone blocks.

Typical signals: PSD matrix, covariance, Lyapunov inequality, relaxation, robust optimization, cone, LMI, semidefinite.

## Smooth Nonlinear Models

- **NLP:** nonlinear objective or constraints; may be constrained or unconstrained.
- **Least squares:** residual vector objective, often `min ||r(x)||^2`.
- **Structured scientific model:** objective and derivatives may come from simulation code.

Typical signals: nonlinear physics model, differentiable simulation, calibration, residuals, ODE/PDE discretization.

## Manifold And Riemannian Models

- **Manifold optimization:** variables constrained to sphere, Stiefel, Grassmann, oblique, symplectic Stiefel, hyperbolic, orthogonal/unitary matrices, or product manifolds.
- **Orthogonality-constrained neural network:** network weights constrained through Stiefel or related manifolds.

Typical signals: `X^T X = I`, unit norm rows, orthogonal dictionary learning, low-rank correlation factorization, Riemannian gradient, manifold layer.

## Repository-Native Models

Use repository-native classification when the source already contains a solver script, benchmark harness, data loader, custom derivative code, or paper-specific reproduction path. This route often preserves evidence better than generating a fresh adapter.

## Classification Output

A modeling checkpoint should include:

- primary problem type
- secondary problem type if ambiguous
- convexity evidence or uncertainty
- variable domains
- matrix/vector dimensions
- data source and missing data
- natural solver families
- risks that require human review
