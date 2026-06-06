"""Problem-spec loading and solver routing primitives."""

from __future__ import annotations

from dataclasses import dataclass, field
import json
import re
from pathlib import Path
from typing import Any

import yaml


SDPT3_CLASSES = {
    "conic_sqlp",
    "semidefinite_program",
    "second_order_cone_program",
    "linear_cone_program",
    "linear_matrix_inequality",
}

CDOPT_CLASSES = {
    "riemannian",
    "manifold_optimization",
    "orthogonality_constrained",
    "stiefel",
    "sphere",
    "oblique",
    "grassmann",
    "generalized_stiefel",
    "hyperbolic",
    "symplectic_stiefel",
}

SUPPORTED_BACKENDS = {"auto", "sdpt3", "cdopt", "scipy", "existing"}
INPUT_TYPES = {
    "natural_language",
    "latex",
    "paper_excerpt",
    "repository_source",
    "solver_data",
    "structured_spec",
    "mixed",
}
MODELING_STATUSES = {"proposed", "confirmed", "needs_revision", "unknown"}


def slugify_problem_id(value: str) -> str:
    slug = re.sub(r"[^A-Za-z0-9_]+", "_", value.strip())
    slug = re.sub(r"_+", "_", slug).strip("_").lower()
    return slug or "optimization_problem"


