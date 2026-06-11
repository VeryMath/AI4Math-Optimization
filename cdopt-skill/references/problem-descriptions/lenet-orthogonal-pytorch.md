---
title: LeNet with Orthogonality-Constrained Convolution Kernels (PyTorch)
source_url: https://cdopt.github.io/examples/LeNet_orth.html
source_file: LeNet_orth.html
prompt_kind: official_implementation_example
problem_family: manifold_constrained_neural_network
manifold: Stiefel
backend: torch
template_key: cdopt_torch_constrained_layers
run_level: small_cpu_training
approval_required: true
---

# LeNet with Orthogonality-Constrained Convolution Kernels (PyTorch)

## Prompt Body

Use $cdopt-skill.

Consider the official CDOpt PyTorch example that trains a LeNet-style CNN whose
convolution kernels are constrained to the Stiefel manifold (orthonormal
filters). Instead of projecting weights after each step, CDOpt dissolves the
constraint into the loss: each constrained layer contributes a quadratic
penalty, and the network is trained by ordinary `torch.optim` optimizers.

The training objective per batch is

```text
minimize_W    task_loss(model(x), y) + sum_layers penalty_param * || W^T W - I ||_F^2 / scaling
subject to    each constrained kernel approximately lies on the Stiefel manifold.
```

Before any code or run, build a modeling checkpoint that records:

- which layers carry the manifold constraint and the manifold type (Stiefel);
- the constrained-layer construction route (`Conv2d_cdopt` / `Linear_cdopt`
  with `manifold_class=` and `penalty_param=`, or wrapping a plain layer with
  `set_constraint_dissolving`);
- the task loss (`F.nll_loss` over `log_softmax` for classification);
- how the quadratic penalty enters the loss via `get_quad_penalty(model)`;
- data source and size (the official run uses MNIST; a smoke test should use a
  tiny synthetic batch instead of downloading data);
- optimizer, learning rate, number of steps, device (CPU for validation), and
  the feasibility proxy to report.

Do not download datasets, install dependencies, or train until the model and
run plan are reviewed.

## Expected Modeling Signals

- Decision variables: convolution/linear weights; constrained kernels live on
  the Stiefel manifold (`W^T W = I`).
- Objective: classification loss plus the aggregated constraint-dissolving
  quadratic penalty; this is a training loss, not a single static optimum.
- Constraint/manifold: Stiefel, applied per constrained layer via
  `manifold_class=stiefel_torch`.
- API specifics: import from `cdopt.nn.modules`
  (`Conv2d_cdopt`, `Linear_cdopt`, `get_quad_penalty`) and
  `cdopt.manifold_torch` (`stiefel_torch`); pass the manifold CLASS, not an
  instance; add `get_quad_penalty(model)` to the loss every step.
- Feasibility proxy: `layer.quad_penalty()` or `get_quad_penalty(model)` should
  stay small; report it instead of a stationarity norm.
- Risk checks: kernel/channel shapes vs Stiefel dimension order, `penalty_param`
  magnitude, CPU-only and tiny-data for validation, deterministic seed, and not
  treating training accuracy as a correctness proof.
- After review, adapt from `references/cdopt_official_examples.md`
  (Template: PyTorch Neural Network With Constrained Layers). For a tiny
  deterministic CPU check, generate a runner with
  `scripts/write_constrained_layer_runner.py`.
