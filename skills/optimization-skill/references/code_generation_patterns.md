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
