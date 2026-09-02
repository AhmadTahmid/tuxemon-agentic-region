import hashlib
from pathlib import Path

from world_synthesis.compiler import (
    build_world,
    compile_layout,
    layout_to_tmx,
    merge_blocked_cells,
)
from world_synthesis.schema import load_world_spec
from world_synthesis.validate import validate_layout

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "world_synthesis" / "glasswind_region.yaml"


def _world_and_route():
    world = load_world_spec(SPEC)
    route = next(
        item for item in world.region.maps if item.id == "glasswind_causeway"
    )
    return world, route


def test_generation_is_deterministic() -> None:
    world, route = _world_and_route()
    first = compile_layout(world, route)
    second = compile_layout(world, route)
    assert first.layers == second.layers
    assert first.blocked == second.blocked
    assert first.generated_objects == second.generated_objects


def test_validation_rejects_unknown_story_event_action() -> None:
    world, route = _world_and_route()
    event = route.events[0].model_copy(update={"actions": ["not_an_action text"]})
    candidate = route.model_copy(update={"events": [event]})
    issues = validate_layout(world, compile_layout(world, candidate), REPO)
    assert any(item.code == "unknown_event_action" for item in issues)


def test_authored_critical_path_and_bridge_stay_clear() -> None:
    world, route = _world_and_route()
    layout = compile_layout(world, route)
    assert layout.path_cells.isdisjoint(layout.blocked)
    assert layout.bridge_cells.isdisjoint(layout.blocked)
    assert (route.player_spawn.x, route.player_spawn.y) not in layout.blocked


def test_collision_merging_preserves_exact_cells_and_reduces_shapes() -> None:
    cells = {(x, y) for y in range(4) for x in range(10)} | {(20, 20)}
    rectangles = merge_blocked_cells(cells)
    expanded = {
        (x, y)
        for left, top, width, height in rectangles
        for y in range(top, top + height)
        for x in range(left, left + width)
    }
    assert expanded == cells
    assert len(rectangles) == 2
    assert len(rectangles) < len(cells)


def test_build_has_stable_tmx_hash() -> None:
    build_world(SPEC, REPO)
    path = (
        REPO / "mods" / "world_synthesis" / "maps" / "glasswind_causeway.tmx"
    )
    first = hashlib.sha256(path.read_bytes()).hexdigest()
    build_world(SPEC, REPO)
    second = hashlib.sha256(path.read_bytes()).hexdigest()
    assert first == second


def test_forest_scatter_is_seeded_and_respects_safe_zone() -> None:
    world, route = _world_and_route()
    forest_zone = route.zones[0].model_copy(
        update={
            "id": "test_forest",
            "kind": "forest",
            "bounds": route.zones[0].bounds.model_copy(
                update={"x": 4, "y": 4, "width": 8, "height": 8}
            ),
            "density": 1.0,
            "tags": ["pine"],
        }
    )
    safe_zone = route.zones[0].model_copy(
        update={
            "id": "test_clearing",
            "kind": "safe",
            "bounds": route.zones[0].bounds.model_copy(
                update={"x": 6, "y": 6, "width": 3, "height": 3}
            ),
            "density": 0.0,
            "tags": [],
        }
    )
    candidate = route.model_copy(
        update={
            "boundary": route.boundary.model_copy(
                update={
                    "kind": "none",
                    "depth": 0,
                    "density": 0,
                    "falloff_per_cell": 0,
                }
            ),
            "zones": [forest_zone, safe_zone],
            "landmarks": [],
            "props": [],
        }
    )
    first = compile_layout(world, candidate)
    second = compile_layout(world, candidate)
    safe_cells = safe_zone.bounds.cells()
    forest_cells = {
        tuple(item["at"])
        for item in first.generated_objects
        if item["rule"] == "test_forest"
    }
    assert forest_cells
    assert forest_cells.isdisjoint(safe_cells)
    assert first.generated_objects == second.generated_objects


def test_starter_event_uses_typed_metadata_not_map_id() -> None:
    world, route = _world_and_route()
    candidate = route.model_copy(update={"id": "generic_starter_map"})
    tmx = layout_to_tmx(compile_layout(world, candidate))
    assert "add_monster cardiling,7" in tmx
    assert "glasswind_route_milestone_starter_given:yes" in tmx


def test_explicit_fence_openings_remain_walkable() -> None:
    world, route = _world_and_route()
    layout = compile_layout(world, route)
    fence = next(
        item
        for item in route.environmental_features
        if item.id == "warden_fence"
    )
    assert {(point.x, point.y) for point in fence.entrances}.isdisjoint(
        layout.blocked
    )


def test_generic_database_outputs_are_named_from_spec() -> None:
    build_world(SPEC, REPO)
    assert (
        REPO
        / "mods"
        / "world_synthesis"
        / "db"
        / "npc"
        / "glasswind_route_milestone_npcs.yaml"
    ).exists()
    assert (
        REPO
        / "mods"
        / "world_synthesis"
        / "l18n"
        / "en_US"
        / "LC_MESSAGES"
        / "glasswind_route_milestone.po"
    ).exists()


def test_story_event_serializes_generic_state_conditions() -> None:
    world, route = _world_and_route()
    event = route.events[0].model_copy(
        update={"conditions": ["is variable_set shared_shortcut:open"]}
    )
    candidate = route.model_copy(update={"events": [event]})
    tmx = layout_to_tmx(compile_layout(world, candidate))
    assert "is variable_set shared_shortcut:open" in tmx
    assert "is char_facing_tile player" in tmx


def test_generic_building_stamp_uses_existing_tiles_and_blocks_footprint() -> (
    None
):
    world, route = _world_and_route()
    prop = route.props[0].model_copy(
        update={
            "id": "test_house",
            "kind": "building",
            "at": route.props[0].at.model_copy(update={"x": 5, "y": 8}),
        }
    )
    candidate = route.model_copy(update={"props": [prop]})
    layout = compile_layout(world, candidate)
    assert layout.layers["Above Player"][4][5:9] == [850, 851, 852, 853]
    assert layout.layers["Objects"][8][5:9] == [978, 979, 980, 981]
    assert {(x, y) for y in range(4, 9) for x in range(5, 9)} <= layout.blocked
