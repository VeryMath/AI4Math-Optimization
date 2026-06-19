#!/usr/bin/env python3
"""Write a tiny CPU-only CDOpt Stiefel dictionary-learning runner."""

import argparse
import textwrap
from pathlib import Path


RUNNER = r'''#!/usr/bin/env python3
"""Tiny deterministic CDOpt Stiefel dictionary-learning example."""

import argparse
import json
import time
from pathlib import Path

import cdopt
import numpy as np
import scipy as sp
import torch

def build_data(n, m, theta, seed, dtype, np, torch):
    rng = np.random.default_rng(seed)
    q, _ = np.linalg.qr(rng.standard_normal((n, n)))
    mask = rng.binomial(1, theta, size=(n, m))
    coeff = mask * rng.standard_normal((n, m))
    y_np = q @ coeff
    return torch.tensor(y_np, dtype=dtype)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--n", type=int, default=6)
    parser.add_argument("--m", type=int, default=None)
    parser.add_argument("--theta", type=float, default=0.3)
    parser.add_argument("--mu", type=float, default=0.1)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--maxiter", type=int, default=50)
    parser.add_argument("--gtol", type=float, default=1e-6)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    n = args.n
    m = args.m or 10 * n * n
    device = torch.device("cpu")
    dtype = torch.float64

    y = build_data(n, m, args.theta, args.seed, dtype, np, torch)

    manifold = cdopt.manifold_torch.stiefel_torch((n, n), device=device, dtype=dtype)

    def obj_fun(x):
        scores = x.T @ y
        return args.mu * torch.mean(torch.log(torch.cosh(scores / args.mu)))

    problem_obj = cdopt.core.problem(manifold, obj_fun, beta="auto")
    started = time.time()
    result = sp.optimize.minimize(
        problem_obj.cdf_fun_vec_np,
        problem_obj.Xinit_vec_np,
        jac=problem_obj.cdf_grad_vec_np,
        method="L-BFGS-B",
        options={"maxiter": args.maxiter, "gtol": args.gtol},
    )
    elapsed = time.time() - started

    grad = problem_obj.cdf_grad_vec_np(result.x)
    feasibility = None
    try:
        x_tensor = torch.tensor(result.x, dtype=dtype, device=device).reshape(n, n)
        x_projected = manifold.Post_process(x_tensor)
        feasibility = float(manifold.Feas_eval(x_projected))
    except Exception as exc:  # noqa: BLE001 - keep run summary robust
        feasibility = f"unavailable: {type(exc).__name__}: {exc}"

    summary = {
        "example": "stiefel_dictionary_learning_torch_scipy",
        "solver": "scipy.optimize.minimize L-BFGS-B via CDOpt CDF callbacks",
        "success": bool(result.success),
        "status": int(result.status),
        "message": str(result.message),
        "fval": float(result.fun),
        "iterations": int(getattr(result, "nit", -1)),
        "function_evaluations": int(getattr(result, "nfev", -1)),
        "gradient_evaluations": int(getattr(result, "njev", -1)),
        "gradient_norm": float(np.linalg.norm(grad)),
        "feasibility": feasibility,
        "elapsed_seconds": elapsed,
        "parameters": {
            "n": n,
            "m": m,
            "theta": args.theta,
            "mu": args.mu,
            "seed": args.seed,
            "maxiter": args.maxiter,
            "gtol": args.gtol,
            "dtype": "torch.float64",
            "device": "cpu",
        },
        "versions": {
            "cdopt": getattr(cdopt, "__version__", None),
            "numpy": np.__version__,
            "scipy": sp.__version__,
            "torch": torch.__version__,
        },
        "paths": {
            "cdopt": getattr(cdopt, "__file__", None),
        },
    }

    results_dir = Path(args.results_dir)
    results_dir.mkdir(parents=True, exist_ok=True)
    out_path = results_dir / "solver_summary.json"
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {out_path}")


if __name__ == "__main__":
    main()
'''


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--output-dir",
        default=".local/cdopt-runs/dictionary_learning_torch_scipy",
        help="directory where run_dictionary_learning.py will be written",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_path = output_dir / "run_dictionary_learning.py"
    runner_path.write_text(textwrap.dedent(RUNNER))
    runner_path.chmod(0o755)
    print(runner_path)


if __name__ == "__main__":
    main()
