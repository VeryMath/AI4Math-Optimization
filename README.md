# Optimization Solver Skill

English | [简体中文](README.zh-CN.md)

Optimization Solver Skill is a standalone, coding-agent-facing project for turning mathematical optimization tasks into safe, inspectable solver workflows. It is designed for agents that need to understand an optimization problem, choose a solver ecosystem, generate execution code, request approval, run the solver, parse evidence, and diagnose failures.

The project presents the full Skill concept, not a narrow demo. It covers the target end-to-end workflow from natural-language or LaTeX problem statements to structured modeling, solver selection, execution, result interpretation, and Skill-registry integration. The helper scripts automate the structured-spec layer for SDPT3 and CDOpt, while the documentation defines the broader modeling and solver expansion surface.

## Core Idea

The human gives a goal, problem statement, paper excerpt, repository, `.mat` file, or structured problem spec. The coding agent uses this Skill to:

1. Identify the optimization problem class and modeling form.
2. Convert or normalize the problem into a reviewable problem spec.
3. Route the task to an appropriate solver backend.
4. Generate solver entrypoint code without rewriting the source project.
5. Write a run plan and ask for approval before execution or dependency changes.
6. Run only approved commands.
7. Parse solver outputs, numerical status, certificates, and failures.
8. Report evidence and propose repairs or alternative solver routes.

## Capability Map

| Layer | Scope | Current artifacts |
| --- | --- | --- |
| Problem understanding | Natural language, LaTeX, paper excerpts, README instructions, local data files, existing source code | `references/problem_schema.md`, `references/modeling_pipeline.md` |
| Modeling conversion | Standard forms for LP, QP, SOCP, SDP, SQLP, nonlinear programs, manifold optimization, and source-defined models | `problem_schema.md`, modeling checkpoints |
| Solver routing | SDPT3, CDOpt, existing repository solvers, and extension points for CVX/CVXPY/YALMIP/JuMP/Pyomo/MOSEK/SciPy | `references/solver_catalog.md`, `scripts/solver_router.py` |
| Code generation | MATLAB/Octave wrappers, Python adapters, log/result output contracts | `references/code_generation_patterns.md`, `scripts/codegen.py` |
| Execution governance | Human approvals before solver runs, installs, MEX compilation, source edits, and modeling adapters | `SKILL.md`, plan artifact contract |
| Result parsing | Solver status, objective values, infeasibility, numerical instability, dependency failures, shape/data errors | `scripts/result_parser.py` |
| Reporting | Run summary, solver evidence, failure diagnosis, next solver choices | `references/evaluation_reporting.md` |

## Solver Coverage

The first concrete backends are:

- **SDPT3** for confirmed semidefinite, second-order-cone, linear-cone, and SQLP-style MATLAB/Octave problems. The helper layer routes SQLP-compatible specs and generates a MATLAB/Octave wrapper that loads `blk`, `At`, `C`, and `b`, applies `sqlparameters`, calls the selected SDPT3 entrypoint, and saves solver evidence.
- **CDOpt** for confirmed Riemannian and manifold-constrained optimization through constraint dissolving. The helper layer routes common manifold classes and generates a Python wrapper that constructs CDOpt manifolds, builds `cdopt.core.problem`, runs SciPy `optimize.minimize`, and writes a JSON summary.

Current generated CDOpt wrappers support `torch`, `numpy`/`np`, and `jax` manifold constructors for sphere, oblique, Stiefel, Grassmann, generalized Stiefel, hyperbolic, and symplectic Stiefel families. They require an importable objective module/function and a reviewed problem spec. Natural-language or LaTeX-only problems still stop at a modeling checkpoint before executable code is generated.

The Skill is structured to grow into a broader optimization solver hub:

