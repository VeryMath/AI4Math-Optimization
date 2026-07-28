# OSQP Solver Skill

Chinese guide: [README.zh-CN.md](README.zh-CN.md)

This AI4Math skill models, solves, updates, and independently checks continuous
convex quadratic programs with the native OSQP Python interface. It is a
release-ready local candidate for
[`VeryMath/AI4Math-Optimization`](https://github.com/VeryMath/AI4Math-Optimization);
it is not an official upstream package until that repository accepts and merges
it.

## Scope

Use the skill for

\[
\min_x \tfrac12 x^\top P x + q^\top x
\quad\text{subject to}\quad l \leq Ax \leq u,
\qquad P=P^\top\succeq0.
\]

Do not route mixed-integer, nonconvex, nonlinear-constraint, SDP, or general
SOCP models to this package. The bundled JSON runner is an auditable tool for
small dense examples, not a production sparse-data format.

## Isolated installation

Create an isolated environment and install the supported OSQP major version:

```bash
python3 -m venv .venv-osqp
source .venv-osqp/bin/activate
python -m pip install -r requirements-test.txt
python scripts/check_osqp_environment.py --json
```

The probe reports `ready: true` only when `osqp`, `numpy`, and `scipy` import
successfully and the OSQP version is in the supported range. Obtain approval
before installing into an existing environment.

## Quick start

From this package directory:

```bash
python scripts/solve_qp.py references/feasible-example.json
python scripts/solve_qp.py references/primal-infeasible-example.json
python scripts/solve_qp.py references/dual-infeasible-example.json
```

Use `--validate-only` for dependency-free structural validation. It does not
run PSD or numerical solution checks:

```bash
python scripts/solve_qp.py references/feasible-example.json --validate-only
```

For a persistent report, choose a path different from the input:

```bash
python scripts/solve_qp.py references/feasible-example.json \
  --output outputs/feasible-result.json
```

## CLI contract and limits

- Successful validation or an accepted solve exits `0`. Input/dependency
  failures exit `2`; a rejected numerical status or solver failure exits `3`.
- Standard output is exactly one JSON document on success. Machine-readable
  errors are written as exactly one JSON document to standard error.
- Result documents use `schema_version: osqp-solver-result-v1`; structural-only
  reports use `osqp-solver-validation-v1`.
- `settings.verbose: true` is rejected because OSQP logging would corrupt the
  single-JSON standard-output contract.
- The runner rejects resolved input/output paths that are the same. A distinct
  existing output file may be atomically replaced, so use a run-specific path.
- The default dense guard accepts at most a 32 MiB input, `n <= 1000`, and
  `2,000,000` logical entries across `P` and `A`. Use the native sparse API for
  larger problems.
- An accepted solution must pass primal feasibility, stationarity,
  normal-cone/complementarity, objective, and PSD checks. Infeasibility
  certificates are normalized and must pass scale-aware residual, sign, and
  strict negative-margin checks.

Read [SKILL.md](SKILL.md) for the workflow and
[references/verification.md](references/verification.md) for the mathematical
acceptance conditions.

## Validation

From the AI4Math Skill Library root, with the isolated environment active:

```bash
python -m unittest discover -s tests -p 'test_osqp_solver_skill.py' -v
python scripts/validate_skill_repo.py
```

Do not treat skipped numerical tests as release evidence. The OSQP-enabled
suite must run without skips before publishing; inspect the unittest summary
and require `skipped=0`.

## License, citation, and provenance

This package is intended to follow the AI4Math repository's MIT license after
maintainer authorization and upstream acceptance. The separately installed
OSQP project is Apache-2.0 licensed; this package does not vendor or relicense
OSQP code. Software licensing and academic citation are separate obligations.
Use [references/citation.md](references/citation.md) for the official OSQP
citation.

The workflow and references were prepared from the official OSQP documentation
linked in [references/python-api.md](references/python-api.md). Before public
release, a human maintainer must confirm publication authorization and record
factual contributor attribution. Packaging by an AI agent is not that
authorization.
