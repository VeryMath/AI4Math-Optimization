---
name: cdopt-optimization
description: Use when Codex needs to solve, reproduce, test, compare, generate examples for, or diagnose CDOpt manifold optimization workflows, including CDOpt package smoke tests, official problem description cards, Stiefel dictionary learning, SciPy wrappers, PyTorch/JAX/NumPy CDOpt examples, dependency checks, tiny CPU validation runs, comparison plans, or JSON result reporting.
---

# CDOpt Optimization

## Overview

Use this skill as a CDOpt-specific workflow extracted from the broader optimization skill. Keep the same core discipline: model first, run only after approval, and report from durable evidence.

The center is CDOpt and manifold-constrained optimization. If the problem is not a CDOpt or Riemannian/manifold workflow, say that and route to a broader optimization skill or repository-native solver path instead of forcing CDOpt.

## Interaction

If a new session has not chosen a language, ask only:

```text
Would you like to work in Chinese or English?
```

After the language is known, ask for the concrete CDOpt task or optimization problem directly. Do not begin with a long questionnaire.

Classify the task as one of these modes:

- **Package validation:** check whether CDOpt and its numerical stack are installed and usable.
- **Smoke test:** run the local manifold notebook suite or a tiny CPU-only CDOpt problem after approval.
- **Problem modeling:** turn a natural-language, LaTeX, paper, or official Problem Description card into a reviewed model.
- **Code adaptation:** study an official CDOpt example for reference, then adapt it only after the model has been reviewed.
- **Comparison experiment:** compare solvers, backends, or baselines only when the user asks for method selection, a report, or reproducibility evidence.
- **Failure diagnosis:** inspect dependency errors, API mismatches, solver status, feasibility, stationarity, or numerical warnings.
- **Result interpretation:** summarize saved JSON/log evidence, not just console snippets.

## Workflow

1. Read the task and identify whether CDOpt is actually appropriate.
2. Before modeling, generating code, or running validation, create a task workspace under `outputs/{run_id}/`. Put checkpoints, generated code, logs, JSON results, and summaries for this task under that directory. Use a short, stable `run_id` such as `2026-06-11-dictionary-learning` or `stiefel-backend-comparison`.
3. For package validation, run:

```bash
python3 scripts/check_cdopt_environment.py --json
```

If `cdopt` is missing, stop and give the exact install command you would need. Do not install without approval.

4. For optimization problems, write a modeling checkpoint before executable code:
   - source evidence
   - variables and domains
   - manifold type and shape
   - objective and constraints
   - data and dimensions
   - backend choice: NumPy, Torch, JAX, or neural-network layer wrappers
   - candidate solver route and ambiguities

5. Ask the user to confirm, revise, reject, or skip the interpreted model before generating solver code from unstructured input.
6. Use `references/INDEX.md` to load only the relevant reference:
   - local Problem Description cards for modeling prompts
   - official problem-code pairs for matched examples
   - implementation templates after model review
   - comparison and adapted-code review protocols when requested
7. Before any CDOpt solve, prefer the local post-install smoke test when it exists. Resolve its path from the `check_cdopt_environment.py` JSON report (`smoke_test.path`) or the `CDOPT_SMOKE_TEST` environment variable; the default location is `~/cdopt_manifold_tests/run_all_notebooks.py`:

```bash
python3 "${CDOPT_SMOKE_TEST:-$HOME/cdopt_manifold_tests/run_all_notebooks.py}"
```

Treat this as installation/API validation, not as an application benchmark. Ask before running it unless the user already approved CDOpt validation in the current task.

8. For a standalone runner, generate the script inside the task workspace first, then run only after approval. Three generators are available:

- SciPy-optimization family (Stiefel dictionary learning):

```bash
python3 scripts/write_stiefel_dictionary_runner.py --output-dir .local/cdopt-runs/dictionary_learning_torch_scipy
python3 .local/cdopt-runs/dictionary_learning_torch_scipy/run_dictionary_learning.py --help
```

- Constrained neural-network family (PyTorch Stiefel-constrained layer):

```bash
python3 scripts/write_constrained_layer_runner.py --output-dir .local/cdopt-runs/constrained_layer_torch
python3 .local/cdopt-runs/constrained_layer_torch/run_constrained_layer.py --help
```

- Constrained RNN/LSTM family (PyTorch sequence models):

```bash
python3 scripts/write_constrained_rnn_runner.py --output-dir .local/cdopt-runs/constrained_rnn_torch
python3 .local/cdopt-runs/constrained_rnn_torch/run_constrained_rnn.py --cell-type rnn --help
python3 .local/cdopt-runs/constrained_rnn_torch/run_constrained_rnn.py --cell-type lstm --help
```

Keep the default run CPU-only, small, deterministic, synthetic-data, and JSON-producing. The `.local/cdopt-runs/...` paths above are maintainer examples; for user tasks, prefer `outputs/{run_id}/generated/...` and `outputs/{run_id}/results/...`.

9. For a comparison experiment, write `comparison_plan.md` before executable changes or runs. Keep the matrix minimal and explicit: methods/backends/baselines, shared data and dimensions, seed and initialization policy, stopping criteria, budget limits, metrics, artifact names, and known fairness caveats. Ask the user to approve the plan before running any comparison or expanding the matrix.

