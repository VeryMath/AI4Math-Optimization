import importlib.util
import json
import re
from pathlib import Path

import yaml

from problem_spec import SDPT3_CLASSES, OptimizationProblemSpec


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "optimization-modeling-skill"
OPTSKILLS_ROOT = SKILL_ROOT / "references" / "optskills" / "skill_library"


def load_search_module():
    script_path = SKILL_ROOT / "scripts" / "search_archetypes.py"
    spec = importlib.util.spec_from_file_location("search_archetypes", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repo_exposes_one_unified_optimization_skill():
    skill_dirs = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))

    assert skill_dirs == ["optimization-modeling-skill"]


def test_unified_skill_has_codex_metadata_and_source_notice():
    skill_file = SKILL_ROOT / "SKILL.md"
    text = skill_file.read_text()

    assert "name: optimization-modeling-skill" in text
    assert "description: Use when a coding agent must" in text
    assert "Use when Codex must" not in text
    assert "OptSkills" in text
    assert "modeling_checkpoint.md" in text
    assert "problem.yaml" in text
    assert "solver route" in text
    assert "optional helper" in text
    assert "rg" in text
    assert "agent judgment" in text
    assert "interaction language" in text
    assert "send the concrete optimization problem" in text
    assert "Do not start with a questionnaire" in text
    assert "optimization-solver-skill" not in text
    assert "Use the search script before loading many archetype files" not in text


def test_interactive_opening_requires_language_only_first_response():
    text = (SKILL_ROOT / "SKILL.md").read_text()
    openai_yaml = (SKILL_ROOT / "agents" / "openai.yaml").read_text()

    assert "First Response Contract" in text
    assert "the entire first response must be one short language question" in text
    assert "Do not say the Skill has been loaded" in text
    assert "Do not list accepted input types" in text
    assert "Do not mention solvers, archetypes, problem.yaml, or execution plans" in text
    assert "What optimization problem are you working on?" not in text
    assert "I can take:" not in text
    assert "First ask the user to choose Chinese or English" in openai_yaml


def test_optskills_released_libraries_are_imported_as_references():
    expected_libraries = {
        "skill_library_cluster": 46,
        "skill_library_learned": 56,
        "skill_library_nanoco_learned": 93,
    }

    for library_name, minimum_count in expected_libraries.items():
        library_dir = OPTSKILLS_ROOT / library_name
        assert (library_dir / "index.json").exists()
        assert (library_dir / "ingredients.json").exists()
        assert len(list(library_dir.glob("*.md"))) >= minimum_count

    source_notice = (SKILL_ROOT / "references" / "optskills" / "SOURCE.md").read_text()
    assert "fujiwaranoM0kou/OptSkills" in source_notice
    assert "MIT" in source_notice
    assert "not individual installed agent skills" in source_notice
    assert "not individual Codex skills" not in source_notice


def test_archetype_search_finds_relevant_reference_files():
    search = load_search_module()

    tsp_results = search.search_archetypes("traveling salesman tour with subtour elimination", limit=5)
    assert tsp_results
    assert any("tsp" in result["path"].lower() for result in tsp_results)

    cover_results = search.search_archetypes("minimum cost choose sets to cover all required elements", limit=5)
    assert cover_results
    assert any("cover" in result["path"].lower() for result in cover_results)

    for result in tsp_results + cover_results:
        assert {"library", "path", "score", "title"} <= result.keys()
        assert result["score"] > 0


def test_archetype_search_cli_outputs_json(tmp_path):
    search = load_search_module()
    output_path = tmp_path / "results.json"

    exit_code = search.main(
        [
            "--query",
            "ship products from suppliers to customers with demand and capacity",
            "--limit",
            "3",
            "--out",
            str(output_path),
        ]
    )

    assert exit_code == 0
    payload = json.loads(output_path.read_text())
    assert len(payload["results"]) == 3
    assert any("transport" in result["path"].lower() or "flow" in result["path"].lower() for result in payload["results"])


