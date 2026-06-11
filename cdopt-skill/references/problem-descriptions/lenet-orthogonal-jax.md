---
title: LeNet with Orthogonality-Constrained Convolution Kernels (JAX/FLAX)
source_url: https://cdopt.github.io/examples/LeNet_orth_jax.html
source_file: LeNet_orth_jax.html
prompt_kind: official_implementation_example
problem_family: manifold_constrained_neural_network
manifold: Stiefel
backend: jax_flax
template_key: cdopt_jax_flax_constrained_layers
run_level: small_cpu_training
approval_required: true
---

# LeNet with Orthogonality-Constrained Convolution Kernels (JAX/FLAX)

## Prompt Body

Use $cdopt-skill.

Consider the official CDOpt JAX/FLAX example that trains a LeNet-style CNN whose
convolution kernels are constrained to the Stiefel manifold. As in the PyTorch
version, the manifold constraint is dissolved into the loss: each CDOpt Linen
layer returns both its output and a quadratic penalty, and the model is trained
with `optax` optimizers under `jax.jit`.

The per-batch objective is

```text
minimize_W    cross_entropy(logits, labels) + 0.05 * quad_penalty
subject to    each constrained kernel approximately lies on the Stiefel manifold.
```

Before any code or run, build a modeling checkpoint that records:

- which layers carry the manifold constraint and the manifold type (Stiefel);
- the CDOpt Linen layers used (`Conv_cdopt`, `Dense_cdopt` with
  `manifold_class=`), and that each returns `(output, quad_penalty)`;
- the loss (softmax cross entropy) and how `quad_penalty` is added with its
  coefficient;
- the train state / optimizer (`optax.sgd`, `flax.training.train_state`);
- data source and size (official run uses MNIST via `tensorflow_datasets`; a
  smoke test should use a tiny synthetic batch and `jax_enable_x64` off/on as
  needed);
- device (CPU for validation), steps, seed, and the feasibility proxy.

Do not download datasets, install dependencies, or train until the model and
run plan are reviewed.

## Expected Modeling Signals

- Decision variables: convolution/dense weights; constrained kernels live on
  the Stiefel manifold.
- Objective: cross-entropy plus a weighted `quad_penalty`; this is a training
  loss, not a single static optimum.
- Constraint/manifold: Stiefel, via `manifold_class=stiefel_jax`.
- API specifics: import from `cdopt.manifold_jax` (`stiefel_jax`, ...) and
  `cdopt.linen` (`Conv_cdopt`, `Dense_cdopt`); CDOpt Linen layers return a tuple
  `(output, quad_penalty)`, so thread the penalty through `loss_fn` and
  `jax.value_and_grad(loss_fn, has_aux=True)`.
- Feasibility proxy: the returned `quad_penalty` (official runs report it as
  `feas`) should stay small; report it instead of a stationarity norm.
- Risk checks: JAX/FLAX/optax install state, tuple-return handling, batch shape
  `[N, H, W, C]`, penalty coefficient, CPU-only tiny-data validation,
  deterministic PRNG seed, and not confusing JIT timing with correctness.
- After review, adapt from `references/cdopt_official_examples.md`
  (Template: JAX/FLAX Neural Network With Constrained Layers).
