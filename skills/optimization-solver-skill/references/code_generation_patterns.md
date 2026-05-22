# Code Generation Patterns

Generated code is an execution adapter, not a source rewrite. Write it under `outputs/{run_id}/generated/` unless the human approves adding an adapter to the source repository.

## General Adapter Contract

Generated adapters should:

1. State that they were generated and require review before execution.
2. Load only approved data paths.
3. Fail clearly when a dependency, model component, or shape is missing.
4. Save machine-readable summaries under `outputs/{run_id}/results/`.
5. Preserve raw stdout/stderr in `outputs/{run_id}/logs/run.log`.
6. Avoid secrets, license tokens, and private environment assumptions.

## MATLAB SDPT3 Wrapper

Generated wrappers should:

1. Optionally run the approved SDPT3 startup path.
2. Load `blk`, `At`, `C`, and `b` from an approved `.mat` file.
3. Build `OPTIONS` from `sqlparameters`.
4. Call `sdpt3(blk, At, C, b, OPTIONS)` by default.
5. Save `obj`, `X`, `y`, `Z`, `info`, and `runhist` to a result `.mat` file.
6. Emit enough text for the parser to capture termination status and numerical warnings.

## Python CDOpt Wrapper

Generated wrappers should:

1. Import CDOpt and fail clearly if it is missing.
2. Import the user-provided objective module and function.
3. Construct the requested manifold from the selected backend when all required fields are confirmed.
4. Build a `cdopt.core.problem` object.
5. Route the generated constraint-dissolving function to SciPy `optimize.minimize` for the generated adapter path.
6. Write a JSON summary with objective value, feasibility, iterations, backend, and status.

The generated CDOpt path supports `torch`, `numpy`/`np`, and `jax` manifold constructors when the spec provides a manifold type, shape, objective module, objective function, beta, and SciPy optimizer options. If the source repository already uses a PyTorch, JAX, or custom optimizer loop, preserve that route as repository-native unless the human approves a custom adapter.

When the manifold construction details are ambiguous, stop at the modeling checkpoint instead of inventing executable code.

## Modeling-Layer Adapter

Use this pattern for CVX, YALMIP, CVXPY, JuMP, or Pyomo:

1. Preserve the mathematical names from the problem spec.
2. Keep model construction separate from solver invocation.
3. Print model dimensions and selected solver.
4. Save solver status and objective value in a language-native result file plus JSON when possible.
5. Make the generated file easy to diff against the reviewed model checkpoint.

## Safety

- Never embed secrets, license tokens, or private paths in generated code.
- Keep generated code deterministic and small.
- Generated code may stop with a clear message when required problem pieces are missing; it should not silently invent math.
- If code generation would require unresolved modeling choices, write a modeling checkpoint instead of executable code.
