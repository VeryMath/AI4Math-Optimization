# Human-Agent Interaction Examples

Use these examples to test the Skill in conversation. They are not CI tests. They are prompt scenarios that check whether a coding agent follows the Skill workflow: inspect sources, identify the math, choose a solver route, write a modeling checkpoint when needed, explain execution risks, and ask for approval before running code or changing dependencies.

## Source Material

CDOpt's documentation provides useful interaction-test material:

- Examples overview: https://cdopt.github.io/md_files/examples.html
- SciPy examples overview: https://cdopt.github.io/examples/example_scipy.html
- Dictionary Learning: https://cdopt.github.io/examples/dictionary_learning.html
- Dictionary Learning Accelerated by JIT: https://cdopt.github.io/examples/dictionary_learning_jax.html
- PyTorch examples overview: https://cdopt.github.io/examples/example_torch.html
- JAX/FLAX examples overview: https://cdopt.github.io/examples/example_jax.html

Use official examples as source evidence, but shrink problem sizes and avoid heavy training runs unless the human approves the runtime and dependencies.

## Scenario 1: Choose a CDOpt Example for Skill Validation

Human prompt:

```text
Use $optimization-solver-skill to inspect the CDOpt examples page and pick one example for a human-agent workflow test. I want something lightweight that checks CDOpt modeling, solver routing, and result parsing.
```

Expected agent behavior:

1. Read `references/INDEX.md` and this file.
2. Inspect the CDOpt examples page.
3. Recommend the SciPy Dictionary Learning example as the first interaction test because it exercises manifold modeling and CDOpt core APIs without neural-network training.
4. Explain that PyTorch and JAX/FLAX examples are useful optional tests but have heavier dependency and runtime risk.
5. Propose a shrunken problem size and CPU-only run.
6. Ask before installing CDOpt, torch, jax, scipy, or running the example.

Acceptance checklist:

- The agent distinguishes interaction testing from automated CI testing.
- The agent recommends a concrete example and explains why.
- The agent does not run anything before approval.
- The agent names dependency risks for PyTorch/JAX examples.

## Scenario 2: Dictionary Learning as a CDOpt Workflow Test

Human prompt:

```text
Use $optimization-solver-skill with the CDOpt Dictionary Learning example. Turn it into a small human-reviewed workflow test: identify the model, route the solver, and prepare a run plan. Use tiny dimensions and CPU only.
```

Expected agent behavior:

1. Identify the model as Stiefel-manifold optimization:
   - variable: `X in R^{n x n}`
   - objective: minimize the negative fourth-power dictionary-learning objective
   - constraint: `X^T X = I`
2. Write a modeling checkpoint before code generation.
3. Normalize the task into a `problem.yaml` style spec:

```yaml
schema_version: 1
problem_id: cdopt_dictionary_learning_small
input_type: paper_excerpt
problem_class: riemannian
domain:
  family: manifold_optimization
  tags: [stiefel, dictionary_learning, cdopt]
objective:
  sense: minimize
  expression: -sum((Y @ X) ** 4)
variables:
  - name: X
    type: matrix
    shape: [n, n]
    manifold: stiefel
constraints:
  - name: orthogonality
    expression: X.T @ X = I
data:
  parameters:
    n: 3
    m: 90
    theta: 0.3
solver_preferences:
  backend: cdopt
  timeout_seconds: 120
review:
  modeling_status: proposed
  execution_approval_required: true
cdopt:
  backend: torch
  manifold:
    type: stiefel_torch
    shape: [3, 3]
  objective:
    module: problem_definition
    function: obj_fun
  beta: auto
```

4. Route to CDOpt and explain why.
5. Create a run plan with expected evidence:
   - objective value
   - iterations or function evaluations
   - stationarity or gradient norm
   - feasibility of the Stiefel constraint
   - raw log path
6. Ask for `approve`, `revise`, `reject`, or `skip`.

Acceptance checklist:

- The agent recognizes the Stiefel manifold from `X^T X = I`.
- The agent shrinks the example rather than reproducing the full notebook by default.
- The agent asks for model confirmation before execution.
- The agent does not require GPU.

## Scenario 3: JIT Example as an Optional Backend Test

Human prompt:

```text
Use $optimization-solver-skill to evaluate whether the CDOpt Dictionary Learning JIT example is a good interaction test.
```

Expected agent behavior:

1. Identify the JIT example as related to Dictionary Learning but using JAX.
2. Explain that it tests CDOpt plus JAX/JIT integration, not just the core CDOpt workflow.
3. Mark it as optional because JAX installation and hardware behavior can vary.
4. Propose a two-stage plan:
   - first run the non-JAX Dictionary Learning workflow
   - then run a JAX/JIT comparison only after dependency approval

Acceptance checklist:

- The agent does not treat JAX as required for basic CDOpt validation.
- The agent asks before installing JAX.
- The agent frames JIT speedup as backend evidence, not solver correctness by itself.

## Scenario 4: PyTorch Neural-Network Examples as Heavy Interaction Tests

Human prompt:

```text
Use $optimization-solver-skill to decide whether CDOpt's PyTorch neural-network examples should be part of the human-agent test set.
```

Expected agent behavior:

1. Recognize PyTorch examples as useful for testing CDOpt neural-network layers and manifold-constrained training.
2. Treat them as heavy integration examples rather than first-line solver tests.
3. Ask about acceptable runtime, GPU/CPU constraints, and dependency installation.
4. Prefer a small model or single-batch dry run when the goal is testing the Skill workflow rather than training a model.

Acceptance checklist:

- The agent separates solver API validation from training-performance validation.
- The agent does not default to running long neural-network training.
- The agent names PyTorch and optional optimizer packages as dependency risks.

## Scenario 5: Natural-Language Request Grounded in an Official Example

Human prompt:

```text
Use $optimization-solver-skill. I want to solve the CDOpt dictionary-learning example where X is orthogonal and the objective uses fourth powers of YX. Build the model and tell me what you would run.
```

Expected agent behavior:

1. Treat this as natural-language-to-model conversion.
2. Write or summarize a modeling checkpoint.
3. Ask whether the intended model is the official Dictionary Learning Stiefel problem.
4. Produce a structured spec only after noting assumptions.
5. Prepare a route and plan, then pause for approval.

Acceptance checklist:

- The agent does not skip the modeling checkpoint.
- The agent asks about missing dimensions and data-generation choices.
- The agent keeps the official example as evidence, not as a command to run blindly.

