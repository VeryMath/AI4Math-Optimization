#!/usr/bin/env python3
"""Write a tiny CPU-only CDOpt Stiefel dictionary-learning runner."""

import argparse
import math
import textwrap
from pathlib import Path


RUNNER = r'''#!/usr/bin/env python3
"""Tiny deterministic CDOpt Stiefel dictionary-learning example."""

import argparse
import json
import math
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

    if args.n < 1 or args.n > 512:
        parser.error("--n must be between 1 and 512")
    if args.m is not None and not 1 <= args.m <= 10_000_000:
        parser.error("--m must be between 1 and 10000000")
    if not math.isfinite(args.theta) or not 0.0 <= args.theta <= 1.0:
        parser.error("--theta must be finite and between 0 and 1")
    if not math.isfinite(args.mu) or args.mu <= 0.0:
        parser.error("--mu must be finite and greater than 0")
    if args.maxiter < 1 or args.maxiter > 100_000:
        parser.error("--maxiter must be between 1 and 100000")
    if not math.isfinite(args.gtol) or args.gtol <= 0.0:
        parser.error("--gtol must be finite and greater than 0")
    results_dir = Path(args.results_dir)
    if results_dir.exists() and (results_dir.is_symlink() or not results_dir.is_dir()):
        parser.error("--results-dir must be a real directory")

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

    execution_success = bool(result.success) and all(
        math.isfinite(value) for value in (float(result.fun), float(np.linalg.norm(grad)))
    )
    verification_success = isinstance(feasibility, float) and math.isfinite(feasibility)
    summary = {
        "example": "stiefel_dictionary_learning_torch_scipy",
        "solver": "scipy.optimize.minimize L-BFGS-B via CDOpt CDF callbacks",
        "success": execution_success and verification_success,
        "execution": {"success": execution_success, "stage": "solver"},
        "solver": {"success": bool(result.success), "status": int(result.status)},
        "verification": {"success": verification_success, "metric": "manifold.Feas_eval"},
        "mathematical_conclusion": "not_assessed",
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

    results_dir.mkdir(parents=True, exist_ok=True)
    if results_dir.is_symlink():
        raise RuntimeError("results directory became a symlink")
    out_path = results_dir / "solver_summary.json"
    if out_path.is_symlink():
        raise RuntimeError("refusing to replace symlinked solver_summary.json")
    out_path.write_text(json.dumps(summary, indent=2, sort_keys=True))
    print(json.dumps(summary, indent=2, sort_keys=True))
    print(f"wrote {out_path}")
    return 0 if summary["success"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
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
    if output_dir.is_symlink() or (output_dir.exists() and not output_dir.is_dir()):
        parser.error("--output-dir must be a real directory")
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_path = output_dir / "run_dictionary_learning.py"
    if runner_path.is_symlink() or (runner_path.exists() and not runner_path.is_file()):
        parser.error("refusing to replace an unsafe generated runner path")
    runner_path.write_text(textwrap.dedent(RUNNER))
    runner_path.chmod(0o755)
    print(runner_path)


if __name__ == "__main__":
    main()
