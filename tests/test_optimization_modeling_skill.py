import importlib.util
import json
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SKILL_ROOT = ROOT / "skills" / "optimization-modeling-skill"
OPTSKILLS_ROOT = SKILL_ROOT / "references" / "optskills" / "skill_library"


def load_search_module():
    script_path = SKILL_ROOT / "scripts" / "search_archetypes.py"
    spec = importlib.util.spec_from_file_location("search_archetypes", script_path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_modeling_skill_has_codex_metadata_and_source_notice():
    skill_file = SKILL_ROOT / "SKILL.md"
    text = skill_file.read_text()

    assert "name: optimization-modeling-skill" in text
    assert "OptSkills" in text
    assert "modeling_checkpoint.md" in text
    assert "problem.yaml" in text
    assert "optimization-solver-skill" in text
    assert "optional helper" in text
    assert "rg" in text
    assert "agent judgment" in text
    assert "interaction language" in text
    assert "send the concrete optimization problem" in text
    assert "Do not start with a questionnaire" in text
    assert "Use the search script before loading many archetype files" not in text


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
