---
name: optimization-skill
description: Use when a coding agent must understand, model, solve, reproduce, route, execute, parse, or diagnose mathematical optimization problems from natural language, LaTeX, papers, code, data, or structured specs across OptSkills archetypes, SDPT3, CDOpt, MATLAB/Octave, Python, conic, semidefinite, nonlinear, MILP, or manifold workflows.
---

# Optimization Skill

This Skill is an **Optimization Modeling & Solver Orchestration** workflow.

It helps a coding agent turn a concrete optimization problem into a reviewed mathematical model, choose a suitable solver ecosystem, generate or adapt solver code when appropriate, run only after approval, and interpret numerical evidence.

## Positioning

Model first, solve second. The Skill's center is the mathematical model and solver route, not any single solver package.

CDOpt is a solver route, not the Skill's center of gravity. SDPT3, CVXPY, Pyomo, CVX, YALMIP, SciPy, HiGHS, Gurobi, MOSEK, IPOPT, Manopt, Pymanopt, Geoopt, and repository-native code are also routes when the model and environment make them appropriate.

OptSkills archetypes, local CDOpt Problem Description cards, LP/MILP few-shots, solver docs, and code templates are auxiliary materials. More precisely, examples, solver docs, and code templates are auxiliary materials for modeling, routing, implementation, and diagnosis.

## Operating Principle

Keep five layers separate and reviewable:

1. **Problem statement:** what the user or source actually says.
2. **Math model:** variables, domains, objective, constraints, dimensions, data, assumptions, and ambiguities.
3. **Problem type:** LP, MILP, QP, SOCP, SDP, NLP, least squares, conic, manifold, neural-network constrained, or repository-native.
4. **Solver route:** which solver ecosystem is appropriate and why.
5. **Evidence report:** what the approved run actually returned.

Never let a generated model, solver route, code template, or natural-language interpretation outrun human review.

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
- official example Problem Descriptions, preferably through local cards under `examples/cdopt/problem-descriptions/`
- README solver instructions
- source code with embedded optimization models
- `.mat`, `.npz`, `.json`, `.yaml`, or CSV data
- structured problem specs using `references/problem_schema.md`

When the input is not already structured, write `modeling_checkpoint.md` content before execution: source evidence, variables, domains, objective, constraints, dimensions, data sources, candidate problem types, candidate solver routes, and unresolved ambiguities.

## Reference Navigation

Start with `references/INDEX.md` for routing.

Use references through agent judgment:

- Core modeling references define how to turn inputs into a reviewable model and `problem.yaml`.
- Solver selection references define what ecosystems can solve which problem types.
- Implementation templates help after the model and route are reviewed.
- Auxiliary example materials help with pattern recognition and tests; they are not automatically confirmed models.

Important references:

- `references/modeling_pipeline.md`: read for unstructured inputs and modeling checkpoints.
- `references/problem_type_taxonomy.md`: read when classifying LP, MILP, QP, SOCP, SDP, NLP, least squares, conic, manifold, and repository-native problems.
- `references/problem_schema.md`: read before accepting, generating, or editing `problem.yaml`.
- `references/solver_catalog.md`: read when selecting solver ecosystems.
- `references/solver_selection_rules.md`: read when ranking multiple possible routes.
- `references/implementation_templates.md`: read before adapting CVXPY, Pyomo, SciPy, SDPT3, CDOpt, or repository-native code.
- `references/cdopt_official_examples.md`: read after a local CDOpt Problem Description card has been understood and model-reviewed.
- `references/optskills/SOURCE.md`: read when using imported OptSkills references for archetype matching.
- `scripts/search_archetypes.py`: optional helper for local keyword search over the imported OptSkills indexes and markdown files.
- `examples/lp-milp-example-prompts.md`, `examples/lp-milp-example-prompts.zh-CN.md`, and `examples/lp-milp-problem-specs.md`: few-shot references for classic LP/MILP modeling and future CVXPY/Pyomo adapter work.
- `examples/cdopt-example-prompts.md`, `examples/cdopt-example-prompts.zh-CN.md`, and `examples/cdopt/problem-descriptions/*.md`: local CDOpt Problem Description prompt cards for application-level modeling tests.

These `examples/` files are packaged inside the Skill so an installed coding agent can read them locally. The repository root also mirrors them under `examples/` for browsing and testing.

The primary navigation method is agent judgment: inspect the user goal, use `rg`, read relevant references, compare modeling assumptions, and choose the best route. The search script is only an optional helper when the corpus is large or the first `rg` pass is noisy:

```bash
python skills/optimization-skill/scripts/search_archetypes.py --query "<problem statement>" --limit 5
```

Never treat the script ranking as authoritative. It can suggest candidates, but the coding agent must still read and judge the actual reference files against the user's problem.

## Workflow

