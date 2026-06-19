---
name: optimization-modeling
description: Use when a coding agent needs optimization modeling, solver-route selection, approval-gated execution, numerical evidence review, or failure diagnosis for AI4Math optimization problems.
---

# Optimization Modeling

This root `SKILL.md` is a compatibility entrypoint for platforms that expect one
top-level Skill file. The shared Skill layer lives at:

```text
skills/optimization-modeling/SKILL.md
```

Read that concrete Skill before modeling or solving optimization tasks. Keep
platform adapters thin and improve the shared Skill layer first.

## Operating Boundary

- Inspect the problem and create a reviewed mathematical model first.
- Ask before solver execution, source edits, installs, long runs, or final
  numerical claims.
- Report solver status, objective values, feasibility, warnings, and limits
  from durable evidence.
