# AI4Math Optimization

AI4Math Optimization collects Skill-as-adapter packages for mathematical
optimization modeling, solver use, and optimization workflow support.

## Skill Packages

| Package | Purpose | Entry point |
| --- | --- | --- |
| `skills/copt-linear-program/` | COPT linear programming workflow with scripts and references. | `SKILL.md`, `readme.md` |

## Legacy Root Packages

Existing root-level packages such as `LP-Skill/`, `MIP-Skill/`,
`SOCP-Skill/`, and `OR_SOLVER-Skill/` are preserved as legacy material. New
imports should use the `skills/<skill-name>/` layout.

## Usage

Open the package you need, read its README and `SKILL.md`, then ask your coding
agent to follow the workflow. Keep solver examples, scripts, and references
inside the package directory.
