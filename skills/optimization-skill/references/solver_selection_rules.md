# Solver Selection Rules

Use these rules after the modeling checkpoint is confirmed or when proposing candidate routes for human review.

## Ranking Criteria

Rank solver routes by:

1. **Model fidelity:** preserves the mathematical structure and original source assumptions.
2. **Evidence quality:** returns interpretable status, objective, feasibility, gap, residuals, or stationarity.
3. **Environment risk:** dependencies, licenses, native compilation, MATLAB availability, GPU/JAX requirements.
4. **Existing code:** prefer repository-native routes when they reproduce the source experiment cleanly.
5. **Codegen support:** generated wrappers are helpful, but not a reason to choose the wrong solver.
6. **Human approval:** execution, installs, code edits, data downloads, and final conclusions require approval.

## Default Choices

- Prefer existing repository code when the task is reproduction or when the model is deeply tied to source-specific data.
- Prefer modeling layers for LP/MILP/SOCP/SDP when the model is naturally algebraic and no direct solver data exists.
- Prefer direct SDPT3 only when SQLP data or MATLAB conic modeling already exists.
- Prefer CDOpt or another manifold route only when manifold constraints are explicit and the objective can be evaluated.
- Prefer SciPy/IPOPT/CasADi for smooth NLP only after checking derivative availability and constraints.
- Stop at a modeling checkpoint if the input is natural-language only and key model choices are ambiguous.

## Tie Breakers

- If two routes are mathematically plausible, present both with trade-offs.
- If a solver needs a commercial license, list an open-source fallback.
- If code generation is not implemented for the best route, say so and propose a reviewed adapter plan.
- If the solver may be numerically fragile, state scaling and diagnostic checks in the run plan.

## Approval Gates

Ask before:

- installing or upgrading solver packages
- compiling native/MEX extensions
- changing MATLAB/Python/Julia environment paths
- downloading datasets
- generating a modeling adapter from unconfirmed math
- running generated or repository solver code
- accepting final mathematical conclusions
