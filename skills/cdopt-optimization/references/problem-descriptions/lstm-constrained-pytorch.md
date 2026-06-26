---
title: Bidirectional LSTM with Constrained Weights (PyTorch)
source_url: https://cdopt.github.io/examples/rnn_lstm.html
source_file: rnn_lstm.html
prompt_kind: official_implementation_example
problem_family: manifold_constrained_neural_network
manifold: Stiefel
backend: torch
template_key: cdopt_torch_constrained_lstm
run_level: small_cpu_training
approval_required: true
---

# Bidirectional LSTM with Constrained Weights (PyTorch)

## Prompt Body

Use $cdopt-optimization.

Consider the official CDOpt PyTorch example that trains a bidirectional,
multi-layer LSTM on MNIST sequence data. Recurrent weights are constrained to
the Stiefel manifold through `LSTM_cdopt`, with the constraint dissolved into
the loss via `get_quad_penalty(model)`.

The per-batch training objective is

```text
minimize_W    CrossEntropy(logits, labels) + get_quad_penalty(model)
subject to    LSTM recurrent weights approximately lie on the Stiefel manifold.
```

Before any code or run, build a modeling checkpoint that records:

- input shape `(batch, seq_len, input_size)` with `batch_first=True`;
- bidirectional flag and how hidden/cell states are initialized
  (`2 * num_layers` stacks when bidirectional);
- constrained layer: `LSTM_cdopt(..., batch_first=True, bidirectional=...,
  manifold_class=stiefel_torch, penalty_param=)`;
- readout from the last time step (`output[:, -1, :]`) through a plain
  `nn.Linear` (output width `hidden_size * 2` when bidirectional);
- task loss and penalty aggregation;
- data source (official MNIST; smoke test should use tiny synthetic sequences
  on CPU);
- optimizer, epochs/steps, seed, and feasibility proxy (`lstm.quad_penalty()`).

Do not download datasets, install dependencies, or train until the model and
run plan are reviewed.

## Expected Modeling Signals

- Decision variables: LSTM recurrent weights; constrained part on Stiefel.
- Objective: classification loss plus quadratic penalty; training loss, not a
  single static optimum.
- Constraint/manifold: Stiefel via `LSTM_cdopt`.
- API specifics: import `LSTM_cdopt` and `get_quad_penalty` from `cdopt.nn`;
  tuple return `(output, (h_n, c_n))` from the LSTM forward pass.
- Shape checks: bidirectional doubles the feature width at the readout layer;
  initialize hidden/cell on the correct device.
- Feasibility proxy: `model.lstm.quad_penalty()` or `get_quad_penalty(model)`.
- Risk checks: layer count vs state tensor shapes, penalty magnitude, CPU-only
  tiny validation, not treating test accuracy as proof of constraint handling.
- After review, adapt from `references/cdopt_official_examples.md`
  (Template: PyTorch Constrained RNN/LSTM). For a tiny CPU check, generate a
  runner with `scripts/write_constrained_rnn_runner.py --cell-type lstm`.
