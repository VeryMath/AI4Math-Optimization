from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
import tempfile
import types
import unittest
from unittest import mock
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
CURATION_PACKAGE = ROOT / "skills" / "AI4Math-Optimization" / "osqp-solver"
UPSTREAM_PACKAGE = ROOT / "skills" / "osqp-solver"
PACKAGE = CURATION_PACKAGE if CURATION_PACKAGE.is_dir() else UPSTREAM_PACKAGE
SOLVER = PACKAGE / "scripts" / "solve_qp.py"
ENVIRONMENT = PACKAGE / "scripts" / "check_osqp_environment.py"
FEASIBLE = PACKAGE / "references" / "feasible-example.json"
PRIMAL_INFEASIBLE = PACKAGE / "references" / "primal-infeasible-example.json"
DUAL_INFEASIBLE = PACKAGE / "references" / "dual-infeasible-example.json"

HAS_NUMPY = importlib.util.find_spec("numpy") is not None
HAS_OSQP_STACK = all(
    importlib.util.find_spec(module) is not None
    for module in ("osqp", "numpy", "scipy")
)


def load_script_module(name: str, path: Path) -> Any:
    spec = importlib.util.spec_from_file_location(name, path)
    if spec is None or spec.loader is None:
        raise RuntimeError(f"cannot import {path}")
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SOLVER_MODULE = load_script_module("osqp_solver_release_gate", SOLVER)
ENVIRONMENT_MODULE = load_script_module(
    "osqp_environment_release_gate", ENVIRONMENT
)


