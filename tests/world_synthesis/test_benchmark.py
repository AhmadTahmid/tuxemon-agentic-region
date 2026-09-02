import hashlib
import json
import random
from pathlib import Path

import pygame as pg

import world_synthesis.benchmark as benchmark
from tuxemon.map.loader import TMXMapLoader
from tuxemon.prepare import headless_init
from world_synthesis.compiler import build_world, compile_layout
from world_synthesis.schema import MapType, load_world_spec
from world_synthesis.validate import validate_layout, validate_warp_pairs

REPO = Path(__file__).resolve().parents[2]


def _main_route(spec: Path):
    world = load_world_spec(spec)
    route = next(
        item for item in world.region.maps if item.map_type == MapType.ROUTE
    )
    return world, route


def test_benchmark_variants_have_equivalent_functional_allowances() -> None:
    benchmark.build_deep_forest()
    signatures = []
    for variant in benchmark.VARIANTS.values():
        world, route = _main_route(variant.spec)
        signatures.append(
            (
                route.width,
                route.height,
                len(route.npcs),
                sum(item.trainer for item in route.npcs),
                len(route.encounter_zones),
                len(route.secrets),
                sum(item.role == "dominant" for item in route.landmarks),
            )
        )
        layouts = build_world(variant.spec, REPO)
        issues = validate_warp_pairs(world)
        issues.extend(validate_layout(world, layouts[route.id], REPO))
        assert [item for item in issues if item.severity == "error"] == []
    assert len(set(signatures)) == 1
    assert signatures[0] == (40, 44, 3, 2, 2, 1, 1)


def test_procedural_baseline_is_deterministic() -> None:
    first = benchmark.VARIANTS["A"].spec.read_bytes()
    benchmark.build_deep_forest()
    second = benchmark.VARIANTS["A"].spec.read_bytes()
    assert first == second
    world, route = _main_route(benchmark.VARIANTS["A"].spec)
    assert (
        compile_layout(world, route).generated_objects
        == compile_layout(world, route).generated_objects
    )


def test_one_shot_baseline_has_no_hidden_design_repairs() -> None:
    repairs = json.loads(
        (
            benchmark.VARIANTS["B"].spec.parent / "mechanical_repairs.json"
        ).read_text(encoding="utf-8")
    )
    assert repairs["design_revisions"] == 0
    assert repairs["mechanical_repairs"] == []


def test_structured_revision_fixes_initial_blockers() -> None:
    benchmark.build_deep_forest()
    initial_path = (
        benchmark.VARIANTS["C"].spec.parent / "initial_world_spec.yaml"
    )
    initial_world, initial_route = _main_route(initial_path)
    initial = compile_layout(initial_world, initial_route)
    initial_errors = [
        item
        for item in validate_layout(initial_world, initial, REPO)
        if item.severity == "error"
    ]
    assert {item.code for item in initial_errors} == {
        "path_blocked",
        "unreachable_critical",
    }
    final_world, final_route = _main_route(benchmark.VARIANTS["C"].spec)
    final = compile_layout(final_world, final_route)
    assert [
        item
        for item in validate_layout(final_world, final, REPO)
        if item.severity == "error"
    ] == []


def test_masked_selection_logs_method_without_revealing_it(
    tmp_path: Path, monkeypatch
) -> None:
    monkeypatch.setattr(benchmark, "HUMAN_RESULTS", tmp_path)
    variant = benchmark.choose_variant(random.Random(4))
    session_id, path = benchmark.create_session(variant)
    payload = json.loads(path.read_text(encoding="utf-8"))
    assert payload["method"] in {"A", "B", "C"}
    assert payload["masked_display_name"] == "Mossveil Passage"
    assert payload["session_id"] == session_id


def test_dry_run_output_does_not_reveal_selected_method(
    tmp_path: Path, monkeypatch, capsys
) -> None:
    monkeypatch.setattr(benchmark, "HUMAN_RESULTS", tmp_path)
    monkeypatch.setattr(benchmark, "build_deep_forest", lambda quiet: 0)
    monkeypatch.setattr(
        benchmark, "choose_variant", lambda: benchmark.VARIANTS["B"]
    )
    assert benchmark.play_deep_forest(dry_run=True) == 0
    output = capsys.readouterr().out.lower()
    assert "procedural" not in output
    assert "one-shot" not in output
    assert "agentic" not in output


def test_compiler_freezes_are_auditable() -> None:
    digest = hashlib.sha256(
        (REPO / "world_synthesis" / "compiler.py").read_bytes()
    ).hexdigest()
    summary = json.loads(
        (
            REPO
            / "artifacts"
            / "world_synthesis"
            / "deep_forest_benchmark.json"
        ).read_text(encoding="utf-8")
    )
    horizon = json.loads(
        (
            REPO
            / "artifacts"
            / "world_synthesis"
            / "horizon_generalization_log.json"
        ).read_text(encoding="utf-8")
    )
    assert summary["compiler_freeze_commit"].startswith("1ded0461f")
    assert horizon["pre_experiment"]["compiler_sha256"] == (
        "a2e28bd42e4810faef84bbe508594aa6f3e231b81e8d1f5d92b6562689962088"
    )
    assert digest == horizon["horizon_freeze"]["compiler_sha256"]


def test_real_tuxemon_loader_reads_all_three_routes(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    benchmark.build_deep_forest()
    context = headless_init()
    pg.display.set_mode((320, 240))
    for variant in benchmark.VARIANTS.values():
        path = (
            REPO
            / "mods"
            / "world_synthesis"
            / "maps"
            / f"{variant.map_id}.tmx"
        )
        loaded = TMXMapLoader().load(str(path), context)
        assert loaded.size == (40, 44)
        assert loaded.collision_map
        assert loaded.events
    pg.display.quit()
