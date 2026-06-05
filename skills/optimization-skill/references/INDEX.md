# Optimization Skill Reference Index

## Trigger

Read this index when the task involves optimization problem modeling, OptSkills archetype matching, solver selection, generated solver code, SDPT3, CDOpt, MATLAB/Octave, Python optimization backends, LaTeX-to-model conversion, result parsing, or solver failure diagnosis.

## Read

- `modeling_pipeline.md`: read when the input is natural language, LaTeX, a paper excerpt, README instructions, data, or source code rather than a confirmed structured spec.
- `optskills/SOURCE.md`: read when using the imported OptSkills references for archetype matching.
- `problem_schema.md`: read before accepting, generating, or editing a structured optimization problem spec.
- `solver_catalog.md`: read when choosing SDPT3, CDOpt, an existing repository solver, or an extension backend.
- `code_generation_patterns.md`: read before generating MATLAB, Octave, Python, or modeling-layer entrypoints.
- `evaluation_reporting.md`: read after a run, failed run, or solver-status ambiguity.

## Do

- Preserve a clear chain from input statement to model, model to solver route, route to command, and command to evidence.
- Treat OptSkills archetypes as references that still need agent judgment and human review.
- Ask for model confirmation before executing a problem derived from natural language or LaTeX.
- Ask for approval before execution, installs, MEX compilation, environment changes, source edits, or final conclusions.
- Report solver uncertainty and numerical warnings explicitly.

## Do not

- Do not treat an interpreted model as confirmed math.
- Do not run generated solver code without an approved run plan.
- Do not install CDOpt, CVX, YALMIP, SDPT3, MATLAB toolboxes, Python solver packages, or MEX dependencies without approval.
- Do not hide infeasibility, weak certificates, bad scaling, or ambiguous termination codes.
