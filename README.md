# Optimization Modeling

Chinese guide: [README.zh-CN.md](README.zh-CN.md)

`optimization-modeling` helps a coding agent turn an optimization problem into a reviewed mathematical model before solver execution.

## When To Use It

Use this skill when the input is:

- prose, LaTeX, paper snippets, data, source code, solver errors, or an existing model;
- an optimization task that needs variables, objective, constraints, dimensions, and ambiguity checks;
- a problem that needs classification before choosing a solver ecosystem;
- a numerical result that needs feasibility, objective, warning, or failure interpretation.

## What It Produces

The agent should produce modeling checkpoints, solver routes, bounded solver code or commands, run logs, feasibility/objective reports, and failure diagnostics.

## Installation

Copy this to your coding agent:

```text
Please install the `optimization-modeling` skill from https://github.com/VeryMath/AI4Math-Optimization.git (branch: kn-Xu). Read `.agent.md`, install the declared Skill entrypoint, verify that `$optimization-modeling` is discoverable, and tell me whether I need to restart the agent.
```

If you already have this skill repository locally, replace the repository URL
with the local folder path. The coding agent should handle cloning, linking,
configuration, reload/restart checks, and verification.

## Quick Start

```text
Use this repository's optimization workflow.

Read:
- AGENTS.md
- SKILL.md
- skills/optimization-modeling/SKILL.md

Goal:
<describe the optimization model, solver task, or numerical issue>

Constraints:
- inspect the problem first;
- build a modeling checkpoint;
- ask before solver runs, source edits, dependency changes, or final claims.
```

## Start An Optimization Session

After installation, open a fresh chat and paste:

```text
Use $optimization-modeling.
```

The Skill should first ask only for the interaction language:

```text
Would you like to work in Chinese or English?
```

After choosing a language, send the actual optimization problem directly. Natural language, LaTeX, paper excerpts, source code, README instructions, data descriptions, `.mat`/`.npz`/`.json`/`.yaml`/CSV files, or an existing `problem.yaml` are all acceptable.

The agent should then model the problem, expose ambiguities, ask for confirmation, propose a solver route, and run code only after approval. Examples, solver docs, and code templates are auxiliary materials; the model and solver route remain the main workflow.

## How To Interact

Use a checkpoint loop:

```text
problem -> model checkpoint -> solver route -> approve / revise / reject / skip
        -> approved run -> evidence summary -> next checkpoint
```

Use `approve` to run a proposed step, `revise` to update the model or route,
`reject` to stop the path, and `skip` to move past a phase. The agent should ask
before installs, solver execution, source edits, long runs, or final
mathematical/numerical claims.

## About The Skill

`optimization-modeling` is designed as one public entry point for optimization work. The user gives a concrete problem; the agent is responsible for turning it into a reviewable model, selecting an appropriate solver ecosystem, and explaining the numerical evidence.

The Skill guides the agent to:

- read the problem before asking broad setup questions
- identify variables, objective, constraints, dimensions, data, and ambiguities
- compare the problem with imported OptSkills references when useful
- create a modeling checkpoint before executable solver code
- classify problem types such as LP, MILP, QP, SOCP, SDP, NLP, least squares, and manifold optimization
- route confirmed models to solver ecosystems such as CVXPY, Pyomo, SciPy/HiGHS, SDPT3, CVX, YALMIP, IPOPT, CasADi, Manopt, Pymanopt, Geoopt, commercial solvers, or repository-native methods
- generate or adapt bounded entrypoints and run them only after approval
- report objective values, feasibility, solver status, numerical warnings, and failure causes

The Skill is not a solver by itself. It is a workflow layer that helps a coding agent use solvers carefully, with model review and execution approval kept visible.

## Example Materials

The examples are optional supporting material for testing and few-shot guidance. They are not the main workflow. The main workflow is still: understand the user's problem, build a reviewed model, choose a solver route, and run only after approval.

- Classic LP/MILP examples: [examples/lp-milp-example-prompts.md](examples/lp-milp-example-prompts.md) and [examples/lp-milp-example-prompts.zh-CN.md](examples/lp-milp-example-prompts.zh-CN.md) cover transportation LP, assignment MILP, set cover, facility location, network flow, scheduling, and natural-language-to-spec conversion. The companion [examples/lp-milp-problem-specs.md](examples/lp-milp-problem-specs.md) shows schema-compatible `problem.yaml` drafts.

## Maintainer Checks

From this repository:

```bash
python <path-to-skill-validator>/quick_validate.py skills/optimization-modeling
python -m pytest -q
```

Skill instructions live in [skills/optimization-modeling/SKILL.md](skills/optimization-modeling/SKILL.md). Solver-routing details live under `skills/optimization-modeling/references/`.
