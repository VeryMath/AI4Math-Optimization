import importlib.util
import json
from pathlib import Path


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
