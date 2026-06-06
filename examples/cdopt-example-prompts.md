# CDOpt Local Problem Description Cards

English | [简体中文](cdopt-example-prompts.zh-CN.md)

These prompts test `$optimization-skill` with local Markdown cards derived from
the official CDOpt examples. The coding-agent workflow should read the local
card first; the official URL is kept as provenance, not as the primary prompt
source.

Use pattern:

```text
Use $optimization-skill.

Read this local Problem Description card:
examples/cdopt/problem-descriptions/<card-name>.md

Treat the card's `## Prompt Body` section as the official Problem Description
prompt. If running this manually, paste the official Problem Description from
that local Problem Description card into the session.

Build the modeling checkpoint first. Only after model review, read the matched
problem-code pair:
skills/optimization-skill/references/few_shots/cdopt_official_pairs.md

Then use the matching Implementation Template reference only if code adaptation
is appropriate:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

The local cards are prompt materials. The problem-code pairs keep the official
problem statement next to the corresponding solving code. The implementation
templates are separate and live in
`skills/optimization-skill/references/cdopt_official_examples.md`.

## Prompt 0: Local Card Map

```text
Use $optimization-skill.

Read the local CDOpt Problem Description cards under:
examples/cdopt/problem-descriptions/

For each card, treat `## Prompt Body` as the standalone modeling-test prompt and
use `## Expected Modeling Signals` only for review. Pages without a local card
are Implementation Template examples, not prompt examples.

Do not copy the official code verbatim. Do not install packages or run code.
```

## Prompt 1: Dictionary Learning

Local card:
`examples/cdopt/problem-descriptions/dictionary-learning.md`

Source:
https://cdopt.github.io/examples/dictionary_learning.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/dictionary-learning.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing the CDOpt / SciPy / L-BFGS-B route.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 2: Dictionary Learning Accelerated By JIT

Local card:
`examples/cdopt/problem-descriptions/dictionary-learning-jax.md`

Source:
https://cdopt.github.io/examples/dictionary_learning_jax.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/dictionary-learning-jax.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before deciding whether JAX/JIT is useful for this run.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 3: Discretized 1D Kohn-Sham Equation

Local card:
`examples/cdopt/problem-descriptions/kohn-sham-1d.md`

Source:
https://cdopt.github.io/examples/nonlinear_eigenvalue.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/kohn-sham-1d.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before reviewing derivatives or solver code.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 4: Low-Rank Nearest Correlation Estimation

Local card:
`examples/cdopt/problem-descriptions/nearest-correlation.md`

Source:
https://cdopt.github.io/examples/nearest_correlation_estimation.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/nearest-correlation.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing an oblique-manifold route.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 5: Bose-Einstein Condensates

Local card:
`examples/cdopt/problem-descriptions/bose-einstein-condensates.md`

Source:
https://cdopt.github.io/examples/bose_einstein_condensates.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/bose-einstein-condensates.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing a sphere-manifold route.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 6: Symplectic Eigenvalue Problem

Local card:
`examples/cdopt/problem-descriptions/symplectic-eigenvalue.md`

Source:
https://cdopt.github.io/examples/symplectic_eigenvalue.html#problem-description

```text
Use $optimization-skill.

Read the local Problem Description card:
examples/cdopt/problem-descriptions/symplectic-eigenvalue.md

Treat `## Prompt Body` as the official Problem Description prompt. Build the
modeling checkpoint before choosing a symplectic-Stiefel route.

After model review, use:
skills/optimization-skill/references/cdopt_official_examples.md

Do not copy the official code verbatim. Do not install dependencies or run code
without approval.
```

## Prompt 7: PyTorch LeNet Template Check

Source:
https://cdopt.github.io/examples/LeNet_orth.html

```text
Use $optimization-skill.

This CDOpt official page does not provide a standalone local Problem Description
card:
https://cdopt.github.io/examples/LeNet_orth.html

Classify it as an Implementation Template example. Use:
skills/optimization-skill/references/cdopt_official_examples.md

Explain what a separate modeling-test prompt would need before adapting the
PyTorch constrained-layer code.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 8: JAX/FLAX LeNet Template Check

Source:
https://cdopt.github.io/examples/LeNet_orth_jax.html

```text
Use $optimization-skill.

This CDOpt official page does not provide a standalone local Problem Description
card:
https://cdopt.github.io/examples/LeNet_orth_jax.html

Classify it as an Implementation Template example. Use:
skills/optimization-skill/references/cdopt_official_examples.md

Explain what a separate modeling-test prompt would need before adapting the
JAX/FLAX constrained-layer code.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```

## Prompt 9: RNN Template Check

Sources:
- https://cdopt.github.io/examples/rnn_single_layer.html
- https://cdopt.github.io/examples/rnn_multi_layer.html
- https://cdopt.github.io/examples/rnn_lstm.html
- https://cdopt.github.io/examples/sine_sequence.html

```text
Use $optimization-skill.

These CDOpt official pages are implementation-template examples rather than
standalone local Problem Description cards:
- https://cdopt.github.io/examples/rnn_single_layer.html
- https://cdopt.github.io/examples/rnn_multi_layer.html
- https://cdopt.github.io/examples/rnn_lstm.html
- https://cdopt.github.io/examples/sine_sequence.html

Use `skills/optimization-skill/references/cdopt_official_examples.md` to
classify the constrained recurrent-layer template.

Explain what a separate modeling-test prompt would need before adapting the
PyTorch RNN/LSTM code.

Do not copy the official code verbatim. Do not install dependencies, download
data, or train without approval.
```
