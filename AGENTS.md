# AGENTS.md

This repository is an AI4Math Skill adapter package for optimization modeling
and solver orchestration. The shared Skill layer is:

```text
skills/optimization-skill/SKILL.md
```

## Contract

- Use the shared Skill layer as the workflow source of truth.
- Keep platform-specific files thin; do not fork optimization workflow behavior.
- Build a model checkpoint before executable solver code.
- Ask before solver execution, installs, source edits, long runs, or final
  numerical claims.
- Report from saved evidence and distinguish numerical experiments from
  mathematical conclusions.
