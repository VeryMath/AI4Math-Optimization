# AI4Math Optimization Skill

English | [简体中文](README.zh-CN.md)

`optimization-skill` is a coding-agent Skill for mathematical optimization work. It helps an agent read a concrete problem, build a reviewed model, match OptSkills references, choose a solver route, generate approved solver entrypoints, parse evidence, and diagnose failures.

The intended user workflow is simple: ask your coding agent to install the Skill, then ask it to use the Skill on your optimization problem. The agent should do the environment-specific work.

## 1. Ask Your Coding Agent To Install It

Paste this into your coding agent:

```text
Please install the optimization-skill from https://github.com/VeryMath/AI4Math-Optimization into your own skill system.

Use the local checkout if it already exists; otherwise clone the repository. Detect where your environment stores skills, install or link skills/optimization-skill there, update any registry or config if needed, reload or restart if required, and verify that $optimization-skill is discoverable.
```

The agent should figure out whether it needs a user skill directory, a project skill directory, a symlink, a copied folder, or a config entry. You should not need to know its internal skill path.

## 2. Start An Optimization Session

After installation, open a fresh chat and paste:

```text
Use $optimization-skill.
```

The Skill should first ask only for the interaction language:

```text
Would you like to work in Chinese or English?
```

After choosing a language, send the actual optimization problem directly. Natural language, LaTeX, paper excerpts, source code, README instructions, data descriptions, `.mat`/`.npz`/`.json`/`.yaml`/CSV files, or an existing `problem.yaml` are all acceptable.

The agent should then model the problem, expose ambiguities, ask for confirmation, propose a solver route, and run code only after approval.

## CDOpt Workflow

For CDOpt tasks, there are two separate checks:

1. Installation/API validation: run or propose the post-install manifold smoke test.

```bash
cd /Users/conanxu/cdopt_manifold_tests
python run_all_notebooks.py
```

2. Application examples: after the smoke test passes, use the copyable prompts in [examples/cdopt-example-prompts.md](examples/cdopt-example-prompts.md) or [examples/cdopt-example-prompts.zh-CN.md](examples/cdopt-example-prompts.zh-CN.md).

The smoke test only validates the CDOpt runtime and core APIs. It is not evidence that an application model is mathematically correct.

## About The Skill

`optimization-skill` is designed as one public entry point for optimization work. The user gives a concrete problem; the agent is responsible for turning it into a reviewable workflow.

The Skill guides the agent to:

- read the problem before asking broad setup questions
- identify variables, objective, constraints, dimensions, data, and ambiguities
- compare the problem with imported OptSkills references when useful
- create a modeling checkpoint before executable solver code
- route confirmed models to solver ecosystems such as SDPT3, CDOpt, or repository-native methods
- generate bounded entrypoints and run them only after approval
- report objective values, feasibility, solver status, numerical warnings, and failure causes

The Skill is not a solver by itself. It is a workflow layer that helps a coding agent use solvers carefully, with model review and execution approval kept visible.

## Maintainer Checks

From this repository:

```bash
python /Users/conanxu/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/optimization-skill
python -m pytest -q
```

Skill instructions live in [skills/optimization-skill/SKILL.md](skills/optimization-skill/SKILL.md). Solver-routing details live under `skills/optimization-skill/references/`.
