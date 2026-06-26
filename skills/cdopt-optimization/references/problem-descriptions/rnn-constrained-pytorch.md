---
title: Single-Layer RNN with Constrained Weights (PyTorch)
source_url: https://cdopt.github.io/examples/rnn_single_layer.html
source_file: rnn_single_layer.html
prompt_kind: official_implementation_example
problem_family: manifold_constrained_neural_network
manifold: Stiefel
backend: torch
template_key: cdopt_torch_constrained_rnn
run_level: small_cpu_training
approval_required: true
---

# Single-Layer RNN with Constrained Weights (PyTorch)

## Prompt Body

Use $cdopt-optimization.

Consider the official CDOpt PyTorch example that treats each MNIST image as a
sequence of 28 time steps with 28 features per step, and trains a vanilla RNN
whose recurrent weights are constrained to the Stiefel manifold via
`RNN_cdopt`. The constraint is dissolved into the loss through a quadratic
penalty added every training step.

The per-batch training objective is

```text
minimize_W    CrossEntropy(logits, labels) + get_quad_penalty(model)
subject to    recurrent weights approximately lie on the Stiefel manifold.
```

Before any code or run, build a modeling checkpoint that records:

- sequence layout: `(batch, seq_len, input_size)` before permuting to
  `(seq_len, batch, input_size)` for `RNN_cdopt`;
- hidden-state initialization shape `(1, batch, hidden_size)`;
- which recurrent layer is constrained (`RNN_cdopt` with
  `manifold_class=stiefel_torch`, `penalty_param=`);
- readout head (plain `nn.Linear` from final hidden state to classes);
- task loss (`nn.CrossEntropyLoss`) and `get_quad_penalty(model)` in the loss;
- data source (official MNIST; smoke test should use a tiny synthetic sequence
  batch on CPU);
- optimizer, steps/epochs, seed, and feasibility proxy (`rnn.quad_penalty()`).

Do not download datasets, install dependencies, or train until the model and
run plan are reviewed.

## Expected Modeling Signals

- Decision variables: RNN recurrent weights; constrained part lives on Stiefel.
- Objective: sequence-classification loss plus aggregated quadratic penalty.
- Constraint/manifold: Stiefel on recurrent weights via `RNN_cdopt`.
- API specifics: import `RNN_cdopt` and `get_quad_penalty` from `cdopt.nn`
  (official RNN pages) or the equivalent export from `cdopt.nn.modules`;
  pass `manifold_class=stiefel_torch`, not a manifold instance.
- Shape checks: permute batch/sequence axes correctly; final logits reshaped to
  `(batch, num_classes)`.
- Feasibility proxy: `model.rnn.quad_penalty()` or `get_quad_penalty(model)`.
- Risk checks: `batch_size` fixed in model `__init__` in the official example,
  hidden-state device, CPU-only tiny validation, deterministic seed.
- After review, adapt from `references/cdopt_official_examples.md`
  (Template: PyTorch Constrained RNN/LSTM). For a tiny CPU check, generate a
  runner with `scripts/write_constrained_rnn_runner.py --cell-type rnn`.
