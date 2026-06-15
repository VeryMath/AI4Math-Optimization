# Codex Loading Notes

This repository exposes a shared Skill layer at:

```text
skills/optimization-skill/SKILL.md
```

Use from the checkout by asking Codex to read `AGENTS.md`, `SKILL.md`, and the
concrete Skill file. For local discovery, link or copy
`skills/optimization-skill/` into the Codex Skill path used by your installation,
then restart or reload if required.

Do not duplicate workflow logic in `.codex/`; update the shared Skill layer.