1. confirm interaction language.
2. collect the concrete optimization problem.
3. build a modeling checkpoint with source evidence, variables, objective, constraints, dimensions, data, assumptions, and ambiguity list.
4. classify the problem type using `references/problem_type_taxonomy.md`.
5. ask the human to confirm, revise, reject, or skip the interpreted model before executable solver code or final conclusions.
6. normalize the confirmed model into problem.yaml using `references/problem_schema.md`.
7. choose a solver route using `references/solver_catalog.md` and `references/solver_selection_rules.md`.
8. If the selected route is CDOpt, run or propose the post-install manifold smoke test before any CDOpt problem solve. Use `/Users/conanxu/cdopt_manifold_tests/run_all_notebooks.py` when that test suite exists; record the command, CDOpt version/path, pass/fail status, and any dependency/API failure. Treat this as an installation/API preflight, not as an application benchmark. For official CDOpt example tests, read the local Problem Description card under `examples/cdopt/problem-descriptions/`, treat its `## Prompt Body` as the modeling prompt, and read `references/cdopt_official_examples.md` only for implementation-template guidance after model review.
9. Route the structured problem when useful:

```bash
conda run -n ai4math python skills/optimization-skill/scripts/solver_router.py --spec <problem.yaml>
```

10. generate or adapt solver code only when appropriate, using `references/implementation_templates.md` and `references/code_generation_patterns.md`.
11. Put the exact command, risks, timeout, expected outputs, dependencies, and any preflight result into a review plan.
12. run only after approval.
13. Parse logs and evidence:

```bash
conda run -n ai4math python skills/optimization-skill/scripts/result_parser.py --log outputs/{run_id}/logs/run.log --out outputs/{run_id}/results/solver_summary.json
```

14. interpret numerical evidence: status, objective values, feasibility, residuals, gap, stationarity, certificates, numerical warnings, and next choices.

## Solver Routes

- **LP/QP:** CVXPY, SciPy/HiGHS, Gurobi, MOSEK, or repository-native code.
- **MILP:** Pyomo, CVXPY, HiGHS, CBC, GLPK, Gurobi, SCIP, or repository-native code.
- **SOCP/SDP/conic:** CVX, YALMIP, CVXPY, SDPT3, MOSEK, SCS, or repository-native code.
- **Smooth NLP:** SciPy, IPOPT, CasADi, or repository-native code.
- **Least squares:** SciPy, CVXPY, specialized repository-native solvers, or Gauss-Newton/LM tooling when already present.
- **Manifold/Riemannian:** CDOpt, Manopt, Pymanopt, Geoopt, or repository-native code.
- **Existing solver route:** repository-native solvers when they are the safest way to reproduce the original experiment.
- **Future backend route:** add solvers by extending `solver_catalog.md`, `problem_schema.md`, `solver_router.py`, `codegen.py`, and parser patterns together.

Current generated support is concrete but intentionally bounded:

- SDPT3 generation expects confirmed direct SQLP data in a `.mat` file and produces a MATLAB/Octave wrapper.
- CDOpt generation expects a confirmed manifold type, shape, backend, objective module/function, beta, and SciPy optimizer options. It produces a Python wrapper that constructs the manifold, builds `cdopt.core.problem`, runs SciPy `optimize.minimize`, and writes a JSON result summary.
- CDOpt execution should be preceded by the post-install manifold smoke test when available. The local suite at `/Users/conanxu/cdopt_manifold_tests` checks PyPI `cdopt==0.5.5`, manifold constructors, CDF gradient generation, finite-difference agreement, feasibility reporting, and a tiny L-BFGS-B path.
- CDOpt official examples should be handled in two layers: first derive the model from a local Problem Description card under `examples/cdopt/problem-descriptions/`, then adapt the implementation template from `references/cdopt_official_examples.md` after model review.
- Natural-language or LaTeX-only models require a modeling checkpoint before executable code is generated.
- Not all listed solver routes have automatic code generation; many should stop at a reviewed model, route recommendation, or repository-native adapter plan.

## Approval Rules

Ask before:

- running generated or repository solver code
- running the CDOpt post-install smoke test, unless the user has already approved CDOpt validation in the current task
- installing or upgrading solver packages
- compiling SDPT3/MEX/native extensions
- modifying MATLAB path, Python environment, or system solver configuration
- generating a modeling adapter from natural language, LaTeX, or an official Problem Description
- editing source code or replacing data
- accepting final mathematical conclusions

## Failure Signals

Call out these signals explicitly:

- missing solver package, MATLAB/Octave path, MEX file, Python backend, or license
- malformed SQLP data (`blk`, `At`, `C`, `b`) or dimension mismatch
- infeasible, dual-infeasible, unbounded, or ambiguous certificates
- stalled complementarity gap, residuals, short steps, bad scaling, or factorization warnings
- CDOpt backend mismatch, missing manifold definition, missing objective module, or shape mismatch
- MILP integrality-gap or time-limit ambiguity
- modeling ambiguity caused by natural-language, LaTeX, paper text, or official Problem Description interpretation

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
