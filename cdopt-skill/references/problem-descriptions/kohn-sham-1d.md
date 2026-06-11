---
title: Discretized 1D Kohn-Sham Equation
source_url: https://cdopt.github.io/examples/nonlinear_eigenvalue.html#problem-description
source_file: nonlinear_eigenvalue.html
prompt_kind: official_problem_description
problem_family: nonlinear_eigenvalue
manifold: Stiefel
template_key: cdopt_numpy_stiefel_manual_derivatives
run_level: tiny_cpu_possible
approval_required: true
---

# Discretized 1D Kohn-Sham Equation

## Prompt Body

Use $cdopt-skill.

Consider the discretized one-dimensional Kohn-Sham model from the official
CDOpt nonlinear eigenvalue example. Let `X in R^{n x p}` collect `p` orthonormal
states. Let `L` be the one-dimensional finite-difference Laplacian-like
tridiagonal matrix with diagonal entries `2` and first off-diagonal entries
`-1`. Define

```text
rho(X) = diag(X X^T).
```

Use the constrained energy model

```text
minimize_X    0.5 trace(X^T L X) + (alpha / 4) rho(X)^T L^{-1} rho(X)
subject to    X^T X = I_p.
```

Build a modeling checkpoint first: identify the variable, density term,
objective, constraint, derivative requirements, solver route, and a tiny CPU
validation plan. Do not generate code or run anything until the model and solver
route are reviewed.

## Expected Modeling Signals

- Decision variable: `X in R^{n x p}`.
- Objective: quadratic kinetic term plus nonlinear density interaction using a
  solve with `L`.
- Constraint/manifold: Stiefel manifold, `X^T X = I_p`.
- Solver candidates: CDOpt NumPy manifold with SciPy `L-BFGS-B`, Pymanopt, or a
  repository-native nonlinear eigenvalue route.
- Risk checks: dimensions, boundary convention in `L`, coefficient of the
  density term, reviewed Euclidean gradient, and optional Hessian-vector product.
- After review, adapt from
  `references/cdopt_official_examples.md`.
