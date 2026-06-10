"""Route a structured optimization problem spec to a solver backend."""

from __future__ import annotations

import argparse
import json
from pathlib import Path
import sys

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parent))
    from problem_spec import load_problem_spec
else:
    from .problem_spec import load_problem_spec


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--spec", required=True, help="YAML or JSON optimization problem spec")
    parser.add_argument("--solver", default=None, help="Optional solver override: sdpt3, scipy, existing")
    parser.add_argument("--out", default=None, help="Optional JSON route output path")
    args = parser.parse_args()

    spec = load_problem_spec(args.spec)
    route = spec.route(solver_override=args.solver)
    payload = json.dumps(route, indent=2, sort_keys=True)

    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(payload + "\n")

    print(payload)


if __name__ == "__main__":
    main()