@dataclass(frozen=True)
class OptimizationProblemSpec:
    """Normalized optimization problem spec used by helper scripts."""

    schema_version: int
    problem_id: str
    input_type: str
    problem_class: str
    domain: dict[str, Any] = field(default_factory=dict)
    objective: dict[str, Any] = field(default_factory=dict)
    variables: list[dict[str, Any]] = field(default_factory=list)
    data: dict[str, Any] = field(default_factory=dict)
    constraints: list[dict[str, Any]] = field(default_factory=list)
    solver_preferences: dict[str, Any] = field(default_factory=dict)
    modeling_layer: dict[str, Any] = field(default_factory=dict)
    review: dict[str, Any] = field(default_factory=dict)
    sdpt3: dict[str, Any] = field(default_factory=dict)
    cdopt: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_mapping(cls, raw: dict[str, Any]) -> "OptimizationProblemSpec":
        if not isinstance(raw, dict):
            raise ValueError("problem spec must be a mapping")

        missing = [key for key in ["schema_version", "problem_id", "input_type", "problem_class"] if key not in raw]
        if missing:
            raise ValueError(f"missing required field(s): {', '.join(missing)}")

        schema_version = int(raw["schema_version"])
        if schema_version != 1:
            raise ValueError(f"unsupported schema_version: {schema_version}")

        objective = raw.get("objective") or {}
        if not isinstance(objective, dict):
            raise ValueError("objective must be a mapping")
        sense = objective.get("sense", "unknown")
        if sense not in {"minimize", "maximize", "unknown"}:
            raise ValueError("objective.sense must be minimize, maximize, or unknown")

        input_type = str(raw["input_type"]).strip().lower()
        if input_type not in INPUT_TYPES:
            allowed = ", ".join(sorted(INPUT_TYPES))
            raise ValueError(f"input_type must be one of: {allowed}")

        variables = raw.get("variables") or []
        if not isinstance(variables, list):
            raise ValueError("variables must be a list")

        constraints = raw.get("constraints") or []
        if not isinstance(constraints, list):
            raise ValueError("constraints must be a list")

        review = _mapping(raw.get("review"), "review")
        modeling_status = str(review.get("modeling_status", "unknown")).lower()
        if modeling_status not in MODELING_STATUSES:
            allowed = ", ".join(sorted(MODELING_STATUSES))
            raise ValueError(f"review.modeling_status must be one of: {allowed}")
        review["modeling_status"] = modeling_status

        return cls(
            schema_version=schema_version,
            problem_id=slugify_problem_id(str(raw["problem_id"])),
            input_type=input_type,
            problem_class=str(raw["problem_class"]).strip().lower(),
            domain=_mapping(raw.get("domain"), "domain"),
            objective=objective,
            variables=variables,
            data=_mapping(raw.get("data"), "data"),
            constraints=constraints,
            solver_preferences=_mapping(raw.get("solver_preferences"), "solver_preferences"),
            modeling_layer=_mapping(raw.get("modeling_layer"), "modeling_layer"),
            review=review,
            sdpt3=_mapping(raw.get("sdpt3"), "sdpt3"),
            cdopt=_mapping(raw.get("cdopt"), "cdopt"),
            metadata=_mapping(raw.get("metadata"), "metadata"),
        )

    def preferred_backend(self) -> str:
        backend = str(self.solver_preferences.get("backend", "auto")).lower()
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"unsupported solver_preferences.backend: {backend}")
        return backend

    def route(self, solver_override: str | None = None) -> dict[str, Any]:
        backend = (solver_override or self.preferred_backend()).lower()
        if backend not in SUPPORTED_BACKENDS:
            raise ValueError(f"unsupported solver backend: {backend}")

        reasons: list[str] = []
        if backend == "auto":
            backend, reasons = self._auto_backend()
        else:
            reasons.append(f"user requested backend '{backend}'")

        if backend == "sdpt3":
            entrypoint = f"run_{self.problem_id}_sdpt3.m"
            execution_backend = str(self.solver_preferences.get("execution_backend", "matlab")).lower()
            command = _matlab_command(execution_backend, entrypoint)
            return {
                "problem_id": self.problem_id,
                "input_type": self.input_type,
                "solver": "sdpt3",
                "language": "matlab",
                "modeling_layer": self.solver_preferences.get("modeling_layer", "direct"),
                "modeling_status": self.review.get("modeling_status", "unknown"),
                "entrypoint": entrypoint,
                "candidate_command": command,
                "risk_level": "medium",
                "requires_approval": True,
                "requires_skills": ["matlab_environment_setup_skill", "matlab_runtime_skill"],
                "reason": "; ".join(reasons),
            }

        if backend == "cdopt":
            entrypoint = f"run_{self.problem_id}_cdopt.py"
            return {
                "problem_id": self.problem_id,
                "input_type": self.input_type,
                "solver": "cdopt",
                "language": "python",
                "modeling_layer": "direct",
                "modeling_status": self.review.get("modeling_status", "unknown"),
                "entrypoint": entrypoint,
                "candidate_command": f"conda run -n ai4math python {entrypoint}",
                "risk_level": "medium",
                "requires_approval": True,
                "requires_skills": ["environment_deployment_skill", "failure_diagnosis_skill"],
                "reason": "; ".join(reasons),
            }

        return {
            "problem_id": self.problem_id,
            "input_type": self.input_type,
            "solver": backend,
            "language": "unknown",
            "modeling_layer": self.solver_preferences.get("modeling_layer", "existing"),
            "modeling_status": self.review.get("modeling_status", "unknown"),
            "entrypoint": "",
            "candidate_command": "",
            "risk_level": "low",
            "requires_approval": False,
            "requires_skills": ["environment_deployment_skill"],
            "reason": "; ".join(reasons) or "no solver-specific route selected",
        }

    def _auto_backend(self) -> tuple[str, list[str]]:
        if self._has_direct_sdpt3_data():
            return "sdpt3", ["confirmed SQLP data includes a .mat file plus blk, At, C, and b"]
        if self.problem_class in CDOPT_CLASSES:
            return "cdopt", [f"problem_class '{self.problem_class}' is manifold-oriented"]
        if any("manifold" in str(item).lower() for item in self.constraints):
            return "cdopt", ["constraints mention a manifold"]
        if self.problem_class in SDPT3_CLASSES:
            return "existing", [
                f"problem_class '{self.problem_class}' needs confirmed SQLP data or reviewed MATLAB conic modeling"
            ]
        return "existing", ["no SDPT3/CDOpt signal was strong enough"]

    def _has_direct_sdpt3_data(self) -> bool:
        variables = self.sdpt3.get("data_variables", {})
        return bool(self.data.get("mat_file")) and {"blk", "At", "C", "b"} <= set(variables)


def _mapping(value: Any, field_name: str) -> dict[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, dict):
        raise ValueError(f"{field_name} must be a mapping")
    return value


def _matlab_command(execution_backend: str, entrypoint: str) -> str:
    if execution_backend == "octave":
        return f"octave --eval \"run('{entrypoint}')\""
    return f"matlab -batch \"run('{entrypoint}')\""


def load_problem_spec(path: str | Path) -> OptimizationProblemSpec:
    spec_path = Path(path)
    text = spec_path.read_text()
    if spec_path.suffix.lower() == ".json":
        raw = json.loads(text)
    else:
        raw = yaml.safe_load(text)
    return OptimizationProblemSpec.from_mapping(raw)


def route_problem_spec(path: str | Path, solver_override: str | None = None) -> dict[str, Any]:
    return load_problem_spec(path).route(solver_override=solver_override)
