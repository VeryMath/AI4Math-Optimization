# CDOpt Optimization

Chinese guide: [README.zh-CN.md](README.zh-CN.md)

`cdopt-optimization` is an evidence-first agent workflow layer for
[CDOpt](https://github.com/cdopt) and manifold-constrained optimization. It
turns a general coding agent into a CDOpt-aware research assistant that can
model optimization problems, inspect the numerical stack, adapt official
examples, run controlled validation, and report only from durable artifacts.

The goal is not to make an agent "run an optimizer." The goal is to make it
behave like a careful computational mathematics collaborator: model first,
ask before executing, preserve evidence, and separate numerical experiments
from numerical conclusions.

## AI4Math Role

This skill is the CDOpt-specific optimization adapter in the AI4Math stack. Use
it when the mathematical object is a manifold-constrained optimization problem
or when a CDOpt official example, backend, or validation run is the right
research instrument.

## Handoff

Upstream handoffs may come from `optimization-modeling`, `paper-to-skill`,
`discover-math-problems`, or a scientific reproduction run that identifies a
manifold optimization subproblem. The handoff should include the reviewed model,
manifold type and shape, backend choice, data dimensions, and comparison
question. Return solver summaries, generated runners, logs, and limitations to
the broader optimization or reproduction workflow.
When a CDOpt task has a stable metric, evaluator, and budget, it can hand off to
`openevolve-experiment-workflow` for bounded search. Treat the result as search or
numerical evidence, not proof.

## Installation / Loading

Use the repository checkout first. Ask your coding agent to read:

```text
AGENTS.md
SKILL.md
cdopt-optimization/SKILL.md
```

If your agent supports local Skill discovery, install or link `cdopt-optimization/`
into that agent's Skill path and reload the agent if needed. Platform notes live
in `CLAUDE.md`, `GEMINI.md`, `.codex/INSTALL.md`, and `.opencode/INSTALL.md`.

Remote install prompt:

```text
Please install `cdopt-optimization` from https://github.com/VeryMath/AI4Math-Optimization into your own skill system.

Use the local checkout if it already exists; otherwise clone the repository. Detect where your environment stores skills, install or link the cdopt-optimization folder there, update any registry or config if needed, reload or restart if required, and verify that $cdopt-optimization is discoverable.
```

## Quick Start

```text
Use this repository's CDOpt workflow.

Read:
- AGENTS.md
- SKILL.md
- cdopt-optimization/SKILL.md

Goal:
<describe the manifold-constrained optimization task>

Constraints:
- create a modeling checkpoint first;
- ask before installs, solver runs, comparison expansion, or final claims.
```

## Why CDOpt Optimization

Manifold optimization workflows are easy to get almost right. A solver script
can run while the manifold shape is wrong, the backend is mismatched, the
gradient is not the one implied by the model, or two methods are compared under
different seeds and stopping rules. `cdopt-optimization` gives coding agents a compact
protocol for avoiding those failures.

It provides:

- **Model discipline** - variables, domains, manifolds, objectives, constraints,
  dimensions, backend choices, and solver routes are reviewed before code.
- **Execution gates** - package installation, solver runs, smoke tests,
  comparison experiments, environment changes, and final mathematical claims
  require explicit approval.
- **Evidence-backed reporting** - results are summarized from JSON files, logs,
  and run summaries rather than from transient console output or chat memory.
- **Official-example coverage** - local problem cards, implementation templates,
  and tiny CPU runners cover the major CDOpt example families.
- **Reproducibility scaffolding** - deterministic synthetic runners, smoke-test
  routing, comparison plans, and summary artifacts make experiments inspectable.

If a task is not genuinely about CDOpt, Riemannian optimization, or
manifold-constrained modeling, the skill is designed to say so and route the
agent toward a broader optimization workflow instead of forcing CDOpt where it
does not belong.

## Evidence-First Workflow

`cdopt-optimization` starts each task by creating a dedicated workspace under
`outputs/{run_id}/`. Modeling checkpoints, generated code, logs, JSON results,
comparison tables, and final summaries for that task stay inside this
workspace, so evidence is not scattered across the repository.

```text
outputs/{run_id}/
├── modeling_checkpoint.md
├── plan.md
├── generated/
├── logs/
├── results/
└── RUN_SUMMARY.md
```

Inside that workspace, agent behavior is organized around three review layers:

| Layer | Artifact | Purpose |
| --- | --- | --- |
| Model review | `modeling_checkpoint.md` | Verify manifold type, dimensions, objective, constraints, backend, solver route, and ambiguities before executable code. |
| Execution review | approval gates | Prevent unapproved installs, solver runs, environment changes, comparison expansion, or unsupported numerical conclusions. |
| Result review | `solver_summary.json`, `RUN_SUMMARY.md`, `COMPARISON_SUMMARY.md` | Report from saved artifacts with status, objective, feasibility, stationarity proxy, timing, package versions, and limitations. |

For method selection or publication-style evidence, the same workspace adds a
comparison gate:

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

Comparison experiments are intentionally opt-in. Single-method validation and
smoke tests stay lightweight.

## Core Capabilities

- **Package validation** - safely checks whether CDOpt and key numerical
  dependencies are importable, where they are loaded from, and whether a local
  smoke-test suite is available.
- **Smoke testing** - routes agents toward the local CDOpt manifold notebook
  suite or tiny CPU-only validation runs after approval.
- **Problem modeling** - turns natural-language tasks, LaTeX, paper excerpts,
  source code, or local Problem Description cards into a reviewed CDOpt model.
- **Code adaptation** - studies official CDOpt examples, then adapts them only
  after the model has been reviewed.
- **Failure diagnosis** - highlights dependency errors, API mismatches,
  backend/device/dtype issues, infeasibility, stationarity warnings, and solver
  termination concerns.
- **Comparison reporting** - supports solver, backend, or baseline comparisons
  through an approved `comparison_plan.md` and saved method-level evidence.

## Official Example Coverage

The official [CDOpt examples](https://cdopt.github.io/examples/) are covered at
different depths depending on how much local scaffolding is useful.

| Official category | What this repository provides | Depth |
| --- | --- | --- |
| **Optimization via SciPy** | Problem Description cards, official problem-code pairs, implementation templates, and a tiny CPU runner generator | Full workflow |
| **NN training via PyTorch** | Cards for LeNet, single-layer RNN, and bidirectional LSTM; constrained-layer and sequence-model templates; tiny CPU runner generators | Cards + runners for LeNet/RNN/LSTM, template-level for larger examples |
| **NN training via JAX/FLAX** | LeNet orthogonal-kernel card and JAX/Flax constrained-layer template | Modeling card + template |

Supported families include Stiefel/Torch/SciPy dictionary learning,
Stiefel/JAX/JIT dictionary learning, NumPy Stiefel examples with manual
derivatives, oblique nearest-correlation estimation, sphere-constrained
Bose-Einstein condensates, symplectic-Stiefel eigenvalue problems, and CDOpt
neural-network constrained layers such as `Conv2d_cdopt`, `Linear_cdopt`,
`RNN_cdopt`, `Conv_cdopt`, and `Dense_cdopt`.

Distributed PyTorch examples require a separate run plan, resource estimate, and
approval. They are not treated as smoke tests.

## Start A CDOpt Session

After installation, open a fresh chat and paste:

```text
Use $cdopt-optimization.
```

The skill first asks only for the interaction language:

```text
Would you like to work in Chinese or English?
```

After choosing a language, send the actual CDOpt task. Natural language, LaTeX,
paper excerpts, source code, a local Problem Description card, a dependency
check, or a request for a comparison plan are all valid starting points.

## How To Interact

Use a checkpoint loop:

```text
task -> model review -> plan -> approve / revise / reject / skip
     -> approved run or comparison -> evidence summary -> next checkpoint
```

Use `approve` to run a proposed step, `revise` to update the model or plan,
`reject` to stop the path, and `skip` to move past a phase. The agent should ask
before installs, solver runs, comparison expansion, source edits, or final
mathematical/numerical claims.

## Repository Layout

```text
cdopt-optimization/
├── SKILL.md                              # Skill instructions
├── agents/openai.yaml                    # agent interface metadata
├── references/
│   ├── INDEX.md                          # progressive-disclosure navigation
│   ├── example_prompts.md                # ready-to-paste $cdopt-optimization prompts
│   ├── cdopt_official_examples.md        # implementation templates
│   ├── few_shots/cdopt_official_pairs.md # official problem-code pairs
│   └── problem-descriptions/             # local Problem Description cards
└── scripts/
    ├── check_cdopt_environment.py         # safe dependency / path probe
    ├── write_stiefel_dictionary_runner.py # tiny SciPy-optimization runner
    ├── write_constrained_layer_runner.py  # tiny PyTorch constrained-layer runner
    └── write_constrained_rnn_runner.py    # tiny PyTorch RNN/LSTM runner
```

## Maintainer Quick Start

```bash
# Safe dependency probe: no install, no solver run
python3 cdopt-optimization/scripts/check_cdopt_environment.py --json

# Generate the tiny deterministic Stiefel dictionary-learning runner
python3 cdopt-optimization/scripts/write_stiefel_dictionary_runner.py \
  --output-dir .local/cdopt-runs/dictionary_learning_torch_scipy

# Generate the tiny PyTorch constrained-layer training runner
python3 cdopt-optimization/scripts/write_constrained_layer_runner.py \
  --output-dir .local/cdopt-runs/constrained_layer_torch

# Generate the tiny PyTorch RNN/LSTM training runner
python3 cdopt-optimization/scripts/write_constrained_rnn_runner.py \
  --output-dir .local/cdopt-runs/constrained_rnn_torch
```

The optional post-install manifold smoke test is resolved from the
`CDOPT_SMOKE_TEST` environment variable, the `smoke_test.path` field reported by
`check_cdopt_environment.py`, or the default
`~/cdopt_manifold_tests/run_all_notebooks.py`.

## Acknowledgments

- [CDOpt](https://github.com/cdopt) and its official examples
  (<https://cdopt.github.io/examples/>), which provide the source problem
  statements, code pairs, and implementation patterns studied here.

Reference problem statements and code snippets are kept as provenance for
modeling and adaptation. Study them first, tie implementation choices back to a
reviewed model, and do not copy official example code verbatim.

## License

Released under the [MIT License](LICENSE).
