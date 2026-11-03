from __future__ import annotations

import subprocess
import sys
import tempfile
import unittest
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SCRIPTS = ROOT / "skills" / "cdopt-optimization" / "scripts"
GENERATORS = (
    ("write_constrained_layer_runner.py", "run_constrained_layer.py", "--steps"),
    ("write_constrained_rnn_runner.py", "run_constrained_rnn.py", "--steps"),
    ("write_stiefel_dictionary_runner.py", "run_dictionary_learning.py", "--maxiter"),
)


class CdoptRunnerGeneratorTests(unittest.TestCase):
    def test_generators_write_compilable_runners_with_failure_exit(self) -> None:
        for generator, runner_name, _bounded_option in GENERATORS:
            with self.subTest(generator=generator), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "generated"
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / generator), "--output-dir", str(output)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertEqual(result.returncode, 0, result.stderr)
                runner = output / runner_name
                subprocess.run(
                    [sys.executable, "-m", "py_compile", str(runner)], check=True
                )
                text = runner.read_text(encoding="utf-8")
                self.assertIn("raise SystemExit(main())", text)
                self.assertIn('return 0 if summary["success"] else 1', text)

    @unittest.skipUnless(hasattr(Path, "symlink_to"), "symlinks unavailable")
    def test_generators_reject_symlinked_output_runner(self) -> None:
        for generator, runner_name, _bounded_option in GENERATORS:
            with self.subTest(generator=generator), tempfile.TemporaryDirectory() as directory:
                output = Path(directory) / "generated"
                output.mkdir()
                target = Path(directory) / "victim.py"
                target.write_text("unchanged", encoding="utf-8")
                (output / runner_name).symlink_to(target)
                result = subprocess.run(
                    [sys.executable, str(SCRIPTS / generator), "--output-dir", str(output)],
                    capture_output=True,
                    text=True,
                    check=False,
                )
                self.assertNotEqual(result.returncode, 0)
                self.assertEqual(target.read_text(encoding="utf-8"), "unchanged")


if __name__ == "__main__":
    unittest.main()