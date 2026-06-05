# Evaluation and Reporting

Use this reference after solver execution, failed execution, or status ambiguity.

## Minimum Evidence

Report:

- command that was approved and run
- solver backend and modeling layer
- objective value or best available metric
- feasibility status and residuals when available
- termination code and solver status
- runtime and iteration count when available
- raw log location
- generated entrypoint location
- limitations and unresolved ambiguity

## Status Vocabulary

- `completed`: solver reached a credible success or optimal status.
- `failed`: execution failed before producing usable solver evidence.
- `infeasible`: solver returned a primal/dual infeasibility signal.
- `numerical_warning`: solver produced results with scaling, residual, or factorization concerns.
- `ambiguous`: status cannot support a mathematical conclusion.
- `needs_model_review`: the model interpretation requires human correction before execution.

## Failure Diagnosis

Route failures by evidence:

| Evidence | Likely category |
| --- | --- |
| missing package, undefined function, missing MEX | dependency or environment |
| dimension mismatch, missing field, malformed `blk` | data/model schema |
| infeasible or dual infeasible | mathematical status |
| stalled residuals, short steps, ill conditioning | numerical failure |
| missing objective module or manifold | CDOpt adapter/modeling |
| timeout or killed process | resource or budget |

## Reporting Shape

Use concise run summaries:

```markdown
# Solver Run Summary

## Status

## Model

## Solver Route

## Evidence

## Failure or Warnings

## Next Choices
```

For final conclusions, distinguish solver evidence from mathematical truth. A solver status can support a claim, but weak certificates, bad scaling, or modeling ambiguity should remain visible.

