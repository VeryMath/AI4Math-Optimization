---
title: Low-Rank Nearest Correlation Estimation
source_url: https://cdopt.github.io/examples/nearest_correlation_estimation.html#problem-description
source_file: nearest_correlation_estimation.html
prompt_kind: official_problem_description
problem_family: low_rank_matrix_optimization
manifold: oblique
template_key: cdopt_scipy_torch_oblique
run_level: tiny_cpu_possible
approval_required: true
---

# Low-Rank Nearest Correlation Estimation

## Prompt Body

Use $cdopt-skill.

Consider the official CDOpt low-rank nearest-correlation model. Given a
symmetric target matrix `G` and a nonnegative symmetric weight matrix `H`, find
a correlation matrix `W` that stays close to `G` under weighted Frobenius loss,
has unit diagonal, and has rank at most `p`.

Use the low-rank factorization `W = X X^T`, where each row of `X in R^{n x p}`
has unit Euclidean norm:

```text
minimize_X    0.5 || H o (X X^T - G) ||_F^2
subject to    || x_i ||_2 = 1,    i = 1, ..., n.
```

Here `o` denotes elementwise multiplication and `x_i` is row `i` of `X`. Build a
modeling checkpoint first: identify the decision variable, factorized
objective, row-norm constraints, manifold route, solver candidates, memory
risks, and a tiny CPU validation plan. Do not generate code or run anything
until the model and solver route are reviewed.

## Expected Modeling Signals

- Decision variable: low-rank factor `X in R^{n x p}`.
- Objective: weighted Frobenius distance between `X X^T` and `G`.
- Constraint/manifold: oblique manifold with unit-norm rows.
- Solver candidates: CDOpt + SciPy `L-BFGS-B`, Pymanopt, Manopt, or
  repository-native low-rank optimization.
- Risk checks: symmetry of `G` and `H`, nonnegative weights, row-vs-column
  convention for the oblique manifold, rank parameter `p`, and dense `n x n`
  memory cost.
- After review, adapt from
  `references/cdopt_official_examples.md`.
