import hashlib
from pathlib import Path

from world_synthesis.compiler import (
    build_world,
    compile_layout,
    merge_blocked_cells,
)
from world_synthesis.schema import load_world_spec

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
