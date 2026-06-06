---
title: Symplectic Eigenvalue Problem
source_url: https://cdopt.github.io/examples/symplectic_eigenvalue.html#problem-description
source_file: symplectic_eigenvalue.html
prompt_kind: official_problem_description
problem_family: symplectic_manifold_optimization
manifold: symplectic Stiefel
template_key: cdopt_scipy_torch_symplectic_stiefel
run_level: tiny_cpu_possible
approval_required: true
---

# Symplectic Eigenvalue Problem

## Prompt Body

Use $optimization-skill.

Consider the official CDOpt symplectic eigenvalue model. Let `L` be a symmetric
positive definite matrix and let `J_n` and `J_p` be the canonical symplectic
matrices of compatible sizes. Optimize over a symplectic Stiefel variable `X`
using the model

```text
minimize_X    0.5 trace(X^T L X)
subject to    X^T J_n X = J_p.
```

Build a modeling checkpoint first: identify the decision variable, objective,
symplectic constraint, shape convention, manifold route, solver candidates, and
a tiny CPU validation plan. Do not generate code or run anything until the model
and solver route are reviewed.

## Expected Modeling Signals

- Decision variable: matrix `X` with shape compatible with `J_n` and `J_p`.
- Objective: trace quadratic involving positive definite `L`.
- Constraint/manifold: symplectic Stiefel constraint `X^T J_n X = J_p`.
- Solver candidates: CDOpt + SciPy `L-BFGS-B`, Manopt-style route, or a
  repository-native symplectic manifold implementation.
- Risk checks: canonical symplectic matrix convention, dimensions `2n x 2p`,
  initialization on the manifold, and constraint residual reporting.
- After review, adapt from
  `skills/optimization-skill/references/cdopt_official_examples.md`.
