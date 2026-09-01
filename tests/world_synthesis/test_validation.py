from pathlib import Path

from world_synthesis.compiler import build_world
from world_synthesis.schema import load_world_spec
from world_synthesis.validate import (
    validate_compiled_tmx,
    validate_layout,
    validate_quest_references,
    validate_warp_pairs,
)

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "world_synthesis" / "glasswind_region.yaml"


def test_all_mandatory_targets_are_reachable_and_warps_are_paired() -> None:
    world = load_world_spec(SPEC)
    layouts = build_world(SPEC, REPO)
    issues = validate_warp_pairs(world)
    for layout in layouts.values():
        issues.extend(validate_layout(world, layout, REPO))
    assert [item for item in issues if item.severity == "error"] == []


def test_compiled_maps_use_supported_tmx_contract() -> None:
    build_world(SPEC, REPO)
    maps = REPO / "mods" / "world_synthesis" / "maps"
    for name in (
        "glasswind_causeway",
        "fernwake_threshold",
        "brasshaven_threshold",
    ):
        assert validate_compiled_tmx(maps / f"{name}.tmx") == []


def test_custom_database_references_exist_upstream() -> None:
    world = load_world_spec(SPEC)
    route = next(
        item for item in world.region.maps if item.id == "glasswind_causeway"
    )
    for npc in route.npcs:
        assert (
            REPO / "mods" / "tuxemon" / "sprites" / f"{npc.sprite}.png"
        ).exists()
    for slug in {monster for npc in route.npcs for monster in npc.party}:
        assert (
            REPO / "mods" / "tuxemon" / "db" / "monster" / f"{slug}.yaml"
        ).exists()


def test_quest_steps_resolve_to_reachable_world_entities() -> None:
    world = load_world_spec(SPEC)
    assert validate_quest_references(world) == []
