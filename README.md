<div align="center">

# AI4Math · Optimization

Skill packages for mathematical optimization modeling, solver setup, LP/MIP/SOCP
workflows, and manifold-constrained optimization.

[中文说明](README.zh-CN.md) · [Skill packages](#skill-packages) · [Quick start](#quick-start) · [Security model](#security-and-scope)

![version](https://img.shields.io/badge/version-0.1.0-blue)
![skills](https://img.shields.io/badge/skills-6-2ea44f)
![license](https://img.shields.io/badge/license-MIT-green)

</div>

## What This Repository Is

This repository is the AI4Math home for optimization skills. It collects
packages for modeling mathematical programs, selecting solvers, checking solver
environments, adapting examples, and reporting evidence from optimization runs.

Use the root page as the public map. For concrete modeling or solving, open the
package that matches the problem class.

## Skill Packages

| Package | Use it for | Start here |
| --- | --- | --- |
| [`cdopt-optimization`](skills/cdopt-optimization/) | CDOpt and manifold-constrained optimization modeling, validation, runner generation, and evidence reports. | [`README`](skills/cdopt-optimization/README.md) · [`SKILL`](skills/cdopt-optimization/SKILL.md) |
| [`copt-linear-program`](skills/copt-linear-program/) | COPT/coptpy linear-programming workflows, word-problem restatement, and solver scripts. | [`README`](skills/copt-linear-program/readme.md) · [`SKILL`](skills/copt-linear-program/SKILL.md) |
| [`linear-programming`](skills/linear-programming/) | General LP modeling, solver selection, and natural-language-to-model workflows. | [`README`](skills/linear-programming/README.md) · [`SKILL`](skills/linear-programming/SKILL.md) |
| [`mixed-integer-programming`](skills/mixed-integer-programming/) | MILP/MIP modeling with binary, integer, and continuous decision variables. | [`README`](skills/mixed-integer-programming/README.md) · [`SKILL`](skills/mixed-integer-programming/SKILL.md) |
| [`second-order-cone-programming`](skills/second-order-cone-programming/) | SOCP modeling and cvxpy-based conic solver workflows. | [`README`](skills/second-order-cone-programming/README.md) · [`SKILL`](skills/second-order-cone-programming/SKILL.md) |
| [`or-solver`](skills/or-solver/) | Shared solver detection, installation planning, license checks, and solver selection for OR skills. | [`README`](skills/or-solver/README.md) · [`SKILL`](skills/or-solver/SKILL.md) |

## Quick Start

Clone the repository and choose a package:

```bash
git clone https://github.com/VeryMath/AI4Math-Optimization.git
cd AI4Math-Optimization
```

For solver setup and selection, start with:

```text
skills/or-solver/SKILL.md
```

For general LP/MIP/SOCP modeling, start with the matching package under
`skills/`. For CDOpt or manifold-constrained tasks, start with:

```text
skills/cdopt-optimization/SKILL.md
```

## Repository Layout

```text
AI4Math-Optimization/
├── README.md
├── README.zh-CN.md
├── SKILL.md
└── skills/
    ├── cdopt-optimization/
    ├── copt-linear-program/
    ├── linear-programming/
    ├── mixed-integer-programming/
    ├── or-solver/
    └── second-order-cone-programming/
```

Keep solver examples, scripts, references, and generated run evidence inside
the package that owns them.

## Validation

There is no root build step. When changing a package, validate its `SKILL.md`,
README links, scripts, and package-local examples. If you use Codex's local
skill validator, run it against every changed standard skill package.

## Security and Scope

Do not commit solver licenses, API keys, private datasets, `.env` files,
generated solver logs with sensitive data, or local run outputs. Public examples
should include source notes for benchmark data and be safe to redistribute.
