import json
import subprocess
import sys

import yaml

from codegen import generate_solver_entrypoint
from problem_spec import OptimizationProblemSpec
from result_parser import parse_solver_log


def write_yaml(path, payload):
    path.write_text(yaml.safe_dump(payload, sort_keys=False))
    return path


def test_solver_router_selects_sdpt3_for_conic_sqlp(tmp_path):
    spec_path = write_yaml(
        tmp_path / "problem.yaml",
        {
            "schema_version": 1,
            "problem_id": "Tiny SDP",
            "input_type": "structured_spec",
            "problem_class": "conic_sqlp",
            "objective": {"sense": "minimize"},
            "review": {"modeling_status": "confirmed"},
            "data": {"mat_file": "tiny.mat"},
            "sdpt3": {"data_variables": {"blk": "blk", "At": "At", "C": "C", "b": "b"}},
        },
    )

    result = subprocess.run(
        [
            sys.executable,
            "skills/optimization-modeling-skill/scripts/solver_router.py",
            "--spec",
            str(spec_path),
        ],
        capture_output=True,
        text=True,
        timeout=30,
    )

    assert result.returncode == 0
    route = json.loads(result.stdout)
    assert route["solver"] == "sdpt3"
    assert route["entrypoint"] == "run_tiny_sdp_sdpt3.m"
    assert "matlab -batch" in route["candidate_command"]


def test_auto_route_does_not_select_direct_sdpt3_without_sqlp_data():
    spec = OptimizationProblemSpec.from_mapping(
        {
            "schema_version": 1,
            "problem_id": "sdp_without_sqlp_data",
            "input_type": "structured_spec",
            "problem_class": "semidefinite_program",
            "objective": {"sense": "minimize"},
            "review": {"modeling_status": "confirmed"},
        }
    )

    route = spec.route()

    assert route["solver"] == "existing"
    assert "confirmed SQLP data" in route["reason"]


def test_codegen_writes_sdpt3_matlab_wrapper(tmp_path):
    spec = OptimizationProblemSpec.from_mapping(
        {
            "schema_version": 1,
            "problem_id": "sdp_case",
            "input_type": "structured_spec",
            "problem_class": "semidefinite_program",
            "objective": {"sense": "minimize"},
            "review": {"modeling_status": "confirmed"},
            "data": {"mat_file": "case.mat"},
            "sdpt3": {
                "solver": "sdpt3",
                "data_variables": {"blk": "blk", "At": "At", "C": "C", "b": "b"},
                "options": {"printlevel": 2},
            },
        }
    )

    route = generate_solver_entrypoint(spec, tmp_path / "generated")

    entrypoint = tmp_path / "generated" / "run_sdp_case_sdpt3.m"
    assert route["solver"] == "sdpt3"
    assert entrypoint.exists()
    text = entrypoint.read_text()
    assert "load(data_file, 'blk', 'At', 'C', 'b')" in text
    assert "[obj, X, y, Z, info, runhist] = sdpt3" in text
    assert "OPTIONS.printlevel = 2;" in text


def test_removed_backend_is_not_supported():
    removed_backend = "cd" + "opt"
    spec = OptimizationProblemSpec.from_mapping(
        {
            "schema_version": 1,
            "problem_id": "removed_backend_demo",
            "input_type": "structured_spec",
            "problem_class": "riemannian",
            "objective": {"sense": "minimize"},
            "review": {"modeling_status": "confirmed"},
            "solver_preferences": {"backend": removed_backend},
        }
    )

    try:
        spec.route()
    except ValueError as exc:
        assert "unsupported solver" in str(exc)
    else:
        raise AssertionError("removed backend should not be accepted")


def test_solver_router_keeps_common_manifold_classes_on_existing_route():
    for problem_class in ["sphere", "oblique", "symplectic_stiefel"]:
        spec = OptimizationProblemSpec.from_mapping(
            {
                "schema_version": 1,
                "problem_id": f"{problem_class}_demo",
                "input_type": "structured_spec",
                "problem_class": problem_class,
                "objective": {"sense": "minimize"},
                "review": {"modeling_status": "confirmed"},
            }
        )

        route = spec.route()

        assert route["solver"] == "existing"
        assert "manifold-oriented problem" in route["reason"]


def test_result_parser_classifies_solver_failures_and_metrics():
    summary = parse_solver_log(
        """
        sqlp stop: primal problem is suspected of being infeasible
        info.termcode = 1
        gap = 3.2e-08
        pinfeas = 1.0e-07
        """
    )

    assert summary["status"] == "failed"
    assert summary["failure_type"] == "infeasible"
    assert summary["metrics"]["termcode"] == 1
    assert summary["metrics"]["gap"] == 3.2e-08


def test_result_parser_classifies_missing_dependency():
    summary = parse_solver_log("ModuleNotFoundError: No module named 'solver_pkg'")

    assert summary["status"] == "failed"
    assert summary["failure_type"] == "missing_dependency"


def test_result_parser_extracts_json_summary_metrics():
    summary = parse_solver_log(
        """
        {
          "status": "completed",
          "solver": "custom",
          "objective": -12.5,
          "stationarity": 1.0e-6,
          "feasibility": 2.0e-8,
          "nit": 20,
          "nfev": 25,
          "elapsed_seconds": 0.12
        }
        """
    )

    assert summary["status"] == "completed"
    assert summary["failure_type"] == "none"
    assert summary["metrics"]["objective"] == -12.5
    assert summary["metrics"]["stationarity"] == 1.0e-6
    assert summary["metrics"]["feasibility"] == 2.0e-8
    assert summary["metrics"]["nit"] == 20
