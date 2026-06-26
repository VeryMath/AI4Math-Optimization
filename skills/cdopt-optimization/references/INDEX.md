# CDOpt Reference Index

Use this file to choose the smallest reference needed for the task.

## Package Validation

Start with `../scripts/check_cdopt_environment.py`.

If the post-install CDOpt manifold smoke test exists (default `~/cdopt_manifold_tests/run_all_notebooks.py`, or the path reported as `smoke_test.path` by `check_cdopt_environment.py`, or `$CDOPT_SMOKE_TEST`), it is the preferred preflight. Treat it as API validation, not as an application benchmark.

## Local Problem Description Cards

Read a card in `problem-descriptions/` when the user wants a modeling prompt or a concrete CDOpt example.

Available cards:

SciPy-optimization family (Optimization via SciPy):

- `problem-descriptions/dictionary-learning.md`
- `problem-descriptions/dictionary-learning-jax.md`
- `problem-descriptions/kohn-sham-1d.md`
- `problem-descriptions/nearest-correlation.md`
- `problem-descriptions/bose-einstein-condensates.md`
- `problem-descriptions/symplectic-eigenvalue.md`

Constrained neural-network family (Training NN with manifold constraints):

- `problem-descriptions/lenet-orthogonal-pytorch.md`
- `problem-descriptions/lenet-orthogonal-jax.md`
- `problem-descriptions/rnn-constrained-pytorch.md`
- `problem-descriptions/lstm-constrained-pytorch.md`

Multi-layer RNN, sine-sequence LSTM, and distributed PyTorch pages remain
template-level references in `cdopt_official_examples.md` only.

Use each card's `Prompt Body` as the modeling source. Use `Expected Modeling Signals` only for review.

Ready-to-paste prompts for every card live in `example_prompts.md`.

## Official Problem-Code Pairs

Read `few_shots/cdopt_official_pairs.md` only after the current problem matches an official CDOpt example family and the model has been reviewed.

Do not read every pair by default. Search by example title or manifold family first:

```bash
rg -n "Dictionary Learning|Kohn-Sham|Nearest Correlation|Bose-Einstein|Symplectic" references/few_shots/cdopt_official_pairs.md
```

## Implementation Templates

Read `cdopt_official_examples.md` after model review when adapting code. This file is a template reference, not proof that the model is correct.

Template families:

- SciPy wrapper around `cdopt.core.problem`
- NumPy Stiefel with manual derivatives
- JAX Stiefel with JIT comparison
- PyTorch neural-network constrained layers
- JAX/Flax constrained layers
- Distributed PyTorch CDOpt

## Adapted-Code Review

Use this checklist only when adapting official examples, mixing backends, using
distributed training, or preparing results for delivery. It is not needed for
package validation, static runner generation, or smoke tests.

Check:

- manifold family, shape, dtype, and device match the reviewed model
- objective, gradients, constraints, and penalties map back to the checkpoint
- initialization, random seed, data dimensions, and stopping criteria are stated
- official code structure is adapted to the reviewed model, not copied verbatim
- saved metrics are enough to support the intended conclusion

## Comparison Experiments

Use comparison experiments only for solver/backend/baseline selection or
evidence-backed reports. Do not run them by default for single-method validation.

Before running, write `comparison_plan.md` and ask for approval. Include:

- compared methods, such as `L-BFGS-B` vs `CG`, Torch vs JAX, or CDOpt vs an
  Euclidean baseline
- shared data, dimensions, seeds, initialization policy, stopping criteria, and
  budget limits
- metrics to compare: objective, feasibility, stationarity proxy, iterations,
  evaluations, elapsed CPU time, warnings, and failure status
- artifact layout: one JSON summary per method plus `comparison_table.csv`
- known caveats, including non-identical gradients, backend precision, hardware,
  or solver termination semantics

After approved runs, write `COMPARISON_SUMMARY.md` from saved files under
`results/` and `logs/`. Do not base cross-method conclusions on console snippets
or chat memory.
