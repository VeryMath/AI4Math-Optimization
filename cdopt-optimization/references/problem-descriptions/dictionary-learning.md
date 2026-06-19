---
title: Dictionary Learning
source_url: https://cdopt.github.io/examples/dictionary_learning.html#problem-description
source_file: dictionary_learning.html
prompt_kind: official_problem_description
problem_family: manifold_optimization
manifold: Stiefel
template_key: cdopt_scipy_torch_stiefel
run_level: tiny_cpu_possible
approval_required: true
---

# Dictionary Learning

## Prompt Body

Use $cdopt-optimization.

Consider the dictionary-learning model from the official CDOpt example. The
data vectors are generated as

```text
y_i = Q z_i,    i = 1, ..., m,
```

where `Q` is an unknown orthogonal matrix and each `z_i` is a sparse
Bernoulli-Gaussian style latent vector. The goal is to recover the unknown
orthogonal structure from the observed data matrix `Y`.

Use the fourth-power objective over an orthogonality-constrained matrix:

```text
minimize_X    - sum_{i=1}^m || y_i^T X ||_4^4
subject to    X^T X = I.
```

Build a modeling checkpoint first: identify the decision variable, objective,
constraint set, manifold route, solver candidates, data-generation assumptions,
and a tiny CPU validation plan. Do not generate code or run anything until the
model and solver route are reviewed.

## Expected Modeling Signals

- Decision variable: matrix `X`, usually square in the synthetic recovery test.
- Objective: negative fourth-power sparsity-promoting score based on `Y^T X` or
  equivalent row/column convention after shape review.
- Constraint/manifold: Stiefel manifold, `X^T X = I`.
- Solver candidates: CDOpt + SciPy `L-BFGS-B` wrapper, Pymanopt, Manopt, or a
  repository-native route if one already exists.
- Risk checks: orientation of `Y`, sign convention, tensor backend, seed, and
  whether synthetic dimensions are small enough for a smoke test.
- After review, adapt from
  `references/cdopt_official_examples.md`.
