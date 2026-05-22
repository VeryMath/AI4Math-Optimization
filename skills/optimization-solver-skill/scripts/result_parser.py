"""Parse solver logs into compact optimization-solver summaries."""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path
from typing import Any


FAILURE_PATTERNS = [
    ("missing_dependency", re.compile(r"ModuleNotFoundError|No module named|Undefined function|not found", re.I)),
    ("missing_mex", re.compile(r"mex|invalid mex|cannot open shared object|dlopen", re.I)),
    ("infeasible", re.compile(r"primal infeasible|dual infeasible|suspected .* infeasible", re.I)),
    ("numerical_failure", re.compile(r"Schur complement|lack of progress|short step|not positive definite|ill[- ]condition", re.I)),
    ("timeout", re.compile(r"timed out|timeout|killed", re.I)),
    ("shape_or_data_error", re.compile(r"dimension mismatch|shape mismatch|Index exceeds|field .* does not exist", re.I)),
]

METRIC_PATTERNS = {
    "termcode": re.compile(r"termcode\D+(-?\d+)", re.I),
    "gap": re.compile(r"\bgap\D+([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", re.I),
    "pinfeas": re.compile(r"pinfeas\D+([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", re.I),
    "dinfeas": re.compile(r"dinfeas\D+([+-]?\d+(?:\.\d+)?(?:e[+-]?\d+)?)", re.I),
}


def parse_solver_log(text: str) -> dict[str, Any]:
    json_summary = _parse_json_summary(text)
    if json_summary:
        return json_summary

    failure_type = "none"
    evidence = ""
    for candidate, pattern in FAILURE_PATTERNS:
        match = pattern.search(text)
        if match:
            failure_type = candidate
            evidence = match.group(0)
            break

    metrics: dict[str, Any] = {}
    for name, pattern in METRIC_PATTERNS.items():
        match = pattern.search(text)
        if match:
            metrics[name] = _coerce_number(match.group(1))

    status = "failed" if failure_type != "none" else "unknown"
    if re.search(r"success|optimal|completed", text, re.I) and failure_type == "none":
        status = "completed"

    return {
        "status": status,
        "failure_type": failure_type,
        "evidence": evidence,
        "metrics": metrics,
    }


def _parse_json_summary(text: str) -> dict[str, Any] | None:
    stripped = text.strip()
    start = stripped.find("{")
    end = stripped.rfind("}")
    if start < 0 or end < start:
        return None

    try:
        payload = json.loads(stripped[start : end + 1])
    except json.JSONDecodeError:
        return None
    if not isinstance(payload, dict) or "status" not in payload:
        return None

    metrics: dict[str, Any] = {}
    for name in ["objective", "stationarity", "feasibility", "nit", "nfev", "elapsed_seconds"]:
        if name in payload:
            metrics[name] = payload[name]

    status = str(payload.get("status", "unknown"))
    success = payload.get("success")
    failure_type = "none" if status == "completed" or success is True else "solver_failure"
    if status == "failed" and payload.get("message"):
        evidence = str(payload["message"])
    else:
        evidence = ""

    return {
        "status": status,
        "failure_type": failure_type,
        "evidence": evidence,
        "metrics": metrics,
    }


def _coerce_number(value: str) -> int | float | str:
    try:
        if re.fullmatch(r"[+-]?\d+", value):
            return int(value)
        return float(value)
    except ValueError:
        return value


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--log", required=True, help="Solver stdout/stderr log")
    parser.add_argument("--out", default=None, help="Optional JSON summary path")
    args = parser.parse_args()

    summary = parse_solver_log(Path(args.log).read_text())
    payload = json.dumps(summary, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n")
    print(payload)


if __name__ == "__main__":
    main()
