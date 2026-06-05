# Modeling Pipeline

Use this reference when the input is not already a confirmed structured problem spec.

## Input Classification

Classify the input before choosing a solver:

- **Natural language:** plain problem statement, task request, or prose.
- **LaTeX:** objective, constraints, theorem statement, or paper model.
- **Paper excerpt:** text plus notation that may require definitions from nearby sections.
- **Repository source:** MATLAB/Python/Julia/R/C++ model code.
- **Solver data:** `.mat`, `.npz`, YAML/JSON, CSV, or generated data files.
- **Mixed:** any combination of the above.

## Modeling Checkpoint

Write a checkpoint before execution when the model is interpreted by the agent:

```markdown
# Modeling Checkpoint

## Variables

## Objective

## Constraints

## Data and Dimensions

## Problem Class

## Candidate Solver Routes

## Ambiguities

## Human Decision

approve / revise / reject / skip
```

The checkpoint should be compact but mathematically explicit. Include source evidence such as file paths, equation labels, line numbers, or quoted variable definitions when available.

## OptSkills Archetype Matching

Use `references/optskills/skill_library/` when the user problem resembles a known operations-research, MILP, network, assignment, routing, scheduling, facility-location, covering, packing, or resource-allocation archetype.

Prefer agent judgment over a fixed script flow:

1. Use the user's goal and terminology to search with `rg`, filenames, and `index.json`.
2. Read a few candidate archetype markdown files.
3. Compare variables, objective, constraints, data assumptions, and known pitfalls.
4. If the corpus is too noisy, optionally run `scripts/search_archetypes.py`.
5. Use the chosen archetype as a reference, then write a fresh model for the current problem.

## LaTeX to Model

For LaTeX:

1. Extract decision variables and dimensions.
2. Identify objective sense and expression.
3. List constraints and cones/domains.
4. Resolve notation from surrounding text.
5. Map the model to `problem_schema.md`.
6. Ask for confirmation if any symbol or dimension is ambiguous.

## Natural Language to Model

For natural language:

1. Restate the problem in mathematical terms.
2. Identify missing data, dimensions, and objective sense.
3. Propose a structured spec.
4. Ask the human to confirm or revise the model.
5. Generate code only after the model is confirmed.

## Repository Source to Model

For existing code:

1. Locate solver calls, model construction, data loading, and result writing.
2. Preserve the repository's native modeling layer when possible.
3. Extract the problem class and solver route.
4. Generate adapters only when the source lacks a safe entrypoint or when the human asks for one.

## Ambiguity Rules

Ask before execution when:

- variable dimensions are missing
- objective sense is implied but not explicit
- constraints use undefined notation
- data files are absent or synthetic
- multiple solver routes could change the mathematical interpretation
- scaling or regularization choices are not specified
