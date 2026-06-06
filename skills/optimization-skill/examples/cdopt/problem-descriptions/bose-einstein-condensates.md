---
title: Bose-Einstein Condensates
source_url: https://cdopt.github.io/examples/bose_einstein_condensates.html#problem-description
source_file: bose_einstein_condensates.html
prompt_kind: official_problem_description
problem_family: nonlinear_sphere_optimization
manifold: sphere
template_key: cdopt_numpy_sphere
run_level: tiny_cpu_possible
approval_required: true
---

# Bose-Einstein Condensates

## Prompt Body

Use $optimization-skill.

Consider the simplified real-valued Bose-Einstein condensates model from the
official CDOpt example. Let `x` be a real vector on the unit sphere and let `A`
be the reviewed symmetric matrix from the discretized problem data. Use the
quartic nonlinear energy model

```text
minimize_x    0.5 x^T A x + alpha sum_i x_i^4
subject to    || x ||_2 = 1.
```

Build a modeling checkpoint first: identify the decision variable, objective,
sphere constraint, solver candidates, derivative/autograd choice, coefficient
conventions, and a tiny CPU validation plan. Do not generate code or run
anything until the model and solver route are reviewed.

## Expected Modeling Signals

- Decision variable: vector `x`.
- Objective: quadratic term plus quartic nonlinearity.
- Constraint/manifold: sphere, `||x||_2 = 1`.
- Solver candidates: CDOpt NumPy sphere with SciPy `L-BFGS-B`, Pymanopt,
  Manopt, or repository-native nonlinear constrained optimization.
- Risk checks: coefficient convention for the quartic term, real vs complex
  formulation, normalization, tiny dimension, and gradient review.
- After review, adapt from
  `skills/optimization-skill/references/cdopt_official_examples.md`.
