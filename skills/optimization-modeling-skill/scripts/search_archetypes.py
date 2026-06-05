"""Search imported OptSkills archetype references."""

from __future__ import annotations

import argparse
from collections import Counter
import json
from pathlib import Path
import re
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LIBRARY_ROOT = ROOT / "references" / "optskills" / "skill_library"

STOPWORDS = {
    "a",
    "all",
    "an",
    "and",
    "are",
    "as",
    "be",
    "by",
    "for",
    "from",
    "in",
    "is",
    "of",
    "on",
    "or",
    "the",
    "to",
    "with",
}

SYNONYM_HINTS = {
    "tsp": {"traveling", "travelling", "salesman", "tour", "route", "subtour", "mtz"},
    "set_cover": {"cover", "coverage", "sets", "elements", "minimum", "required"},
    "transportation": {"ship", "shipping", "supplier", "customer", "warehouse", "demand", "capacity", "transport"},
    "network_flow": {"flow", "arc", "node", "source", "sink", "commodity", "network"},
    "assignment": {"assign", "assignment", "matching", "worker", "task", "bipartite"},
    "facility_location": {"facility", "location", "open", "serve", "coverage"},
    "scheduling": {"schedule", "job", "machine", "precedence", "makespan", "shop"},
    "portfolio": {"portfolio", "variance", "covariance", "return", "risk"},
}


def search_archetypes(query: str, limit: int = 10, library: str | None = None) -> list[dict[str, Any]]:
    """Return ranked OptSkills archetype references for a natural-language query."""

    query_terms = _token_counts(query)
    query_hints = _matched_hints(query_terms)
    results: list[dict[str, Any]] = []

    for library_dir in _library_dirs(library):
        for entry in _load_index(library_dir):
            path = library_dir / entry["path"]
            text = _entry_text(entry, path)
            score = _score_entry(query_terms, query_hints, text, entry)
            if score <= 0:
                continue
            results.append(
                {
                    "library": library_dir.name,
                    "skill_id": entry.get("skill_id", path.stem),
                    "title": entry.get("name", path.stem.replace("_", " ").title()),
                    "description": entry.get("description", ""),
                    "path": str(path.relative_to(ROOT)),
                    "score": score,
                }
            )

    results.sort(key=lambda item: (-item["score"], item["library"], item["path"]))
    return results[:limit]


def _library_dirs(library: str | None) -> list[Path]:
    if library:
        candidates = [LIBRARY_ROOT / library]
    else:
        candidates = sorted(path for path in LIBRARY_ROOT.iterdir() if path.is_dir())
    return [path for path in candidates if (path / "index.json").exists()]


def _load_index(library_dir: Path) -> list[dict[str, Any]]:
    payload = json.loads((library_dir / "index.json").read_text())
    skills = payload.get("skills", [])
    if not isinstance(skills, list):
        return []
    return [entry for entry in skills if isinstance(entry, dict) and entry.get("path")]


def _entry_text(entry: dict[str, Any], path: Path) -> str:
    parts = [
        str(entry.get("skill_id", "")),
        str(entry.get("name", "")),
        str(entry.get("description", "")),
    ]
    if path.exists():
        parts.append(path.read_text(errors="ignore")[:5000])
    return "\n".join(parts).lower()


def _token_counts(text: str) -> Counter[str]:
    tokens = re.findall(r"[a-zA-Z0-9_]+", text.lower())
    return Counter(token for token in tokens if token not in STOPWORDS and len(token) > 1)


def _matched_hints(query_terms: Counter[str]) -> set[str]:
    terms = set(query_terms)
    return {name for name, hint_terms in SYNONYM_HINTS.items() if terms & hint_terms}


def _score_entry(
    query_terms: Counter[str],
    query_hints: set[str],
    text: str,
    entry: dict[str, Any],
) -> int:
    entry_terms = _token_counts(text)
    score = sum(min(count, entry_terms.get(term, 0)) * 2 for term, count in query_terms.items())

    identity = " ".join(
        [
            str(entry.get("skill_id", "")),
            str(entry.get("name", "")),
            str(entry.get("path", "")),
        ]
    ).lower()
    for hint in query_hints:
        hint_tokens = hint.split("_")
        if hint in identity or any(token in identity for token in hint_tokens):
            score += 12

    if "min" in text and {"minimum", "minimize", "cost"} & set(query_terms):
        score += 2
    if "max" in text and {"maximum", "maximize", "profit"} & set(query_terms):
        score += 2
    return score


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--query", required=True, help="Natural-language optimization problem description")
    parser.add_argument("--limit", type=int, default=10, help="Maximum number of matches to return")
    parser.add_argument("--library", default=None, help="Optional OptSkills library directory name")
    parser.add_argument("--out", default=None, help="Optional JSON output path")
    args = parser.parse_args(argv)

    payload = {"query": args.query, "results": search_archetypes(args.query, args.limit, args.library)}
    text = json.dumps(payload, indent=2, sort_keys=True)
    if args.out:
        out_path = Path(args.out)
        out_path.parent.mkdir(parents=True, exist_ok=True)
        out_path.write_text(text + "\n")
    else:
        print(text)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
