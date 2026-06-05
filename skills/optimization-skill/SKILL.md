---
name: optimization-skill
description: Use when Codex must understand, model, solve, reproduce, route, execute, parse, or diagnose mathematical optimization problems from natural language, LaTeX, papers, code, data, or structured specs across OptSkills archetypes, SDPT3, CDOpt, MATLAB/Octave, Python, conic, semidefinite, nonlinear, MILP, or manifold workflows.
---

# Optimization Skill

This Skill is the single public entry point for optimization work. It covers problem intake, OptSkills-assisted archetype matching, mathematical modeling checkpoints, structured specs, solver route selection, approval-gated execution, result parsing, and failure diagnosis.

## Operating Principle

Keep four layers separate and reviewable:

1. **Archetype:** which known optimization pattern appears to match the user's problem.
2. **Math model:** variables, objective, constraints, dimensions, data, and ambiguities.
3. **Solver route:** which backend is appropriate and why.
4. **Evidence report:** what the approved run actually returned.

Never let a generated model, solver route, or natural-language interpretation outrun human review.

## Interactive Opening

### First Response Contract

At the start of a new interactive session, if the user has not already chosen a language, the entire first response must be one short language question.

Use this shape:

```text
Would you like to work in Chinese or English?
```

Do not say the Skill has been loaded.
Do not list accepted input types.
Do not ask what optimization problem the user is working on yet.
Do not mention solvers, archetypes, problem.yaml, or execution plans.
Do not include bullets, examples, or a capability summary in the first response.

After the user chooses the interaction language, ask the user to send the concrete optimization problem directly. It can be prose, formulas, a paper excerpt, code, data notes, or a mixed bundle.

Do not start with a questionnaire about input type, target, solver, or workflow mode. The user often has one concrete problem in hand. Read it first, infer whether the task is modeling, solving, reproduction, or failure diagnosis, then ask only the follow-up questions needed for a correct model.

Second-turn guidance after language is confirmed:

```text
Send the concrete optimization problem directly. It can be prose, formulas, a paper excerpt, code, or data notes. I will read it first and guide the modeling from there.
```

## Input Modes

Accept these inputs and route them through the same modeling checkpoint:

- natural-language optimization problem statements
- LaTeX objective and constraints
- paper excerpts or theorem/proposition statements
- README solver instructions
- source code with embedded optimization models
- `.mat`, `.npz`, `.json`, `.yaml`, or CSV data
- structured problem specs using `references/problem_schema.md`

When the input is not already structured, write `modeling_checkpoint.md` content before execution: archetype match, variables, objective, constraints, dimensions, data sources, candidate solver routes, and unresolved ambiguities.

## Reference Navigation

Start with `references/INDEX.md` for routing.

Use the imported OptSkills corpus as reference material, not as an automatically confirmed model:

- `references/optskills/SOURCE.md`: source, license, and imported library scope.
- `references/optskills/skill_library/`: imported released libraries:
  - `skill_library_cluster`
  - `skill_library_learned`
  - `skill_library_nanoco_learned`
- `scripts/search_archetypes.py`: optional helper for local keyword search over the imported OptSkills indexes and markdown files.

The primary navigation method is agent judgment: inspect the user goal, use `rg`, read relevant `index.json` files, open candidate markdown references, compare modeling assumptions, and choose the best archetype. The search script is only an optional helper when the corpus is large or the first `rg` pass is noisy:

```bash
python skills/optimization-skill/scripts/search_archetypes.py --query "<problem statement>" --limit 5
```

Never treat the script ranking as authoritative. It can suggest candidates, but the coding agent must still read and judge the actual reference files against the user's problem.

## Workflow

1. Confirm interaction language for a new interactive session, then let the user provide the concrete problem.
2. Classify the input type and problem class.
3. If the input is not a confirmed structured spec, read `references/modeling_pipeline.md` and relevant OptSkills references.
4. Create a compact modeling checkpoint with source evidence and an ambiguity list.
5. Ask the human to confirm, revise, reject, or skip the interpreted model before executable solver code or final conclusions.
6. Normalize the confirmed model into `problem.yaml` using `references/problem_schema.md`.
7. Read `references/solver_catalog.md` and choose a solver route.
8. If the selected route is CDOpt, run or propose the post-install manifold smoke test before any CDOpt problem solve. Use `/Users/conanxu/cdopt_manifold_tests/run_all_notebooks.py` when that test suite exists; record the command, CDOpt version/path, pass/fail status, and any dependency/API failure. Treat this as an installation/API preflight, not as an application benchmark.
9. Route the structured problem:

```bash
conda run -n ai4math python skills/optimization-skill/scripts/solver_router.py --spec <problem.yaml>
```

10. Read `references/code_generation_patterns.md` and generate an entrypoint when appropriate:

```bash
conda run -n ai4math python skills/optimization-skill/scripts/codegen.py --spec <problem.yaml> --out outputs/{run_id}/generated
```

11. Put the exact command, risks, timeout, expected outputs, dependencies, and any CDOpt preflight result into a review plan.
12. Run only approved commands.
13. Parse logs and evidence:

```bash
conda run -n ai4math python skills/optimization-skill/scripts/result_parser.py --log outputs/{run_id}/logs/run.log --out outputs/{run_id}/results/solver_summary.json
```

14. Read `references/evaluation_reporting.md` and summarize status, objective values, feasibility, residuals, certificates, numerical warnings, and next choices.

## Solver Routes

- **SDPT3:** direct SQLP data (`blk`, `At`, `C`, `b`), semidefinite programs, SOCP/SDP/LP cone models, MATLAB/Octave execution.
- **CDOpt:** Riemannian and manifold-constrained models, orthogonality constraints, constraint dissolving, Python backend workflows.
- **Modeling layers:** CVX, YALMIP, CVXPY, JuMP, and Pyomo when the source already uses them or a modeling adapter is approved.
- **Existing solver route:** repository-native solvers when they are the safest way to reproduce the original experiment.
- **Future backend route:** add solvers by extending `solver_catalog.md`, `problem_schema.md`, `solver_router.py`, `codegen.py`, and parser patterns together.

Current generated support is concrete but intentionally bounded:

- SDPT3 generation expects confirmed direct SQLP data in a `.mat` file and produces a MATLAB/Octave wrapper.
- CDOpt generation expects a confirmed manifold type, shape, backend, objective module/function, beta, and SciPy optimizer options. It produces a Python wrapper that constructs the manifold, builds `cdopt.core.problem`, runs SciPy `optimize.minimize`, and writes a JSON result summary.
- CDOpt execution should be preceded by the post-install manifold smoke test when available. The local suite at `/Users/conanxu/cdopt_manifold_tests` checks PyPI `cdopt==0.5.5`, manifold constructors, CDF gradient generation, finite-difference agreement, feasibility reporting, and a tiny L-BFGS-B path.
- Natural-language or LaTeX-only models require a modeling checkpoint before executable SDPT3/CDOpt code is generated.

## Approval Rules

Ask before:

- running generated or repository solver code
- running the CDOpt post-install smoke test, unless the user has already approved CDOpt validation in the current task
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
