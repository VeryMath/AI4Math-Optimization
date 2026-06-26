#!/usr/bin/env python3
"""Write a tiny CPU-only CDOpt PyTorch constrained RNN/LSTM training runner."""

import argparse
import textwrap
from pathlib import Path


RUNNER = r'''#!/usr/bin/env python3
"""Tiny deterministic CDOpt PyTorch constrained RNN/LSTM training runner.

Mirrors the official single-layer RNN and bidirectional LSTM MNIST examples
but stays CPU-only, uses synthetic sequence batches, and reports
get_quad_penalty as a feasibility proxy.
"""

import argparse
import json
import time
from pathlib import Path

import cdopt
import numpy as np
import torch
import torch.nn as nn

from cdopt.manifold_torch import stiefel_torch
from cdopt.nn import LSTM_cdopt, RNN_cdopt, get_quad_penalty


class RNNClassifier(nn.Module):
    def __init__(self, batch_size, input_size, hidden_size, num_classes, penalty_param):
        super().__init__()
        self.batch_size = batch_size
        self.hidden_size = hidden_size
        self.rnn = RNN_cdopt(
            input_size,
            hidden_size,
            manifold_class=stiefel_torch,
            penalty_param=penalty_param,
        )
        self.head = nn.Linear(hidden_size, num_classes)

    def forward(self, x):
        # x: (batch, seq_len, input_size) -> (seq_len, batch, input_size)
        x = x.permute(1, 0, 2)
        hidden = torch.zeros(1, self.batch_size, self.hidden_size, device=x.device, dtype=x.dtype)
        _, hidden = self.rnn(x, hidden)
        logits = self.head(hidden.squeeze(0))
        return logits


class LSTMClassifier(nn.Module):
    def __init__(
        self,
        input_size,
        hidden_size,
        num_layers,
        num_classes,
        penalty_param,
        bidirectional=True,
    ):
        super().__init__()
        self.hidden_size = hidden_size
        self.num_layers = num_layers
        self.bidirectional = bidirectional
        self.lstm = LSTM_cdopt(
            input_size,
            hidden_size,
            num_layers,
            batch_first=True,
            bidirectional=bidirectional,
            manifold_class=stiefel_torch,
            penalty_param=penalty_param,
        )
        out_features = hidden_size * (2 if bidirectional else 1)
        self.head = nn.Linear(out_features, num_classes)

    def forward(self, x):
        batch = x.size(0)
        layers = self.num_layers * (2 if self.bidirectional else 1)
        hidden = torch.zeros(layers, batch, self.hidden_size, device=x.device, dtype=x.dtype)
        cell = torch.zeros(layers, batch, self.hidden_size, device=x.device, dtype=x.dtype)
        output, _ = self.lstm(x, (hidden, cell))
        logits = self.head(output[:, -1, :])
        return logits


def build_model(cell_type, args, device, dtype):
    if cell_type == "rnn":
        return RNNClassifier(
            args.batch,
            args.input_size,
            args.hidden_size,
            args.num_classes,
            args.penalty,
        ).to(device=device, dtype=dtype)
    return LSTMClassifier(
        args.input_size,
        args.hidden_size,
        args.num_layers,
        args.num_classes,
        args.penalty,
        bidirectional=args.bidirectional,
    ).to(device=device, dtype=dtype)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--cell-type", choices=("rnn", "lstm"), default="rnn")
    parser.add_argument("--batch", type=int, default=16)
    parser.add_argument("--seq-len", type=int, default=8)
    parser.add_argument("--input-size", type=int, default=12)
    parser.add_argument("--hidden-size", type=int, default=16)
    parser.add_argument("--num-layers", type=int, default=2)
    parser.add_argument("--num-classes", type=int, default=3)
    parser.add_argument("--bidirectional", action="store_true", default=True)
    parser.add_argument("--no-bidirectional", action="store_false", dest="bidirectional")
    parser.add_argument("--steps", type=int, default=30)
    parser.add_argument("--lr", type=float, default=0.05)
    parser.add_argument("--penalty", type=float, default=0.2)
    parser.add_argument("--seed", type=int, default=0)
    parser.add_argument("--results-dir", default="results")
    args = parser.parse_args()

    torch.manual_seed(args.seed)
    rng = np.random.default_rng(args.seed)
    device = torch.device("cpu")
    dtype = torch.float64

    x = torch.tensor(
        rng.standard_normal((args.batch, args.seq_len, args.input_size)), dtype=dtype
    )
    y = torch.tensor(
        rng.integers(0, args.num_classes, size=(args.batch,)), dtype=torch.long
    )

    model = build_model(args.cell_type, args, device, dtype)
    optimizer = torch.optim.SGD(model.parameters(), lr=args.lr)
    criterion = nn.CrossEntropyLoss()

    started = time.time()
    initial_loss = None
    final_loss = None
    error = None
    try:
        for step in range(args.steps):
            optimizer.zero_grad()
            logits = model(x)
            loss = criterion(logits, y) + get_quad_penalty(model)
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
        "example": f"constrained_{args.cell_type}_torch",
        "framework": f"pytorch + cdopt.nn {args.cell_type.upper()}_cdopt",
        "success": error is None,
        "error": error,
        "initial_loss": initial_loss,
        "final_loss": final_loss,
        "final_quad_penalty": feasibility,
        "steps": args.steps,
        "elapsed_seconds": elapsed,
        "parameters": {
            "cell_type": args.cell_type,
            "batch": args.batch,
            "seq_len": args.seq_len,
            "input_size": args.input_size,
            "hidden_size": args.hidden_size,
            "num_layers": args.num_layers,
            "num_classes": args.num_classes,
            "bidirectional": args.bidirectional if args.cell_type == "lstm" else None,
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
        default=".local/cdopt-runs/constrained_rnn_torch",
        help="directory where run_constrained_rnn.py will be written",
    )
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)
    runner_path = output_dir / "run_constrained_rnn.py"
    runner_path.write_text(textwrap.dedent(RUNNER))
    runner_path.chmod(0o755)
    print(runner_path)


if __name__ == "__main__":
    main()
