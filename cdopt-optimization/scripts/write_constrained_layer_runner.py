#!/usr/bin/env python3
"""Write a tiny CPU-only CDOpt PyTorch constrained-layer training runner."""

import argparse
import textwrap
from pathlib import Path


RUNNER = r'''#!/usr/bin/env python3
"""Tiny deterministic CDOpt PyTorch Stiefel-constrained-layer training runner.

This mirrors the official LeNet orthogonal-kernel example
(https://cdopt.github.io/examples/LeNet_orth.html) but stays CPU-only, uses a
small synthetic classification batch instead of MNIST, and reports the
constraint-dissolving quadratic penalty as a feasibility proxy.
"""

import argparse
import json
import time
from pathlib import Path

import cdopt
import numpy as np
import torch
import torch.nn as nn
import torch.nn.functional as F

from cdopt.manifold_torch import stiefel_torch
from cdopt.nn.modules import Linear_cdopt, get_quad_penalty


class Net(nn.Module):
    def __init__(self, in_features, hidden_features, num_classes, penalty_param):
        super().__init__()
        # Pass the manifold CLASS (not an instance); the constrained weight is
        # kept close to the Stiefel manifold via the dissolved quadratic penalty.
        self.constrained = Linear_cdopt(
            in_features,
            hidden_features,
            manifold_class=stiefel_torch,
            penalty_param=penalty_param,
        )
        self.head = nn.Linear(hidden_features, num_classes)

    def forward(self, x):
        x = F.relu(self.constrained(x))
        return F.log_softmax(self.head(x), dim=1)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--in-features", type=int, default=8)
    parser.add_argument("--hidden-features", type=int, default=16)
    parser.add_argument("--num-classes", type=int, default=3)
    parser.add_argument("--batch", type=int, default=32)
    parser.add_argument("--steps", type=int, default=50)
    parser.add_argument("--lr", type=float, default=0.1)
    parser.add_argument("--penalty", type=float, default=0.05)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device("cpu")
    dtype = torch.float64

    x = torch.tensor(
        rng.standard_normal((args.batch, args.in_features)), dtype=dtype
    )
    y = torch.tensor(
        rng.integers(0, args.num_classes, size=(args.batch,)), dtype=torch.long
    )

    model = Net(
        args.in_features, args.hidden_features, args.num_classes, args.penalty
    ).to(device=device, dtype=dtype)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)

    started = time.time()
    initial_loss = None
    final_loss = None
    error = None
    try:
        for step in range(args.steps):
            optimizer.zero_grad()
            logits = model(x)
            loss = F.nll_loss(logits, y) + get_quad_penalty(model)
            loss.backward()
            optimizer.step()
            if step == 0:
                initial_loss = float(loss.item())
            final_loss = float(loss.item())
    except Exception as exc:  # noqa: BLE001 - keep run summary robust
        error = f"{type(exc).__name__}: {exc}"
    elapsed = time.time() - started

    feasibility = None
    try:
        feasibility = float(get_quad_penalty(model).item())
    except Exception as exc:  # noqa: BLE001 - keep run summary robust
        feasibility = f"unavailable: {type(exc).__name__}: {exc}"

    summary = {
        "example": "lenet_style_stiefel_constrained_layer_torch",
        "framework": "pytorch + cdopt.nn constraint-dissolving layer",
        "success": error is None,
        "error": error,
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "final_quad_penalty": feasibility,
        "steps": args.steps,
        "elapsed_seconds": elapsed,
        "parameters": {
            "in_features": args.in_features,
            "hidden_features": args.hidden_features,
            "num_classes": args.num_classes,
            "batch": args.batch,
            "lr": args.lr,
            "penalty_param": args.penalty,
            "seed": args.seed,
            "dtype": "torch.float64",
            "device": "cpu",
        },
        "versions": {
            "cdopt": getattr(cdopt, "__version__", None),
            "numpy": np.__version__,
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
        default=".local/cdopt-runs/constrained_layer_torch",
        help="directory where run_constrained_layer.py will be written",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_path = output_dir / "run_constrained_layer.py"
    runner_path.write_text(textwrap.dedent(RUNNER))
    runner_path.chmod(0o755)
    print(runner_path)


if __name__ == "__main__":
    main()
