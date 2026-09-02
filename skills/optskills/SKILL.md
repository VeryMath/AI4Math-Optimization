---
name: optskills
description: Use when a coding agent must model or solve a natural-language operations-research problem by selecting from the released OptSkills problem-archetype cards, or when the user explicitly asks to update this standalone OptSkills library from its official upstream repository.
---

# OptSkills

Use this package independently. Do not call sibling skills in the enclosing
repository and do not require the OptSkills training, agent, chat, or embedding
system.

## Normal use

1. Restate the user's sets, parameters, decision variables, objective,
   constraints, units, and assumptions.
2. Read `skill_library/index.json`. Compare the problem structure with each
   entry's `name` and `description`, then select one to three candidates.
3. Read only the selected files using their relative `path` fields. Never
   invent a path from a skill ID.
4. Choose the closest card by variables, objective, and constraint structure.
   If none fits, say that no released card matched and continue with general
   mathematical modeling without claiming a card was used.
5. Apply the card to the user's actual data. Card examples are guidance, not
   proof that the new model is correct.
6. Use only solver libraries and licenses actually available in the current
   environment. Ask before installing dependencies.
7. Check solver status before reading values. Recompute the objective and the
   problem's key constraints whenever execution is possible.
8. Report separately: selected card, completed model, solver execution,
   constraint checks, and unresolved limitations.

## Explicit update requests

Only when the user asks to update or synchronize OptSkills, read `UPDATE.md`
and follow it. Do not update during an ordinary modeling task.

## Source boundary

The files under `skill_library/` are released upstream material. Do not rewrite
them as part of normal use. If a card contains a placeholder, missing
dependency, inconsistent notation, or suspected error, correct the active task
explicitly, report the issue, and leave the card unchanged until an upstream
release replaces it.
