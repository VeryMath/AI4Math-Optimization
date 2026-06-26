#!/usr/bin/env python3
"""Probe CDOpt-related Python packages without installing or running solvers."""

import argparse
import importlib
import importlib.util
import json
import os
import sys
from pathlib import Path

try:
    from importlib import metadata
except ImportError:  # pragma: no cover - Python 3.7 fallback
    import importlib_metadata as metadata


PACKAGES = ("cdopt", "torch", "numpy", "scipy", "jax", "flax")


def package_version(name):
    try:
        return metadata.version(name)
    except metadata.PackageNotFoundError:
        return None


def probe_package(name):
    spec = importlib.util.find_spec(name)
    if spec is None:
        return {
            "available": False,
            "version": None,
            "path": None,
            "error": "module not found",
        }

    try:
        module = importlib.import_module(name)
    except Exception as exc:  # noqa: BLE001 - report import failure details
        return {
            "available": False,
            "version": package_version(name),
            "path": getattr(spec, "origin", None),
            "error": f"{type(exc).__name__}: {exc}",
        }

    return {
        "available": True,
        "version": getattr(module, "__version__", None) or package_version(name),
        "path": getattr(module, "__file__", None),
        "error": None,
    }


def build_report():
    env_smoke_test = os.environ.get("CDOPT_SMOKE_TEST")
    if env_smoke_test:
        smoke_test = Path(env_smoke_test)
    else:
        smoke_test = Path.home() / "cdopt_manifold_tests" / "run_all_notebooks.py"
    packages = {name: probe_package(name) for name in PACKAGES}
    return {
        "python": sys.executable,
        "python_version": sys.version.split()[0],
        "packages": packages,
        "smoke_test": {
            "path": str(smoke_test),
            "exists": smoke_test.exists(),
        },
        "install_hint": "python3 -m pip install cdopt torch numpy scipy",
    }


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--json", action="store_true", help="print machine-readable JSON")
    args = parser.parse_args()

    report = build_report()
    if args.json:
        print(json.dumps(report, indent=2, sort_keys=True))
        return

    print(f"Python: {report['python']} ({report['python_version']})")
    for name, info in report["packages"].items():
        status = "ok" if info["available"] else "missing"
        version = info["version"] or "unknown"
        path = info["path"] or "-"
        print(f"{name}: {status}, version={version}, path={path}")
        if info["error"]:
            print(f"  error: {info['error']}")
    smoke = report["smoke_test"]
    print(f"smoke_test: exists={smoke['exists']}, path={smoke['path']}")
    if not report["packages"]["cdopt"]["available"]:
        print(f"install_hint: {report['install_hint']}")


if __name__ == "__main__":
    main()