def test_lp_milp_few_shot_examples_are_present():
    english_prompts = ROOT / "examples" / "lp-milp-example-prompts.md"
    chinese_prompts = ROOT / "examples" / "lp-milp-example-prompts.zh-CN.md"
    specs = ROOT / "examples" / "lp-milp-problem-specs.md"

    assert english_prompts.exists()
    assert chinese_prompts.exists()
    assert specs.exists()
    assert english_prompts.read_text().count("## Prompt") == 8
    assert chinese_prompts.read_text().count("## Prompt") == 8

    spec_text = specs.read_text()
    assert "transportation_lp" in spec_text
    assert "assignment_milp" in spec_text
    assert "weighted_set_cover_milp" in spec_text
    assert "capacitated_facility_location_milp" in spec_text
    assert "backend: existing" in spec_text


def test_lp_milp_problem_spec_few_shots_match_schema():
    specs = (ROOT / "examples" / "lp-milp-problem-specs.md").read_text()
    blocks = re.findall(r"```yaml\n(.*?)\n```", specs, flags=re.S)

    assert len(blocks) == 4
    for block in blocks:
        problem = OptimizationProblemSpec.from_mapping(yaml.safe_load(block))
        assert problem.problem_class in {"linear_program", "mixed_integer_linear_program"}
        assert problem.preferred_backend() == "existing"
        assert problem.modeling_layer["package"] in {"cvxpy", "pyomo"}
        assert problem.review["modeling_status"] == "proposed"


def test_specialized_package_materials_are_not_bundled():
    removed = "cd" + "opt"
    removed_title = "CD" + "Opt"

    tracked_paths = {
        path.as_posix().lower()
        for path in ROOT.rglob("*")
        if path.is_file() and ".git" not in path.parts and "__pycache__" not in path.parts
    }

    assert not any(removed in path for path in tracked_paths)

    for path in [
        SKILL_ROOT / "references" / f"{removed}_official_examples.md",
        SKILL_ROOT / "references" / "few_shots" / f"{removed}_official_pairs.md",
        ROOT / "examples" / f"{removed}-example-prompts.md",
        ROOT / "examples" / f"{removed}-example-prompts.zh-CN.md",
        ROOT / "examples" / removed,
    ]:
        assert not path.exists(), f"removed specialized package material still exists: {path}"

    for file_path in [
        SKILL_ROOT / "SKILL.md",
        SKILL_ROOT / "references" / "INDEX.md",
        SKILL_ROOT / "references" / "solver_catalog.md",
        SKILL_ROOT / "references" / "problem_schema.md",
        SKILL_ROOT / "references" / "implementation_templates.md",
        SKILL_ROOT / "references" / "code_generation_patterns.md",
        SKILL_ROOT / "references" / "evaluation_reporting.md",
    ]:
        text = file_path.read_text()
        assert removed not in text.lower(), f"removed package reference remains in {file_path}"
        assert removed_title not in text, f"removed package title remains in {file_path}"


def test_skill_does_not_bundle_duplicate_examples():
    skill_examples = SKILL_ROOT / "examples"
    skill_text = (SKILL_ROOT / "SKILL.md").read_text()
    index_text = (SKILL_ROOT / "references" / "INDEX.md").read_text()

    assert not skill_examples.exists()
    for text in [skill_text, index_text]:
        assert "skills/optimization-modeling-skill/examples" not in text
        assert "examples/lp-milp" not in text
        assert "These `examples/` files are packaged inside the Skill" not in text


def test_public_docs_use_modeling_skill_name_for_general_entrypoint():
    checked_paths = [
        ROOT / "README.md",
        ROOT / "README.zh-CN.md",
        ROOT / "SKILL.md",
        ROOT / ".codex" / "INSTALL.md",
        ROOT / ".opencode" / "INSTALL.md",
        ROOT / "AGENTS.md",
        ROOT / "CLAUDE.md",
        ROOT / "GEMINI.md",
        SKILL_ROOT / "manifest.yaml",
        SKILL_ROOT / "agents" / "openai.yaml",
    ]

    for path in checked_paths:
        text = path.read_text()
        assert "optimization-modeling-skill" in text
        assert "$optimization-skill" not in text
        assert "skills/optimization-skill" not in text


