# Problem Schema

Use this schema as the bridge between human math and executable solver code. It is intentionally reviewable: a human should be able to inspect the objective, variables, constraints, data sources, solver route, and execution risks before anything runs.

## Canonical Shape

```yaml
schema_version: 1
problem_id: example_problem
input_type: latex
problem_class: semidefinite_program
domain:
  family: conic_optimization
  tags: [sdp, sqlp]
objective:
  sense: minimize
  expression: trace(C * X)
variables:
  - name: X
    type: symmetric_matrix
    shape: [n, n]
    cone: positive_semidefinite
constraints:
  - name: affine_equalities
    expression: A(X) = b
data:
  mat_file: data/problem.mat
  parameters:
    n: 100
solver_preferences:
  backend: auto
  modeling_layer: direct
  timeout_seconds: 300
review:
  modeling_status: proposed
  execution_approval_required: true
sdpt3:
  data_variables:
    blk: blk
    At: At
    C: C
    b: b
  options:
    printlevel: 2
metadata:
  source: paper section, repository file, or user prompt
  notes: unresolved assumptions and evidence
```

## Required Fields

- `schema_version`: use `1`.
- `problem_id`: stable identifier for filenames and run artifacts.
- `input_type`: `natural_language`, `latex`, `paper_excerpt`, `repository_source`, `solver_data`, `structured_spec`, or `mixed`.
- `problem_class`: `linear_program`, `quadratic_program`, `second_order_cone_program`, `semidefinite_program`, `conic_sqlp`, `nonlinear_program`, `least_squares`, `riemannian`, `manifold_optimization`, `orthogonality_constrained`, `unconstrained`, or `unknown`.
- `objective.sense`: `minimize`, `maximize`, or `unknown`.
- `review.modeling_status`: `proposed`, `confirmed`, `needs_revision`, or `unknown`.

## Modeling Fields

- `domain.family`: broad family such as `conic_optimization`, `smooth_nonlinear`, `manifold_optimization`, or `repository_native`.
- `variables`: decision variables, types, shapes, cones, domains, and initialization hints.
- `constraints`: named constraints with expressions, cones, dimensions, and source evidence.
- `data`: paths and symbolic parameters needed to instantiate the model.
- `metadata.notes`: ambiguity, assumptions, citations, source lines, or unresolved modeling questions.

## Solver Fields

### SDPT3

Use SDPT3 for SQLP, SDP, SOCP, and linear-cone forms.

- `data.mat_file`: `.mat` file containing problem data.
- `sdpt3.data_variables`: variable names for `blk`, `At`, `C`, and `b`.
- `sdpt3.options`: fields copied into `OPTIONS` after `sqlparameters`.
- `sdpt3.solver`: optional, `sdpt3`, `sqlp`, or `HSDsqlp`.
- `sdpt3.startup_path`: optional path to SDPT3 `startup.m` or installation directory.

### CDOpt

Use CDOpt for manifold-constrained or Riemannian optimization.

```yaml
problem_class: riemannian
cdopt:
  backend: torch
  manifold:
    type: stiefel_torch
    shape: [200, 8]
  objective:
    module: problem_definition
    function: obj_fun
  beta: 100
  optimizer:
    family: scipy
    method: L-BFGS-B
    options:
      maxiter: 200
      gtol: 1.0e-6
```

The objective module must be importable from the approved working directory or from a path added in the run plan.

Concrete code generation currently supports:

- `cdopt.backend`: `torch`, `numpy`/`np`, or `jax`.
- `cdopt.manifold.type`: `sphere_*`, `oblique_*`, `stiefel_*`, `grassmann_*`, `generalized_stiefel_*`, `hyperbolic_*`, or `symp_stiefel_*`, with suffix matching the backend (`_torch`, `_np`, or `_jax`).
- `cdopt.manifold.shape`: non-empty integer list passed to the manifold constructor.
- `cdopt.objective.module` and `cdopt.objective.function`: an importable objective function.
- `cdopt.optimizer.family`: `scipy` for generated wrappers. Other optimizer families should use a repository-native adapter or a reviewed custom extension.

### Modeling Layers

Use a modeling layer when the model is naturally expressed in a higher-level language or already exists in the source:

```yaml
solver_preferences:
  backend: sdpt3
  modeling_layer: yalmip
modeling_layer:
  language: matlab
  package: yalmip
  source_file: models/demo_sdp.m
```

Treat newly generated modeling adapters as reviewable artifacts.
