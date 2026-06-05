---
name: optimization-modeling-skill
description: Use when Codex needs to turn a natural-language, LaTeX, paper, README, data, or source-code optimization problem into a reviewed mathematical model, archetype match, modeling checkpoint, or problem.yaml before handing off to an optimization solver workflow. Includes the full imported OptSkills released skill libraries as references.
---

# Optimization Modeling Skill

This Skill converts optimization problem statements into reviewable mathematical models. It is the modeling-side companion to `optimization-solver-skill`: this Skill identifies the problem archetype and writes the model checkpoint or `problem.yaml`; the solver Skill routes, generates, executes, and parses solver evidence.

## Operating Principle

Separate the modeling question from the solving question:

1. **Archetype:** which known optimization pattern matches the problem.
2. **Model:** variables, objective, constraints, dimensions, and data.
3. **Review checkpoint:** assumptions and ambiguities the human must confirm.
4. **Handoff:** a structured `problem.yaml` suitable for `optimization-solver-skill`.

Do not silently invent missing dimensions, objective sense, data, penalties, or solver choices. If the model is interpreted from prose, ask for confirmation before execution.

## Interactive Opening

At the start of a new interactive modeling session, first confirm the user's preferred interaction language. Keep this as one short question. After the language is confirmed, invite the user to send the concrete optimization problem in any form: prose, formulas, paper excerpt, code, data description, or a mixed bundle.

Do not start with a questionnaire about input type, target, solver, or workflow mode. The user often has one concrete problem in hand. Let them provide it directly, then infer whether the task is modeling, solving, reproduction, or failure diagnosis. Ask follow-up questions only when a missing detail blocks a correct model.

Suggested opening:

```text
Would you like to work in Chinese or English? After that, send me the concrete optimization problem directly. It can be prose, formulas, a paper excerpt, code, or data notes; I will read it first and guide the modeling from there.
```

## References

- `references/optskills/SOURCE.md`: source, license, and imported library scope.
- `references/optskills/skill_library/`: full imported OptSkills released libraries:
  - `skill_library_cluster`
  - `skill_library_learned`
  - `skill_library_nanoco_learned`
- `scripts/search_archetypes.py`: optional helper for local keyword search over the imported OptSkills indexes and markdown files.

The primary navigation method is agent judgment: inspect the user goal, use `rg`, read the relevant `index.json` files, open candidate markdown references, compare their modeling assumptions, and choose the best archetype. The search script is only an optional helper when the corpus is large or the first `rg` pass is noisy:

```bash
python skills/optimization-modeling-skill/scripts/search_archetypes.py --query "<problem statement>" --limit 5
```

Never treat the script ranking as authoritative. It can suggest candidates, but the coding agent must still read and judge the actual reference files against the user's problem.

## Workflow

1. Classify the input as natural language, LaTeX, paper excerpt, repository source, solver data, or mixed.
2. Navigate the OptSkills references with `rg`, `index.json`, filename patterns, and optional script search to find candidate archetypes.
3. Read the most relevant archetype files and compare them to the user problem.
4. Write a compact modeling checkpoint:

```markdown
# Modeling Checkpoint

## Archetype Match

## Variables

## Objective

## Constraints

## Data and Dimensions

## Solver-Relevant Structure

## Ambiguities

## Human Decision

approve / revise / reject / skip
```

5. If the model is confirmed, normalize it into `problem.yaml` compatible with `optimization-solver-skill/references/problem_schema.md`.
6. Hand off to `optimization-solver-skill` for route selection and execution planning.

## Archetype Matching Rules

- Prefer a specific archetype over a generic MILP when the data and constraints match.
- Treat similar file names across OptSkills libraries as alternate formulations; compare the modeling stage and pitfalls before choosing.
- If multiple archetypes plausibly fit, list the candidates and the modeling difference that would decide between them.
- Preserve user terminology in the checkpoint, but normalize mathematical names in `problem.yaml`.
- Keep generated models small and reviewable; do not copy long reference passages into the final answer.

## Handoff Contract

When handing off to `optimization-solver-skill`, include:

- `modeling_checkpoint.md` content or location.
- `problem.yaml` with `review.modeling_status` set to `proposed` unless the human has confirmed it.
- Source evidence: user prompt, paper equation, file path, or OptSkills reference path.
- Open ambiguity list and any solver-relevant warnings.

## Safety

- Ask before executing solver code, installing packages, changing environments, or accepting final mathematical conclusions.
- Mark OptSkills-derived templates as references, not proof that the current user problem has been modeled correctly.
- Report mismatch signals: missing sets, unsupported nonlinear terms, unclear objective sense, incompatible index sets, or absent data.