def test_skill_positioning_centers_modeling_and_solver_orchestration():
    text = (SKILL_ROOT / "SKILL.md").read_text()

    assert "Optimization Modeling & Solver Orchestration" in text
    assert "Model first, solve second" in text
    assert "examples, solver docs, and code templates are auxiliary materials" in text

    flow = [
        "confirm interaction language",
        "collect the concrete optimization problem",
        "build a modeling checkpoint",
        "classify the problem type",
        "normalize the confirmed model into problem.yaml",
        "choose a solver route",
        "generate or adapt solver code only when appropriate",
        "run only after approval",
        "interpret numerical evidence",
    ]
    for item in flow:
        assert item in text


def test_readmes_center_general_optimization_workflow():
    english = (ROOT / "README.md").read_text()
    chinese = (ROOT / "README.zh-CN.md").read_text()

    assert "## Example Materials" in english
    assert "## 示例材料" in chinese

    for text in [english, chinese]:
        assert "examples are optional" in text or "examples 是可选辅助材料" in text

    assert english.index("## About The Skill") < english.index("## Example Materials")
    assert chinese.index("## 关于这个 Skill") < chinese.index("## 示例材料")


def test_reference_index_separates_core_solver_templates_and_examples():
    index = (SKILL_ROOT / "references" / "INDEX.md").read_text()

    for heading in [
        "Core Modeling References",
        "Solver Selection References",
        "Implementation Template References",
        "Auxiliary Example Materials",
    ]:
        assert heading in index

    for reference in [
        "modeling_pipeline.md",
        "problem_schema.md",
        "problem_type_taxonomy.md",
        "solver_catalog.md",
        "solver_selection_rules.md",
        "implementation_templates.md",
        "optskills/SOURCE.md",
    ]:
        assert reference in index


def test_solver_catalog_covers_broad_problem_and_solver_families():
    catalog = (SKILL_ROOT / "references" / "solver_catalog.md").read_text()

    for problem_type in ["LP", "MILP", "QP", "SOCP", "SDP", "NLP", "least squares", "manifold"]:
        assert problem_type in catalog

    for solver_name in [
        "CVXPY",
        "Pyomo",
        "SciPy",
        "HiGHS",
        "CBC",
        "GLPK",
        "Gurobi",
        "SCIP",
        "MOSEK",
        "CVX",
        "YALMIP",
        "SDPT3",
        "IPOPT",
        "CasADi",
        "Manopt",
        "Pymanopt",
        "Geoopt",
    ]:
        assert solver_name in catalog

    assert "repository-native" in catalog
    assert "not all listed routes have automatic code generation" in catalog


def test_problem_schema_lists_all_router_supported_problem_classes():
    schema = (SKILL_ROOT / "references" / "problem_schema.md").read_text()

    for problem_class in sorted(SDPT3_CLASSES):
        assert f"`{problem_class}`" in schema


def test_package_metadata_versions_are_aligned():
    manifest = yaml.safe_load((SKILL_ROOT / "manifest.yaml").read_text())
    pyproject = (ROOT / "pyproject.toml").read_text()
    pyproject_version = re.search(r'^version = "([^"]+)"$', pyproject, flags=re.M).group(1)

    assert str(manifest["version"]) == pyproject_version


def test_manifest_keeps_environment_and_companion_skills_optional():
    manifest = yaml.safe_load((SKILL_ROOT / "manifest.yaml").read_text())

    assert manifest["preferred_env"]["conda"] == "ai4math"
    assert not manifest.get("requires_env")
    assert not manifest.get("requires_skills")
    assert "human_review_skill" in manifest["optional_skills"]
