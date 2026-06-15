# AGENTS.md

This repository is an AI4Math Skill adapter package for CDOpt and
manifold-constrained optimization. The shared Skill layer is:

```text
cdopt-skill/SKILL.md
```

## Contract

- Use the shared Skill layer as the workflow source of truth.
- Keep platform-specific files thin; do not fork CDOpt workflow behavior.
- Start with model review before solver code.
- Ask before installs, solver runs, environment changes, comparison expansion,
  source edits, or final numerical claims.
- Report from durable artifacts rather than chat memory.
