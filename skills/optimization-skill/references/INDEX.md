# Optimization Skill Reference Index

Use this index to choose the smallest reference set needed for the current optimization task.

## Core Modeling References

- `modeling_pipeline.md`: read when the input is natural language, LaTeX, a paper excerpt, source code, data notes, README instructions, or an official example Problem Description rather than a confirmed structured spec.
- `problem_type_taxonomy.md`: read when classifying LP, MILP, QP, SOCP, SDP, NLP, least squares, conic, manifold, neural-network constrained, or repository-native problems.
- `problem_schema.md`: read before accepting, generating, or editing a structured `problem.yaml`.

## Solver Selection References

- `solver_catalog.md`: read when choosing a solver ecosystem across CVXPY, Pyomo, SciPy/HiGHS, SDPT3, CVX, YALMIP, MOSEK, Gurobi, IPOPT, CasADi, CDOpt, Manopt, Pymanopt, Geoopt, and repository-native routes.
- `solver_selection_rules.md`: read when multiple solver routes are plausible and the agent must rank them by model fidelity, environment risk, licensing, codegen support, and evidence quality.

## Implementation Template References

- `implementation_templates.md`: read after model review when adapting CVXPY, Pyomo, SciPy, SDPT3, CDOpt, or repository-native solver code.
- `code_generation_patterns.md`: read before using helper code generation scripts or adding generated entrypoints.
- `evaluation_reporting.md`: read after a run, failed run, or solver-status ambiguity.

## Auxiliary Example Materials

- `cdopt_official_examples.md`: local CDOpt Problem Description card map and CDOpt implementation-template notes. These examples are auxiliary modeling and implementation materials, not the center of the Skill.
- `optskills/SOURCE.md`: source, license, and imported OptSkills reference scope.
- `optskills/skill_library/`: imported OptSkills archetype libraries used for pattern recognition.
- `../../examples/lp-milp-example-prompts.md` and `../../examples/lp-milp-example-prompts.zh-CN.md`: classic LP/MILP few-shot prompts.
- `../../examples/lp-milp-problem-specs.md`: schema-compatible LP/MILP few-shot specs.

## Default Path

1. Read the user's concrete problem first.
2. Create a modeling checkpoint before executable code.
3. Confirm or revise the model with the human.
4. Normalize the confirmed model into `problem.yaml`.
5. Choose a solver route from the catalog and selection rules.
6. Use templates only after the route is reviewed.
7. Run only after approval.
8. Interpret numerical evidence with source logs and solver status.

## Do Not

- Do not treat examples, solver documentation, or templates as confirmed math.
- Do not use a solver route just because code generation exists.
- Do not install solvers, download data, compile native extensions, or run generated code without approval.
- Do not hide infeasibility, weak certificates, bad scaling, integrality gaps, or ambiguous termination codes.
