import hashlib
import json
from pathlib import Path

import pytest

import world_synthesis.horizon_benchmark as horizon
from world_synthesis.schema import load_world_spec

REPO = Path(__file__).resolve().parents[2]


@pytest.fixture(scope="module")
def built_summary() -> dict:
    assert horizon.build_ashenbell(quiet=True) == 0
    return json.loads(
        (
            REPO
            / "artifacts"
            / "world_synthesis"
            / "ashenbell_horizon_benchmark.json"
        ).read_text(encoding="utf-8")
    )


def test_variants_share_dimensions_topology_and_allowance(
    built_summary: dict,
) -> None:
    expected = {
        "south_route": [36, 34],
        "ashenbell": [34, 30],
        "highland_pass": [36, 36],
        "old_bell_quarry": [30, 28],
    }
    assert all(
        item["map_dimensions"] == expected for item in built_summary["results"]
    )
    for method in ("R1", "R2"):
        variant = horizon.VARIANTS[method]
        assert variant.spec is not None
        world = load_world_spec(variant.spec)
        assert {
            entry.monster
            for table in world.encounter_tables
            for entry in table.entries
        } == {
            "shybulb",
            "squabbit",
            "elofly",
        }
        assert {
            item.reward
            for map_spec in world.region.maps
            for item in map_spec.secrets
        } == {"potion"}


def test_final_engine_checks_and_r2_cross_map_checks_pass(
    built_summary: dict,
) -> None:
    assert built_summary["real_tuxemon_loader"] == {
        "maps_checked": 12,
        "issues": [],
    }
    assert built_summary["real_database_activation"]["issues"] == []
    by_method = {item["method"]: item for item in built_summary["results"]}
    assert by_method["R0"]["validation_errors"] == []
    assert by_method["R2"]["validation_errors"] == []
    assert by_method["R2"]["consistency_failures"] == []


def test_direct_interaction_anchor_failure_is_preserved(
    built_summary: dict,
) -> None:
    result = next(
        item for item in built_summary["results"] if item["method"] == "R0"
    )
    assert [item["check"] for item in result["consistency_failures"]] == [
        "player-facing interactions have stable reachable anchors"
    ]
    failures = result["consistency_failures"][0]["evidence"]["failures"]
    assert any(item["event"] == "r0_raise_hoist" for item in failures)


def test_r1_one_shot_failures_are_preserved_without_design_repair(
    built_summary: dict,
) -> None:
    result = next(
        item for item in built_summary["results"] if item["method"] == "R1"
    )
    assert [item["code"] for item in result["validation_errors"]] == [
        "path_blocked",
        "path_blocked",
        "path_blocked",
    ]
    assert [item["check"] for item in result["consistency_failures"]] == [
        "player-facing interactions have stable reachable anchors"
    ]
    repairs = json.loads(
        (
            horizon.VARIANTS["R1"].directory / "mechanical_repairs.json"
        ).read_text(encoding="utf-8")
    )
    assert repairs["design_revisions"] == 0
    assert all(
        item["classification"]
        in {"schema_format_only", "event_grammar_only", "asset_reference_only"}
        for item in repairs["mechanical_repairs"]
    )


def test_r2_revision_fixes_initial_mechanical_and_state_failures(
    built_summary: dict,
) -> None:
    directory = horizon.VARIANTS["R2"].directory
    initial_validation = json.loads(
        (directory / "initial_validation" / "validation.json").read_text(
            encoding="utf-8"
        )
    )
    assert initial_validation["summary"]["errors"] == 3
    initial_consistency = json.loads(
        (directory / "initial_consistency_report.json").read_text(
            encoding="utf-8"
        )
    )
    failed = {
        item["check"]
        for item in initial_consistency["MECHANICALLY_VERIFIED"]
        if item["status"] == "FAIL"
    }
    assert "required state variable producer exists" in failed
    assert "player-facing interactions have stable reachable anchors" in failed
    final_consistency = json.loads(
        (directory / "consistency_report.json").read_text(encoding="utf-8")
    )
    assert final_consistency["mechanical_summary"]["failed"] == 0
    assert (directory / "revision_diff.patch").read_text(encoding="utf-8")


def test_direct_response_does_not_use_worldspec_or_compiler() -> None:
    source = (
        horizon.VARIANTS["R0"].directory / "raw_first_output.py"
    ).read_text(encoding="utf-8")
    assert "WorldSpec" not in source
    assert "from world_synthesis" not in source
    assert "import world_synthesis" not in source


def test_build_is_deterministic(built_summary: dict) -> None:
    before = {
        item["method"]: item["tmx_sha256"] for item in built_summary["results"]
    }
    assert horizon.build_ashenbell(quiet=True) == 0
    after_payload = json.loads(
        (
            REPO
            / "artifacts"
            / "world_synthesis"
            / "ashenbell_horizon_benchmark.json"
        ).read_text(encoding="utf-8")
    )
    after = {
        item["method"]: item["tmx_sha256"] for item in after_payload["results"]
    }
    assert before == after


def test_horizon_compiler_freeze_matches_audit() -> None:
    digest = hashlib.sha256(
        (REPO / "world_synthesis" / "compiler.py").read_bytes()
    ).hexdigest()
    audit = json.loads(
        (
            REPO
            / "artifacts"
            / "world_synthesis"
            / "horizon_generalization_log.json"
        ).read_text(encoding="utf-8")
    )
    assert digest == horizon.COMPILER_HASH
    assert digest == audit["horizon_freeze"]["compiler_sha256"]


def test_blind_dry_run_masks_method(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(horizon, "HUMAN_RESULTS", tmp_path)
    monkeypatch.setattr(horizon, "build_ashenbell", lambda quiet: 0)
    monkeypatch.setattr(
        horizon, "choose_variant", lambda: horizon.VARIANTS["R2"]
    )
    assert horizon.play_ashenbell(dry_run=True) == 0
    output = capsys.readouterr().out.lower()
    assert "r0" not in output
    assert "r1" not in output
    assert "r2" not in output
    assert "worldspec" not in output
    assert "agentic" not in output
    assert set(horizon.VARIANTS) == {"R0", "R1", "R2"}
