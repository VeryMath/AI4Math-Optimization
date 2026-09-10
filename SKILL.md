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
- `skills/mixed-integer-programming/`: MIP and MILP modeling workflows.
- `skills/second-order-cone-programming/`: SOCP modeling and solver workflows.
- `skills/or-solver/`: environment setup and troubleshooting for a solver
  already specified by the user or modeling task.
- `skills/osqp-solver/`: continuous convex QP modeling, OSQP execution,
  status gates, and independent solution or infeasibility-certificate checks.
- `skills/optskills/`: natural-language operations-research and LP modeling
  through released OptSkills problem-archetype cards. Read its `SKILL.md`,
  combined `skill_library/index.json`, and selected card files. Modeling is
  self-contained; choose the solver here and use `or-solver` if that target
  needs environment setup.

Prefer package-local instructions over this router when running a concrete
workflow.
