---
name: optimization-solver-skill
description: Use when a coding agent must understand, model, route, execute, parse, or diagnose mathematical optimization problems across natural-language, LaTeX, structured specs, SDPT3, CDOpt, MATLAB/Octave, Python, conic, semidefinite, nonlinear, or manifold solver workflows.
---

# Optimization Solver Skill

This Skill turns optimization work into an inspectable agent workflow. It covers problem understanding, model normalization, solver routing, entrypoint generation, approval-gated execution, result parsing, and failure diagnosis.

Use it directly for solver-focused tasks, or as a specialist inside a broader computational-math reproduction workflow.

## Operating Principle

Separate the math, the solver, and the execution environment:

1. **Math model:** what problem is being solved.
2. **Solver route:** which backend is appropriate and why.
3. **Execution plan:** what command will run, with what dependencies and risks.
4. **Evidence report:** what the solver actually returned.

Never let generated code or a natural-language interpretation outrun human review.

## Input Modes

Accept these inputs and route them through the same model checkpoint:

- natural-language optimization problem statements
- LaTeX objective and constraints
- paper excerpts or theorem/proposition statements
- README solver instructions
- source code with embedded optimization models
- `.mat`, `.npz`, `.json`, `.yaml`, or CSV data
- structured problem specs using `references/problem_schema.md`

When the input is not already structured, write a modeling checkpoint: objective, variables, constraints, dimensions, data sources, solver assumptions, and unresolved ambiguity. Ask the human to confirm before generating executable solver code.

## Standard Workflow

1. Read `references/INDEX.md`.
2. Classify the input type and problem class.
3. If needed, read `references/modeling_pipeline.md` and create a modeling checkpoint.
4. Normalize the problem into `references/problem_schema.md`.
5. Read `references/solver_catalog.md` and choose a solver route.
6. Route the structured problem:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/solver_router.py --spec <problem.yaml>
```

7. Read `references/code_generation_patterns.md` and generate an entrypoint when appropriate:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/codegen.py --spec <problem.yaml> --out outputs/{run_id}/generated
```

8. Put the exact command, risks, timeout, expected outputs, and dependencies into a review plan.
9. Ask the human for `approve`, `revise`, `reject`, or `skip`.
10. Run only approved commands.
11. Parse logs and evidence:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/result_parser.py --log outputs/{run_id}/logs/run.log --out outputs/{run_id}/results/solver_summary.json
```

12. Read `references/evaluation_reporting.md` and summarize status, objective values, feasibility, residuals, certificates, numerical warnings, and next choices.

## Solver Routes

- **SDPT3:** direct SQLP data (`blk`, `At`, `C`, `b`), semidefinite programs, SOCP/SDP/LP cone models, MATLAB/Octave execution.
- **CDOpt:** Riemannian and manifold-constrained models, orthogonality constraints, constraint dissolving, Python backend workflows.
- **Modeling layers:** CVX, YALMIP, CVXPY, JuMP, and Pyomo when the source already uses them or a modeling adapter is approved.
- **Existing solver route:** repository-native solvers when they are the safest way to reproduce the original experiment.
- **Future backend route:** add solvers by extending `solver_catalog.md`, `problem_schema.md`, `solver_router.py`, `codegen.py`, and parser patterns together.

## Approval Rules

Ask before:

- running generated or repository solver code
- installing or upgrading solver packages
- compiling SDPT3/MEX/native extensions
- modifying MATLAB path, Python environment, or system solver configuration
- generating a modeling adapter from natural language or LaTeX
- editing source code or replacing data
- accepting final mathematical conclusions

## Failure Signals

Call out these signals explicitly:

- missing solver package, MATLAB/Octave path, MEX file, Python backend, or license
- malformed SQLP data (`blk`, `At`, `C`, `b`) or dimension mismatch
- infeasible, dual-infeasible, unbounded, or ambiguous certificates
- stalled complementarity gap, residuals, short steps, bad scaling, or factorization warnings
- CDOpt backend mismatch, missing manifold definition, missing objective module, or shape mismatch
- modeling ambiguity caused by natural-language or LaTeX interpretation

## Output Contract

Prefer this run layout when the agent needs durable evidence:

```text
outputs/{run_id}/
├── problem.yaml
├── modeling_checkpoint.md
├── plan.md
├── generated/
├── logs/run.log
├── results/solver_summary.json
├── figures/
├── repair_plan.md
└── RUN_SUMMARY.md
```

Only create the files that the task actually needs. Keep the conversation as the primary interface.

## References

- `references/INDEX.md`: what to read next.
- `references/problem_schema.md`: canonical problem spec.
- `references/modeling_pipeline.md`: natural-language, LaTeX, and source-to-model conversion.
- `references/solver_catalog.md`: solver backend guidance.
- `references/code_generation_patterns.md`: generated entrypoint conventions.
- `references/evaluation_reporting.md`: result interpretation and reporting.
