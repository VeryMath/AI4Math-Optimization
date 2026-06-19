---
name: cdopt-optimization
description: Use when a coding agent needs CDOpt-aware manifold-constrained optimization modeling, environment checks, approval-gated solver runs, evidence-backed summaries, or comparison plans.
---

# CDOpt Optimization

This root `SKILL.md` is a compatibility entrypoint for platforms that expect one
top-level Skill file. The shared Skill layer lives at:

```text
cdopt-optimization/SKILL.md
```

Read that concrete Skill before modeling or running CDOpt tasks. Keep platform
adapters thin and improve the shared Skill layer first.

## Operating Boundary

- Build a modeling checkpoint before executable solver code.
- Ask before package installation, solver runs, environment changes,
  comparison expansion, or numerical conclusions.
- Report from saved artifacts under `outputs/{run_id}/`.
