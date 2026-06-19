from pathlib import Path
import unittest


ROOT = Path(__file__).resolve().parents[1]


class CdoptSkillShapeTests(unittest.TestCase):
    def test_public_docs_use_portable_smoke_test_paths(self):
        files = [
            ROOT / "README.md",
            ROOT / "README.zh-CN.md",
            ROOT / "cdopt-optimization" / "SKILL.md",
            ROOT / "cdopt-optimization" / "references" / "INDEX.md",
        ]

        for path in files:
            text = path.read_text(encoding="utf-8")
            with self.subTest(path=path.relative_to(ROOT)):
                self.assertIn("CDOPT_SMOKE_TEST", text)
                self.assertIn("~/cdopt_manifold_tests/run_all_notebooks.py", text)
                self.assertNotIn("/" + "Users" + "/", text)

    def test_repository_has_minimal_python_project_metadata(self):
        pyproject = ROOT / "pyproject.toml"
        self.assertTrue(pyproject.is_file())

        text = pyproject.read_text(encoding="utf-8")
        self.assertIn('name = "cdopt-optimization"', text)
        self.assertIn('requires-python = ">=3.10"', text)
        self.assertIn('dev = ["pytest>=8.0"]', text)
        self.assertIn('testpaths = ["tests"]', text)

    def test_license_and_acknowledgment_are_visible(self):
        readme = (ROOT / "README.md").read_text(encoding="utf-8")
        license_text = (ROOT / "LICENSE").read_text(encoding="utf-8")

        self.assertIn("## Acknowledgments", readme)
        self.assertIn("CDOpt", readme)
        self.assertIn("MIT License", license_text)


if __name__ == "__main__":
    unittest.main()
