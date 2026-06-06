import importlib.util
import json
import re
from pathlib import Path

import yaml

from problem_spec import OptimizationProblemSpec


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "optimization-skill"
OPTSKILLS_ROOT = SKILL_ROOT / "references" / "optskills" / "skill_library"


def load_search_module():
    script_path = SKILL_ROOT / "scripts" / "search_archetypes.py"
    spec = importlib.util.spec_from_file_location("search_archetypes", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_repo_exposes_one_unified_optimization_skill():
    skill_dirs = sorted(path.parent.name for path in (ROOT / "skills").glob("*/SKILL.md"))

    assert skill_dirs == ["optimization-skill"]


def test_unified_skill_has_codex_metadata_and_source_notice():
    skill_file = SKILL_ROOT / "SKILL.md"
    text = skill_file.read_text()

    assert "name: optimization-skill" in text
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
    assert "optimization-modeling-skill" not in text
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


def test_cdopt_official_examples_reference_uses_clear_problem_and_template_layers():
    reference = SKILL_ROOT / "references" / "cdopt_official_examples.md"

    assert reference.exists()
    text = reference.read_text()
    assert "Problem Description Prompts" in text
    assert "Implementation Templates" in text
    assert "https://github.com/cdopt/cdopt.github.io/tree/main/docs/examples" in text

    for filename in [
        "dictionary_learning.html",
        "dictionary_learning_jax.html",
        "nonlinear_eigenvalue.html",
        "nearest_correlation_estimation.html",
        "bose_einstein_condensates.html",
        "symplectic_eigenvalue.html",
        "LeNet_orth.html",
        "LeNet_orth_jax.html",
        "rnn_single_layer.html",
        "distributed_linear_basic.html",
    ]:
        assert filename in text

    assert text.count(".html") >= 17
    assert "Use this as an implementation template, not as an automatically approved model." in text
    assert "cdopt.core.problem" in text
    assert "ConstraintDissolvingLayer" in text


def test_cdopt_prompts_are_driven_by_official_problem_descriptions():
    english = (ROOT / "examples" / "cdopt-example-prompts.md").read_text()
    chinese = (ROOT / "examples" / "cdopt-example-prompts.zh-CN.md").read_text()

    for text in [english, chinese]:
        assert "cdopt_official_examples.md" in text
        assert "Problem Description" in text
        assert "Prompt Body" in text
        assert "local Problem Description card" in text or "本地 Problem Description card" in text
        assert "Implementation Template" in text
        assert "examples/cdopt/problem-descriptions/" in text
        assert "dictionary_learning.html#problem-description" in text
        assert "LeNet_orth.html" in text
        assert "Do not copy the official code verbatim" in text
        assert "Read the official Problem Description section" not in text
        assert "[PASTE THE OFFICIAL PROBLEM DESCRIPTION TEXT HERE]" not in text
        assert text.count("## Prompt") >= 8


def test_cdopt_problem_description_cards_are_local_markdown():
    card_dir = ROOT / "examples" / "cdopt" / "problem-descriptions"
    expected_cards = [
        "dictionary-learning.md",
        "dictionary-learning-jax.md",
        "kohn-sham-1d.md",
        "nearest-correlation.md",
        "bose-einstein-condensates.md",
        "symplectic-eigenvalue.md",
    ]

    for card_name in expected_cards:
        path = card_dir / card_name
        assert path.exists(), f"missing local CDOpt card: {path}"
        text = path.read_text()
        assert "source_url:" in text
        assert "source_file:" in text
        assert "prompt_kind: official_problem_description" in text
        assert "## Prompt Body" in text
        assert "## Expected Modeling Signals" in text
        assert "https://cdopt.github.io/examples/" in text
        assert "skills/optimization-skill/references/cdopt_official_examples.md" in text
        assert "[PASTE THE OFFICIAL PROBLEM DESCRIPTION TEXT HERE]" not in text

        prompt_body = text.split("## Prompt Body", 1)[1].split("## Expected Modeling Signals", 1)[0]
        assert "Implementation Template" not in prompt_body

    combined = "\n".join((card_dir / card_name).read_text() for card_name in expected_cards)
    for modeling_signal in ["Stiefel", "oblique", "sphere", "symplectic", "L-BFGS-B", "CDOpt"]:
        assert modeling_signal in combined


def test_cdopt_prompt_indexes_point_to_local_problem_description_cards():
    english = (ROOT / "examples" / "cdopt-example-prompts.md").read_text()
    chinese = (ROOT / "examples" / "cdopt-example-prompts.zh-CN.md").read_text()

    for text in [english, chinese]:
        assert "examples/cdopt/problem-descriptions/dictionary-learning.md" in text
        assert "examples/cdopt/problem-descriptions/symplectic-eigenvalue.md" in text
        assert "local Problem Description card" in text or "本地 Problem Description card" in text
        assert "[PASTE THE OFFICIAL PROBLEM DESCRIPTION TEXT HERE]" not in text


def test_skill_local_examples_are_synced_with_repository_examples():
    repo_examples = ROOT / "examples"
    skill_examples = SKILL_ROOT / "examples"
    expected_files = [
        "cdopt-example-prompts.md",
        "cdopt-example-prompts.zh-CN.md",
        "lp-milp-example-prompts.md",
        "lp-milp-example-prompts.zh-CN.md",
        "lp-milp-problem-specs.md",
        "cdopt/problem-descriptions/dictionary-learning.md",
        "cdopt/problem-descriptions/dictionary-learning-jax.md",
        "cdopt/problem-descriptions/kohn-sham-1d.md",
        "cdopt/problem-descriptions/nearest-correlation.md",
        "cdopt/problem-descriptions/bose-einstein-condensates.md",
        "cdopt/problem-descriptions/symplectic-eigenvalue.md",
    ]

    for relative_path in expected_files:
        repo_file = repo_examples / relative_path
        skill_file = skill_examples / relative_path
        assert skill_file.exists(), f"missing skill-local example: {skill_file}"
        assert skill_file.read_text() == repo_file.read_text()


def test_skill_positioning_centers_modeling_and_solver_orchestration():
    text = (SKILL_ROOT / "SKILL.md").read_text()

    assert "Optimization Modeling & Solver Orchestration" in text
    assert "Model first, solve second" in text
    assert "examples, solver docs, and code templates are auxiliary materials" in text
    assert "CDOpt is a solver route, not the Skill's center of gravity" in text

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


def test_readmes_center_general_optimization_workflow_not_cdopt():
    english = (ROOT / "README.md").read_text()
    chinese = (ROOT / "README.zh-CN.md").read_text()

    assert "## CDOpt Workflow" not in english
    assert "## CDOpt Workflow" not in chinese
    assert "## Example Materials" in english
    assert "## 示例材料" in chinese

    for text in [english, chinese]:
        assert "CDOpt is only one solver route" in text or "CDOpt 只是其中一个 solver 路线" in text
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
        "cdopt_official_examples.md",
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
        "CDOpt",
        "Manopt",
        "Pymanopt",
        "Geoopt",
    ]:
        assert solver_name in catalog

    assert "repository-native" in catalog
    assert "not all listed routes have automatic code generation" in catalog