- Modeling layers: CVX, YALMIP, CVXPY, JuMP, Pyomo.
- Conic and SDP solvers: SDPT3, SeDuMi, MOSEK, SCS, Clarabel.
- Smooth and nonlinear solvers: SciPy optimize, IPOPT-style routes, repository-native methods.
- Manifold optimization: CDOpt, Manopt/Pymanopt-style routes, orthogonality-constrained models.

## Project Layout

- `skills/optimization-solver-skill/SKILL.md`: primary Skill instructions for coding agents.
- `skills/optimization-solver-skill/agents/openai.yaml`: UI metadata for Skill-aware agents.
- `skills/optimization-solver-skill/references/INDEX.md`: reference routing index.
- `skills/optimization-solver-skill/references/problem_schema.md`: canonical optimization problem spec.
- `skills/optimization-solver-skill/references/modeling_pipeline.md`: natural-language, LaTeX, and source-to-model workflow.
- `skills/optimization-solver-skill/references/solver_catalog.md`: solver and modeling backend guidance.
- `skills/optimization-solver-skill/references/code_generation_patterns.md`: generated adapter conventions.
- `skills/optimization-solver-skill/references/evaluation_reporting.md`: result interpretation and reporting guidance.
- `skills/optimization-solver-skill/scripts/solver_router.py`: route structured specs to solver backends.
- `skills/optimization-solver-skill/scripts/codegen.py`: generate SDPT3 MATLAB or CDOpt Python entrypoints.
- `skills/optimization-solver-skill/scripts/result_parser.py`: parse solver logs into compact summaries.
- `tests/`: maintainer checks for routing, code generation, and parsing.
- `pyproject.toml`: standalone Python test/package metadata for the helper layer.

## Agent Workflow

1. Read `skills/optimization-solver-skill/SKILL.md`.
2. Inspect the user input and classify it as natural-language, LaTeX, repository source, solver data, or structured spec.
3. If the input is not already structured, create a modeling checkpoint using `references/modeling_pipeline.md`; ask the human to confirm the mathematical model before execution.
4. Normalize the problem with `references/problem_schema.md`.
5. Route the solver:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/solver_router.py --spec problem.yaml
```

6. Generate an entrypoint when the route supports code generation:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/codegen.py --spec problem.yaml --out outputs/run_001/generated
```

7. Put the generated entrypoint and exact command in a review plan.
8. Ask for approval before running solver code, installing dependencies, compiling MEX files, changing MATLAB/Python environments, or editing source.
9. After an approved run, parse logs:

```bash
conda run -n ai4math python skills/optimization-solver-skill/scripts/result_parser.py --log outputs/run_001/logs/run.log --out outputs/run_001/results/solver_summary.json
```

10. Report objective values, feasibility, certificates, residuals, solver status, runtime, and failure evidence.

## Example Problem Spec

```yaml
schema_version: 1
problem_id: demo_sdp
input_type: structured_spec
problem_class: conic_sqlp
objective:
  sense: minimize
data:
  mat_file: data/demo_sdp.mat
solver_preferences:
  backend: auto
  timeout_seconds: 300
sdpt3:
  data_variables:
    blk: blk
    At: At
    C: C
    b: b
  options:
    printlevel: 2
review:
  modeling_status: confirmed
  execution_approval_required: true
```

## Safety Boundary

- Do not run generated solver code without human approval.
- Do not install SDPT3, CDOpt, CVX, YALMIP, MATLAB toolboxes, Python solver packages, or backend dependencies without approval.
- Do not compile MEX files without approval.
- Do not execute a natural-language or LaTeX-derived model until the structured model has been reviewed.
- Do not hide numerical uncertainty. Report infeasibility, weak certificates, stalled residuals, and ambiguous solver statuses explicitly.

## Verify

Run from this folder:

```bash
python /Users/conanxu/.codex/skills/.system/skill-creator/scripts/quick_validate.py skills/optimization-solver-skill
conda run -n ai4math pytest
```

Current verification: `Skill is valid!` and `8 passed`.