class OsqpSolverSkillTests(unittest.TestCase):
    def run_json(self, *args: str) -> tuple[subprocess.CompletedProcess[str], dict]:
        result = subprocess.run(
            [sys.executable, *args],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        stream = result.stdout if result.stdout.strip() else result.stderr
        return result, json.loads(stream)

    def assert_single_json_document(self, stream: str) -> dict:
        self.assertTrue(stream.strip(), "expected a JSON document")
        document = json.loads(stream)
        self.assertIsInstance(document, dict)
        return document

    def write_problem(
        self, directory: str, problem: dict[str, Any], name: str = "problem.json"
    ) -> Path:
        path = Path(directory) / name
        path.write_text(json.dumps(problem), encoding="utf-8")
        return path

    @staticmethod
    def scalar_qp(**overrides: Any) -> dict[str, Any]:
        problem: dict[str, Any] = {
            "name": "scalar-qp",
            "P": [[1.0]],
            "q": [0.0],
            "A": [],
            "l": [],
            "u": [],
        }
        problem.update(overrides)
        return problem

    def test_skill_has_expected_resources_and_no_placeholders(self) -> None:
        expected = (
            PACKAGE / "README.md",
            PACKAGE / "README.zh-CN.md",
            PACKAGE / "SKILL.md",
            PACKAGE / "requirements-test.txt",
            PACKAGE / "agents" / "openai.yaml",
            ENVIRONMENT,
            SOLVER,
            PACKAGE / "references" / "python-api.md",
            PACKAGE / "references" / "verification.md",
            PACKAGE / "references" / "citation.md",
            FEASIBLE,
            PRIMAL_INFEASIBLE,
            DUAL_INFEASIBLE,
        )
        for path in expected:
            with self.subTest(path=path):
                self.assertTrue(path.is_file())
                self.assertNotIn("TODO", path.read_text(encoding="utf-8"))

    def test_environment_probe_is_machine_readable_without_dependencies(self) -> None:
        result, report = self.run_json(str(ENVIRONMENT), "--json")
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual({"osqp", "numpy", "scipy"}, set(report["packages"]))
        self.assertEqual(
            (
                all(item["available"] for item in report["packages"].values())
                and report["packages"]["osqp"]["compatible"]
            ),
            report["ready"],
        )
        self.assertIn("osqp>=1", report["install_hint"])

    def test_release_dependency_matches_runtime_version_gate(self) -> None:
        requirement = (PACKAGE / "requirements-test.txt").read_text(
            encoding="utf-8"
        )
        self.assertEqual("osqp>=1,<2", requirement.strip())
        self.assertEqual(requirement.strip(), SOLVER_MODULE.OSQP_REQUIREMENT)
        self.assertEqual(requirement.strip(), ENVIRONMENT_MODULE.OSQP_REQUIREMENT)

    def test_environment_probe_marks_unsupported_osqp_versions_not_ready(self) -> None:
        base = {
            "available": True,
            "path": "/isolated/site-packages/package.py",
            "error": None,
        }
        for version in ("0.6.3", "2.0.0"):
            packages = {
                "osqp": {**base, "version": version},
                "numpy": {**base, "version": "2.0.0"},
                "scipy": {**base, "version": "1.14.0"},
            }
            with self.subTest(version=version), mock.patch.object(
                ENVIRONMENT_MODULE,
                "probe_package",
                side_effect=lambda name, reports=packages: dict(reports[name]),
            ):
                report = ENVIRONMENT_MODULE.build_report()
                self.assertFalse(report["ready"])
                self.assertFalse(report["packages"]["osqp"]["compatible"])

    def test_environment_probe_accepts_supported_osqp_major(self) -> None:
        base = {
            "available": True,
            "path": "/isolated/site-packages/package.py",
            "error": None,
        }
        packages = {
            "osqp": {**base, "version": "1.1.3"},
            "numpy": {**base, "version": "2.0.0"},
            "scipy": {**base, "version": "1.14.0"},
        }
        with mock.patch.object(
            ENVIRONMENT_MODULE,
            "probe_package",
            side_effect=lambda name: dict(packages[name]),
        ):
            report = ENVIRONMENT_MODULE.build_report()
        self.assertTrue(report["ready"])
        self.assertTrue(report["packages"]["osqp"]["compatible"])

    def test_runtime_rejects_unsupported_osqp_major_without_solving(self) -> None:
        fake_numpy = types.ModuleType("numpy")
        fake_osqp = types.ModuleType("osqp")
        fake_osqp.__version__ = "0.6.3"
        fake_scipy = types.ModuleType("scipy")
        fake_scipy.sparse = object()
        with mock.patch.dict(
            sys.modules,
            {
                "numpy": fake_numpy,
                "osqp": fake_osqp,
                "scipy": fake_scipy,
            },
        ):
            with self.assertRaises(SOLVER_MODULE.DependencyError):
                SOLVER_MODULE.load_numeric_stack()

    def test_runtime_accepts_supported_osqp_major_without_solving(self) -> None:
        fake_numpy = types.ModuleType("numpy")
        fake_osqp = types.ModuleType("osqp")
        fake_osqp.__version__ = "1.1.3"
        fake_scipy = types.ModuleType("scipy")
        fake_scipy.sparse = object()
        with mock.patch.dict(
            sys.modules,
            {
                "numpy": fake_numpy,
                "osqp": fake_osqp,
                "scipy": fake_scipy,
            },
        ):
            numerical_stack = SOLVER_MODULE.load_numeric_stack()
        self.assertIs(fake_numpy, numerical_stack[0])
        self.assertIs(fake_osqp, numerical_stack[1])
        self.assertIs(fake_scipy.sparse, numerical_stack[2])

    def test_inaccurate_statuses_require_explicit_acceptance(self) -> None:
        expected_payloads = {
            2: "solution",
            4: "primal_certificate",
            6: "dual_certificate",
        }
        for status_value, payload_kind in expected_payloads.items():
            with self.subTest(status_value=status_value):
                _, inaccurate, observed_payload = SOLVER_MODULE.STATUS_BY_VALUE[
                    status_value
                ]
                self.assertTrue(inaccurate)
                self.assertEqual(payload_kind, observed_payload)
                self.assertFalse(
                    SOLVER_MODULE._payload_is_accepted(
                        payload_kind, True, inaccurate, False
                    )
                )
                self.assertTrue(
                    SOLVER_MODULE._payload_is_accepted(
                        payload_kind, True, inaccurate, True
                    )
                )
                self.assertFalse(
                    SOLVER_MODULE._payload_is_accepted(
                        payload_kind, False, inaccurate, True
                    )
                )

    def test_examples_pass_dependency_free_structural_validation(self) -> None:
        for example in (FEASIBLE, PRIMAL_INFEASIBLE, DUAL_INFEASIBLE):
            with self.subTest(example=example.name):
                result, report = self.run_json(
                    str(SOLVER), str(example), "--validate-only"
                )
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertTrue(report["valid"])
                self.assertTrue(report["problem"]["structural_checks"]["symmetric_P"])

    def test_invalid_nonsymmetric_P_is_rejected(self) -> None:
        problem = {
            "P": [[1.0, 2.0], [0.0, 1.0]],
            "q": [0.0, 0.0],
            "A": [],
            "l": [],
            "u": [],
        }
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "invalid.json"
            path.write_text(json.dumps(problem), encoding="utf-8")
            result, report = self.run_json(
                str(SOLVER), str(path), "--validate-only"
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("input", report["error"]["kind"])
        self.assertIn("symmetric", report["error"]["message"])

    def test_near_symmetric_P_is_canonicalized_once(self) -> None:
        asymmetry = 5e-11
        problem = SOLVER_MODULE.validate_problem(
            {
                "P": [[2.0, asymmetry], [0.0, 1.0]],
                "q": [0.0, 0.0],
                "A": [],
                "l": [],
                "u": [],
            }
        )
        self.assertAlmostEqual(
            problem["P"][0][1], problem["P"][1][0], places=18
        )
        self.assertAlmostEqual(asymmetry / 2.0, problem["P"][0][1], places=18)
        self.assertTrue(problem["structural_checks"]["P_canonicalized"])

    def test_unknown_top_level_field_is_rejected(self) -> None:
        problem = self.scalar_qp(typo_field="silently ignored")
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_problem(directory, problem)
            result, report = self.run_json(
                str(SOLVER), str(path), "--validate-only"
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("input", report["error"]["kind"])

    def test_duplicate_json_object_key_is_rejected(self) -> None:
        duplicate = (
            '{"P":[[1.0]],"q":[0.0],"q":[1.0],'
            '"A":[],"l":[],"u":[]}'
        )
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "duplicate-key.json"
            path.write_text(duplicate, encoding="utf-8")
            result, report = self.run_json(
                str(SOLVER), str(path), "--validate-only"
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("input", report["error"]["kind"])
        self.assertIn("duplicate", report["error"]["message"].lower())

    def test_unknown_solver_setting_is_rejected(self) -> None:
        problem = self.scalar_qp(settings={"typo_setting": 1})
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_problem(directory, problem)
            result, report = self.run_json(
                str(SOLVER), str(path), "--validate-only"
            )
        self.assertEqual(2, result.returncode)
        self.assertEqual("", result.stdout)
        self.assertEqual("input", report["error"]["kind"])

    def test_invalid_solver_setting_value_is_rejected(self) -> None:
        invalid_settings = (
            {"eps_abs": -1.0},
            {"max_iter": 1.5},
            {"polishing": 1},
        )
        for settings in invalid_settings:
            with self.subTest(settings=settings), tempfile.TemporaryDirectory() as directory:
                path = self.write_problem(
                    directory, self.scalar_qp(settings=settings)
                )
                result, report = self.run_json(
                    str(SOLVER), str(path), "--validate-only"
                )
                self.assertEqual(2, result.returncode)
                self.assertEqual("", result.stdout)
                self.assertEqual("input", report["error"]["kind"])

    def test_verbose_true_is_rejected_and_false_is_retained(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            true_path = self.write_problem(
                directory,
                self.scalar_qp(settings={"verbose": True}),
                "verbose-true.json",
            )
            result, report = self.run_json(
                str(SOLVER), str(true_path), "--validate-only"
            )
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual("input", report["error"]["kind"])

            false_path = self.write_problem(
                directory,
                self.scalar_qp(settings={"verbose": False}),
                "verbose-false.json",
            )
            validated = SOLVER_MODULE.load_problem(false_path)
            self.assertIs(False, validated["settings"]["verbose"])

    def test_success_and_error_streams_each_contain_exactly_one_json_document(
        self,
    ) -> None:
        success = subprocess.run(
            [sys.executable, str(SOLVER), str(FEASIBLE), "--validate-only"],
            cwd=ROOT,
            text=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            check=False,
        )
        self.assertEqual(0, success.returncode, success.stderr)
        self.assertEqual("", success.stderr)
        success_report = self.assert_single_json_document(success.stdout)
        self.assertTrue(success_report["valid"])

        with tempfile.TemporaryDirectory() as directory:
            invalid_path = self.write_problem(
                directory, self.scalar_qp(settings={"verbose": True})
            )
            failure = subprocess.run(
                [sys.executable, str(SOLVER), str(invalid_path), "--validate-only"],
                cwd=ROOT,
                text=True,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                check=False,
            )
        self.assertEqual(2, failure.returncode)
        self.assertEqual("", failure.stdout)
        error_report = self.assert_single_json_document(failure.stderr)
        self.assertEqual("input", error_report["error"]["kind"])

    def test_input_cannot_also_be_output_and_original_is_preserved(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = self.write_problem(directory, self.scalar_qp())
            original = path.read_bytes()
            result, report = self.run_json(
                str(SOLVER),
                str(path),
                "--validate-only",
                "--output",
                str(path),
            )
            self.assertEqual(2, result.returncode)
            self.assertEqual("", result.stdout)
            self.assertEqual("input", report["error"]["kind"])
            self.assertEqual(original, path.read_bytes())

    def test_distinct_output_is_atomically_replaced_with_report(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            input_path = self.write_problem(directory, self.scalar_qp())
            output_path = Path(directory) / "result.json"
            output_path.write_text("stale", encoding="utf-8")
            result, report = self.run_json(
                str(SOLVER),
                str(input_path),
                "--validate-only",
                "--output",
                str(output_path),
            )
            self.assertEqual(0, result.returncode, result.stderr)
            self.assertEqual(report, json.loads(output_path.read_text(encoding="utf-8")))
            self.assertEqual([], list(Path(directory).glob(".result.json.*.tmp")))

    def test_dense_variable_guard_rejects_before_numerical_solve(self) -> None:
        problem = {
            "P": [[1.0, 0.0], [0.0, 1.0]],
            "q": [0.0, 0.0],
            "A": [],
            "l": [],
            "u": [],
        }
        with mock.patch.object(SOLVER_MODULE, "MAX_DENSE_VARIABLES", 1):
            with self.assertRaises(SOLVER_MODULE.InputError):
                SOLVER_MODULE.validate_problem(problem)

    def test_dense_entry_guard_counts_P_and_A(self) -> None:
        problem = {
            "P": [[1.0, 0.0], [0.0, 1.0]],
            "q": [0.0, 0.0],
            "A": [[1.0, 1.0]],
            "l": [0.0],
            "u": [1.0],
        }
        with (
            mock.patch.object(SOLVER_MODULE, "MAX_DENSE_VARIABLES", 10),
            mock.patch.object(SOLVER_MODULE, "MAX_DENSE_ENTRIES", 5),
        ):
            with self.assertRaises(SOLVER_MODULE.InputError):
                SOLVER_MODULE.validate_problem(problem)

    def test_input_file_size_guard_runs_before_json_decode(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "oversized.json"
            path.write_text(" " * 20, encoding="utf-8")
            with mock.patch.object(SOLVER_MODULE, "MAX_INPUT_BYTES", 10):
                with self.assertRaises(SOLVER_MODULE.InputError):
                    SOLVER_MODULE.load_problem(path)

    @unittest.skipUnless(HAS_NUMPY, "NumPy is required for direct verifier tests")
    def test_nonoptimal_stationary_feasible_pair_fails_kkt_verification(self) -> None:
        import numpy as np

        problem = SOLVER_MODULE.validate_problem(
            {
                "P": [[0.0]],
                "q": [1.0],
                "A": [[1.0]],
                "l": [0.0],
                "u": ["inf"],
                "settings": {"eps_abs": 1e-8, "eps_rel": 1e-8},
            }
        )
        report = SOLVER_MODULE.verify_solution(
            np,
            problem,
            np.asarray(problem["P"], dtype=float),
            np.asarray(problem["A"], dtype=float),
            np.asarray([1.0]),
            np.asarray([-1.0]),
            min_eigenvalue=0.0,
            psd_tolerance=1e-9,
            verify_tolerance=1e-7,
        )
        self.assertFalse(report["passed"])
        self.assertGreater(report["complementarity_inf"], 0.0)

    @unittest.skipUnless(HAS_NUMPY, "NumPy is required for direct verifier tests")
    def test_tiny_forged_primal_certificate_is_rejected_after_normalization(
        self,
    ) -> None:
        import numpy as np

        problem = SOLVER_MODULE.validate_problem(
            {
                "P": [[0.0]],
                "q": [0.0],
                "A": [[1.0]],
                "l": [1.0],
                "u": ["inf"],
            }
        )
        report = SOLVER_MODULE.verify_primal_certificate(
            np,
            problem,
            np.asarray(problem["A"], dtype=float),
            np.asarray([-1e-12]),
            verify_tolerance=1e-7,
        )
        self.assertFalse(report["passed"])
        self.assertGreater(report["certificate_norm_inf"], 0.0)
        self.assertTrue(report["normalized"])

    @unittest.skipUnless(HAS_NUMPY, "NumPy is required for direct verifier tests")
    def test_tiny_forged_dual_certificate_is_rejected_after_normalization(
        self,
    ) -> None:
        import numpy as np

        problem = SOLVER_MODULE.validate_problem(
            {
                "P": [[1.0]],
                "q": [1.0],
                "A": [],
                "l": [],
                "u": [],
            }
        )
        report = SOLVER_MODULE.verify_dual_certificate(
            np,
            problem,
            np.asarray(problem["P"], dtype=float),
            np.empty((0, 1), dtype=float),
            np.asarray([-1e-12]),
            verify_tolerance=1e-7,
        )
        self.assertFalse(report["passed"])
        self.assertGreater(report["certificate_norm_inf"], 0.0)
        self.assertTrue(report["normalized"])

    @unittest.skipUnless(HAS_OSQP_STACK, "OSQP numerical stack is not installed")
    def test_feasible_example_solves_and_verifies(self) -> None:
        result, report = self.run_json(str(SOLVER), str(FEASIBLE))
        self.assertEqual(0, result.returncode, result.stderr)
        self.assertEqual("", result.stderr)
        self.assertEqual("solved", report["status"]["classification"])
        self.assertTrue(report["status"]["accepted"])
        self.assertTrue(report["verification"]["passed"])
        self.assertAlmostEqual(0.3, report["solution"]["x"][0], places=5)
        self.assertAlmostEqual(0.7, report["solution"]["x"][1], places=5)

    @unittest.skipUnless(HAS_OSQP_STACK, "OSQP numerical stack is not installed")
    def test_infeasibility_certificates_verify(self) -> None:
        expected = (
            (PRIMAL_INFEASIBLE, "primal_infeasible"),
            (DUAL_INFEASIBLE, "dual_infeasible"),
        )
        for example, classification in expected:
            with self.subTest(example=example.name):
                result, report = self.run_json(str(SOLVER), str(example))
                self.assertEqual(0, result.returncode, result.stderr)
                self.assertEqual("", result.stderr)
                self.assertEqual(classification, report["status"]["classification"])
                self.assertTrue(report["status"]["accepted"])
                self.assertTrue(report["verification"]["passed"])


if __name__ == "__main__":
    unittest.main()
