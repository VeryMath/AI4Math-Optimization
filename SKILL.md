---
name: ai4math-optimization
description: Route AI4Math optimization tasks to the appropriate bundled skill package.
---

# AI4Math Optimization

Use this repository as a routing layer for optimization workflows.

## Packages

- `skills/cdopt-optimization/`: CDOpt and manifold-constrained optimization
  modeling, validation, and runner generation. Read `SKILL.md`, README,
  references, and scripts before use.
- `skills/copt-linear-program/`: COPT linear programming workflow. Read
  `SKILL.md`, `readme.md`, `reference/`, and `scripts/` before use.
- `skills/linear-programming/`: general LP modeling and solver selection.
- `skills/mixed-integer-programming/`: MIP and MILP modeling workflows.
- `skills/second-order-cone-programming/`: SOCP modeling and solver workflows.
- `skills/or-solver/`: shared optimization solver setup and selection.
- `skills/osqp-solver/`: continuous convex QP modeling, OSQP execution,
  status gates, and independent solution or infeasibility-certificate checks.
- `skills/optskills/`: standalone selection and use of released OptSkills
  problem-archetype cards. Read its `SKILL.md`, combined
  `skill_library/index.json`, and selected card files. It does not depend on
  sibling skill packages.

Prefer package-local instructions over this router when running a concrete
workflow.
