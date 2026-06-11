# CDOpt Example Prompts

These prompts exercise `$cdopt-skill` with the local Problem Description cards in
`references/problem-descriptions/`. The coding-agent workflow should read the
local card first; the official URL is kept as provenance, not as the primary
prompt source.

All paths below are relative to the skill root (`cdopt-skill/`).

Use pattern:

```text
Use $cdopt-skill.

Read this local Problem Description card:
references/problem-descriptions/<card-name>.md

Treat the card's `## Prompt Body` section as the official Problem Description
prompt. Build the modeling checkpoint first. Only after model review, read the
matched problem-code pair:
references/few_shots/cdopt_official_pairs.md

Then use the matching Implementation Template only if code adaptation is
appropriate:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 0: Local Card Map

```text
Use $cdopt-skill.

Read the local CDOpt Problem Description cards under:
references/problem-descriptions/

For each card, treat `## Prompt Body` as the standalone modeling-test prompt and
use `## Expected Modeling Signals` only for review. Pages without a local card
are Implementation Template examples, not prompt examples.

Do not copy the official code verbatim. Do not install packages or run code.
```

## Prompt 1: Dictionary Learning

Local card: `references/problem-descriptions/dictionary-learning.md`
Source: https://cdopt.github.io/examples/dictionary_learning.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/dictionary-learning.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing the CDOpt / SciPy / L-BFGS-B route.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 2: Dictionary Learning Accelerated By JIT

Local card: `references/problem-descriptions/dictionary-learning-jax.md`
Source: https://cdopt.github.io/examples/dictionary_learning_jax.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/dictionary-learning-jax.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before deciding whether JAX/JIT is useful for this run.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 3: Discretized 1D Kohn-Sham Equation

Local card: `references/problem-descriptions/kohn-sham-1d.md`
Source: https://cdopt.github.io/examples/nonlinear_eigenvalue.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/kohn-sham-1d.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before reviewing derivatives or solver code.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 4: Low-Rank Nearest Correlation Estimation

Local card: `references/problem-descriptions/nearest-correlation.md`
Source: https://cdopt.github.io/examples/nearest_correlation_estimation.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/nearest-correlation.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing an oblique-manifold route.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 5: Bose-Einstein Condensates

Local card: `references/problem-descriptions/bose-einstein-condensates.md`
Source: https://cdopt.github.io/examples/bose_einstein_condensates.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/bose-einstein-condensates.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing a sphere-manifold route.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 6: Symplectic Eigenvalue Problem

Local card: `references/problem-descriptions/symplectic-eigenvalue.md`
Source: https://cdopt.github.io/examples/symplectic_eigenvalue.html#problem-description

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/symplectic-eigenvalue.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing a symplectic-Stiefel route.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 7: LeNet Orthogonal-Kernel Training (PyTorch)

Local card: `references/problem-descriptions/lenet-orthogonal-pytorch.md`
Source: https://cdopt.github.io/examples/LeNet_orth.html

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/lenet-orthogonal-pytorch.md

Treat `## Prompt Body` as the official example. Build the modeling checkpoint
(constrained layers, Stiefel manifold, penalty_param, get_quad_penalty in the
loss, tiny synthetic CPU batch) before any code.

After model review, use:
references/cdopt_official_examples.md

For a tiny deterministic CPU check, generate the runner with
scripts/write_constrained_layer_runner.py and run it only after approval.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 8: LeNet Orthogonal-Kernel Training (JAX/FLAX)

Local card: `references/problem-descriptions/lenet-orthogonal-jax.md`
Source: https://cdopt.github.io/examples/LeNet_orth_jax.html

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/lenet-orthogonal-jax.md

Treat `## Prompt Body` as the official example. Build the modeling checkpoint
(Conv_cdopt / Dense_cdopt returning (output, quad_penalty), penalty coefficient,
tiny synthetic CPU batch) before any code.

After model review, use:
references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 9: Single-Layer RNN with Constrained Weights (PyTorch)

Local card: `references/problem-descriptions/rnn-constrained-pytorch.md`
Source: https://cdopt.github.io/examples/rnn_single_layer.html

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/rnn-constrained-pytorch.md

Treat `## Prompt Body` as the official example. Build the modeling checkpoint
(sequence layout, RNN_cdopt, hidden-state init, get_quad_penalty, tiny synthetic
CPU batch) before any code.

After model review, use:
references/cdopt_official_examples.md

For a tiny deterministic CPU check, generate the runner with
scripts/write_constrained_rnn_runner.py --cell-type rnn and run it only after
approval.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 10: Bidirectional LSTM with Constrained Weights (PyTorch)

Local card: `references/problem-descriptions/lstm-constrained-pytorch.md`
Source: https://cdopt.github.io/examples/rnn_lstm.html

```text
Use $cdopt-skill.

Read the local Problem Description card:
references/problem-descriptions/lstm-constrained-pytorch.md

Treat `## Prompt Body` as the official example. Build the modeling checkpoint
(batch_first layout, LSTM_cdopt, bidirectional readout width, get_quad_penalty,
tiny synthetic CPU batch) before any code.

After model review, use:
references/cdopt_official_examples.md

For a tiny deterministic CPU check, generate the runner with
scripts/write_constrained_rnn_runner.py --cell-type lstm and run it only after
approval.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 11: Multi-Layer RNN / Sine Sequence / Distributed Template Checks

These official pages do not provide standalone local Problem Description cards.
Treat them as Implementation Template examples, not prompt examples.

Sources:
- https://cdopt.github.io/examples/rnn_multi_layer.html
- https://cdopt.github.io/examples/sine_sequence.html
- https://cdopt.github.io/examples/distributed_linear_basic.html
- https://cdopt.github.io/examples/distributed_rnn_basic.html

```text
Use $cdopt-skill.

These CDOpt official pages are Implementation Template examples, not standalone
Problem Description cards. Use:
references/cdopt_official_examples.md

Classify the template (deeper RNN/LSTM stacks, sequence prediction heads, or
distributed RPC training) and explain what a separate modeling-test prompt would
need before adapting the code. Distributed examples require a separate run plan,
resource estimate, and approval.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```
