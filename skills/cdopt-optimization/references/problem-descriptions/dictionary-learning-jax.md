---
title: Dictionary Learning Accelerated By JIT
source_url: https://cdopt.github.io/examples/dictionary_learning_jax.html#problem-description
source_file: dictionary_learning_jax.html
prompt_kind: official_problem_description
problem_family: manifold_optimization
manifold: Stiefel
template_key: cdopt_jax_stiefel_jit
run_level: tiny_cpu_possible
approval_required: true
---

# Dictionary Learning Accelerated By JIT

## Prompt Body

Use $cdopt-optimization.

Consider the JAX version of the official CDOpt dictionary-learning example. The
mathematical model is the same orthogonal dictionary-learning problem:

```text
y_i = Q z_i,    i = 1, ..., m,
```

where `Q` is unknown and orthogonal, and `z_i` is sparse. Estimate the
orthogonal structure by solving

```text
minimize_X    - sum_{i=1}^m || y_i^T X ||_4^4
subject to    X^T X = I.
```

Build a modeling checkpoint first. Then decide whether the implementation route
should use JAX, whether JIT is useful for the chosen tiny test size, and how to
compare JIT and non-JIT behavior fairly. Do not generate code or run anything
until the model and solver route are reviewed.

## Expected Modeling Signals

- Decision variable: Stiefel matrix `X`.
- Objective: same dictionary-learning fourth-power objective as the SciPy/Torch
  example.
- Constraint/manifold: Stiefel manifold, `X^T X = I`.
- Solver candidates: CDOpt with JAX backend and SciPy `L-BFGS-B`, or Pymanopt /
  repository-native alternatives if local dependencies make JAX unsuitable.
- Risk checks: JAX install state, `jax_enable_x64`, warm-up timing, tiny problem
  size, and not confusing JIT benchmarking with solver correctness.
- After review, adapt from
  `references/cdopt_official_examples.md`.