10. Report from saved artifacts. Prefer a JSON summary containing solver status, objective value, iterations, evaluations, gradient norm or stationarity proxy, feasibility, elapsed CPU time, CDOpt version/path, and command.

CDOpt solver summaries, comparison tables, and search improvements are
numerical evidence, not proof. If they create a theorem claim or proof
obligation, route the claim to `proof-blueprint-review` or
`lean-formalization`.

## CDOpt Patterns

Use these patterns as starting points after the mathematical model is reviewed.

### SciPy Wrapper

Use for small manifold problems and official SciPy-style examples.

```python
import cdopt
import scipy as sp

M = cdopt.manifold_torch.stiefel_torch((n, n), device=device, dtype=dtype)
problem_obj = cdopt.core.problem(M, obj_fun, beta="auto")

result = sp.optimize.minimize(
    problem_obj.cdf_fun_vec_np,
    problem_obj.Xinit_vec_np,
    jac=problem_obj.cdf_grad_vec_np,
    method="L-BFGS-B",
    options={"maxiter": 50, "gtol": 1e-6},
)
```

Use `L-BFGS-B` as the default tiny-run route. Treat CG as optional comparison evidence, especially if it exits with precision-loss warnings.

### Official Example Families

- Stiefel/Torch/SciPy: dictionary learning.
- Stiefel/JAX/JIT: JAX dictionary learning.
- NumPy Stiefel with derivatives: nonlinear eigenvalue or Kohn-Sham style examples.
- Oblique/Torch/SciPy: low-rank nearest correlation estimation.
- Sphere/NumPy: Bose-Einstein condensates.
- Symplectic Stiefel/Torch: symplectic eigenvalue problem.
- CDOpt neural-network layers: constrained Conv2d, Linear, RNN, LSTM, or JAX/Flax layer wrappers.

For distributed PyTorch examples, require a separate run plan, resource estimate, and approval. They are not smoke tests.

## Review Levels

Use the lightest review that matches the task risk:

- **Model review:** always required for optimization problems. Check the manifold, variables, dimensions, objective, constraints, backend, and solver route before code.
- **Code adaptation review:** required when adapting official examples, mixing backends, using distributed training, or preparing external results. Check that the manifold constructor, objective, gradients, data, initialization, stopping criteria, and reported metrics match the reviewed model. Do not copy official code verbatim without tying it back to the reviewed model.
- **Conclusion review:** required for comparison, tuning, publication, or delivery. Accept numerical claims only when they are supported by saved JSON/log artifacts and documented limitations.

Do not add a separate code-review step for pure dependency probes, static runner generation, or smoke tests that only validate package/API availability.

## Approval Gates

Ask before:

- installing or upgrading CDOpt, PyTorch, JAX, SciPy, or related dependencies
- running generated solver code
- running the local CDOpt smoke-test notebook suite
- running anything beyond a tiny CPU-only validation
- running a comparison experiment or expanding a comparison matrix
- changing Python environments, conda environments, paths, or system packages
- accepting final mathematical conclusions from numerical output
- copying official code verbatim instead of adapting a reviewed model

Dependency probing and static code generation are safe. Actual solver execution is not automatically safe.

## Output Layout

For every task, create and use one task workspace:

```text
outputs/{run_id}/
├── modeling_checkpoint.md
├── plan.md
├── generated/
├── logs/run.log
├── results/solver_summary.json
└── RUN_SUMMARY.md
```

For comparison experiments, extend the same workspace:

```text
outputs/{run_id}/
├── modeling_checkpoint.md
├── comparison_plan.md
├── generated/
├── logs/
├── results/
│   ├── method_a.json
│   ├── method_b.json
│   └── comparison_table.csv
└── COMPARISON_SUMMARY.md
```

Create only the files needed for the task.

## Failure Signals

Call out these signals explicitly:

- `cdopt` missing or imported from an unexpected path
- Torch/JAX/NumPy backend mismatch
- wrong manifold shape or dtype/device mismatch
- missing objective gradient only when the chosen template requires it
- infeasible or high feasibility residual
- large gradient norm or stationarity proxy after termination
- SciPy precision-loss status
- CDOpt `beta="auto"` warnings that affect logs but not correctness
- copied official example code that was not tied back to a reviewed model
- cross-method claims made with different data, seeds, stopping criteria, budgets, or metrics
- conclusions that rely on console snippets or chat memory instead of saved artifacts

## Resources

- `references/INDEX.md`: navigation for local cards, official pairs, templates, comparison protocols, and adapted-code review checks.
- `references/problem-descriptions/`: local CDOpt Problem Description cards.
- `references/example_prompts.md`: ready-to-paste `$cdopt-optimization` prompts for each card and template family.
- `references/few_shots/cdopt_official_pairs.md`: official problem-code pairs, read only for the matched example.
- `references/cdopt_official_examples.md`: implementation template notes after model review.
- `scripts/check_cdopt_environment.py`: safe dependency and path probe.
- `scripts/write_stiefel_dictionary_runner.py`: writes a tiny deterministic CPU Stiefel dictionary-learning runner.
- `scripts/write_constrained_layer_runner.py`: writes a tiny deterministic CPU PyTorch Stiefel-constrained-layer training runner.
- `scripts/write_constrained_rnn_runner.py`: writes a tiny deterministic CPU PyTorch RNN/LSTM constrained training runner.
