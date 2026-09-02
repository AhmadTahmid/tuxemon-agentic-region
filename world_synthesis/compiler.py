"""Deterministic WorldSpec to Tuxemon/Tiled compiler.

The planner authors intent. This module performs mechanical rasterization and
format translation; it deliberately does not invent narrative structure.
"""

from __future__ import annotations

import hashlib
import json
import math
import random
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from world_synthesis.schema import (
    MapSpec,
    Point,
    Rect,
    WorldSpec,
    load_world_spec,
)

TILE_SIZE = 16
TILESET_COLUMNS = 32
TILESET_COUNT = 2048
TILESET_SOURCE = "../../tuxemon/gfx/tilesets/prototyping_outdoor.tsx"


@dataclass
class TilePalette:
    grass: int = 33
    grass_dark: int = 36
    grass_flower: int = 34
    path: int = 193
    water: int = 45
    pine_top: int = 15
    pine_base: int = 47
    tree_top_left: int = 16
    tree_top_right: int = 17
    tree_base_left: int = 48
    tree_base_right: int = 49
    shrub: int = 476
    flower: int = 475
    boulder: int = 50
    rock: int = 54
    bridge_top: int = 562
    bridge_middle: int = 594
    bridge_bottom: int = 626
    fence_horizontal: int = 210
    fence_vertical: int = 242
    sign_top: int = 306
    sign_middle: int = 338
    sign_bottom: int = 370
    building: tuple[tuple[int, ...], ...] = (
        (850, 851, 852, 853),
        (882, 883, 884, 885),
        (914, 915, 916, 917),
        (946, 947, 948, 949),
        (978, 979, 980, 981),
    )


@dataclass
class CompiledLayout:
    map_spec: MapSpec
    layers: dict[str, list[list[int]]]
    experiment_id: str
    starter_monster: str
    starter_level: int
    blocked: set[tuple[int, int]] = field(default_factory=set)
    path_cells: set[tuple[int, int]] = field(default_factory=set)
    bridge_cells: set[tuple[int, int]] = field(default_factory=set)
    generated_objects: list[dict[str, object]] = field(default_factory=list)


def stable_seed(world_seed: int, *parts: str) -> int:
    payload = ":".join([str(world_seed), *parts]).encode()
    return int.from_bytes(hashlib.sha256(payload).digest()[:8], "big")


def _blank(width: int, height: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _line(a: Point, b: Point) -> Iterable[tuple[int, int]]:
    """Integer Bresenham line."""
    x0, y0, x1, y1 = a.x, a.y, b.x, b.y
    dx, sx = abs(x1 - x0), 1 if x0 < x1 else -1
    dy, sy = -abs(y1 - y0), 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        yield x0, y0
        if x0 == x1 and y0 == y1:
            return
        twice = 2 * error
        if twice >= dy:
            error += dy
            x0 += sx
        if twice <= dx:
            error += dx
            y0 += sy


def rasterize_path(
    map_spec: MapSpec, points: list[Point], width: int
) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    radius = (width - 1) / 2
    for start, end in zip(points, points[1:]):
        for cx, cy in _line(start, end):
            for oy in range(-math.ceil(radius), math.ceil(radius) + 1):
                for ox in range(-math.ceil(radius), math.ceil(radius) + 1):
                    if math.hypot(ox, oy) <= radius + 0.35:
                        x, y = cx + ox, cy + oy
                        if (
                            0 <= x < map_spec.width
                            and 0 <= y < map_spec.height
                        ):
                            cells.add((x, y))
    return cells


def _rect_cells(rect: Rect) -> set[tuple[int, int]]:
    return rect.cells()


def _edge_distance(x: int, y: int, width: int, height: int) -> int:
    return min(x, y, width - 1 - x, height - 1 - y)


def compile_layout(world: WorldSpec, map_spec: MapSpec) -> CompiledLayout:
    palette = TilePalette()
    rng = random.Random(
        stable_seed(world.metadata.seed, map_spec.id, str(map_spec.revision))
    )
    ground = _blank(map_spec.width, map_spec.height)
    terrain = _blank(map_spec.width, map_spec.height)
    objects = _blank(map_spec.width, map_spec.height)
    above = _blank(map_spec.width, map_spec.height)
    layers = {
        "Ground": ground,
        "Terrain": terrain,
        "Objects": objects,
        "Above Player": above,
    }

    base_tile = (
        palette.grass_dark
        if map_spec.base_terrain == "forest_floor"
        else palette.grass
    )
    alternate_tile = (
        palette.grass
        if map_spec.base_terrain == "forest_floor"
        else palette.grass_dark
    )
    # A quiet, deterministic variation underlies composition, without explicit coordinates.
    for y in range(map_spec.height):
        for x in range(map_spec.width):
            noise = rng.random()
            ground[y][x] = alternate_tile if noise < 0.035 else base_tile
            if noise > 0.975:
                ground[y][x] = palette.grass_flower

    paths = [map_spec.primary_path, *map_spec.secondary_paths]
    path_cells = set().union(
        *(rasterize_path(map_spec, path.points, path.width) for path in paths)
    )
    for x, y in path_cells:
        terrain[y][x] = palette.path

    river_cells: set[tuple[int, int]] = set()
    bridge_cells: set[tuple[int, int]] = set()
    for feature in map_spec.environmental_features:
        cells = _rect_cells(feature.bounds)
        if feature.kind == "river":
            river_cells |= cells
        elif feature.kind == "bridge":
            bridge_cells |= cells
    for x, y in river_cells:
        terrain[y][x] = palette.water
    if bridge_cells:
        by_x: dict[int, list[int]] = {}
        for x, y in bridge_cells:
            by_x.setdefault(x, []).append(y)
        for x, ys in by_x.items():
            low, high = min(ys), max(ys)
            for y in ys:
                terrain[y][x] = (
                    palette.bridge_top
                    if y == low
                    else palette.bridge_bottom
                    if y == high
                    else palette.bridge_middle
                )

    # Hard boundary with deliberate gaps for authored transitions.
    warp_cells = {(warp.at.x, warp.at.y) for warp in map_spec.warps}
    building_cells = {
        (prop.at.x + ox, prop.at.y - 4 + oy)
        for prop in map_spec.props
        if prop.kind == "building"
        for oy in range(5)
        for ox in range(4)
    }
    protected = path_cells | bridge_cells | warp_cells | building_cells
    protected |= {(npc.at.x, npc.at.y) for npc in map_spec.npcs}
    protected |= {(secret.at.x, secret.at.y) for secret in map_spec.secrets}
    protected |= {(prop.at.x, prop.at.y) for prop in map_spec.props}
    protected |= set().union(
        *(
            _rect_cells(zone.bounds)
            for zone in map_spec.zones
            if zone.kind == "safe"
        )
    )
    blocked = river_cells - bridge_cells
    generated: list[dict[str, object]] = []

    boundary = map_spec.boundary
    if boundary.kind == "forest":
        boundary_rng = random.Random(
            stable_seed(world.metadata.seed, map_spec.id, "boundary")
        )
        for y in range(map_spec.height):
            for x in range(map_spec.width):
                distance = _edge_distance(
                    x, y, map_spec.width, map_spec.height
                )
                if distance >= boundary.depth or y == 0:
                    continue
                probability = (
                    1.0
                    if distance == 0
                    else max(
                        0,
                        boundary.density
                        - boundary.falloff_per_cell * distance,
                    )
                )
                if (
                    boundary_rng.random() >= probability
                    or (x, y) in protected
                ):
                    continue
                objects[y][x] = palette.pine_base
                above[y - 1][x] = palette.pine_top
                blocked.add((x, y))
                generated.append(
                    {
                        "kind": "pine",
                        "at": [x, y],
                        "rule": "boundary",
                    }
                )

    # Dense grass and flowers are zone rules; road/river/landmark clearance is explicit.
    landmark_cells = (
        set().union(
            *(_rect_cells(item.footprint) for item in map_spec.landmarks)
        )
        if map_spec.landmarks
        else set()
    )
    reserved = protected | blocked | river_cells | landmark_cells
    for zone in map_spec.zones:
        if zone.kind != "forest":
            continue
        zone_rng = random.Random(
            stable_seed(
                world.metadata.seed,
                map_spec.id,
                zone.id,
                str(map_spec.revision),
            )
        )
        for x, y in sorted(
            _rect_cells(zone.bounds), key=lambda cell: (cell[1], cell[0])
        ):
            if (
                y == 0
                or (x, y) in reserved
                or zone_rng.random() >= zone.density
            ):
                continue
            objects[y][x] = palette.pine_base
            above[y - 1][x] = palette.pine_top
            blocked.add((x, y))
            reserved.add((x, y))
            generated.append(
                {"kind": "pine", "at": [x, y], "rule": zone.id}
            )

    for zone in map_spec.zones:
        if zone.kind not in {"meadow", "encounter", "secret"}:
            continue
        zone_rng = random.Random(
            stable_seed(
                world.metadata.seed,
                map_spec.id,
                zone.id,
                str(map_spec.revision),
            )
        )
        for x, y in sorted(
            _rect_cells(zone.bounds), key=lambda cell: (cell[1], cell[0])
        ):
            if (x, y) in reserved:
                continue
            roll = zone_rng.random()
            if "tall_grass" in zone.tags and roll < zone.density:
                ground[y][x] = (
                    palette.grass_flower
                    if zone_rng.random() < 0.11
                    else palette.grass_dark
                )
                generated.append(
                    {"kind": "tall_grass", "at": [x, y], "rule": zone.id}
                )
                if zone_rng.random() < 0.055:
                    objects[y][x] = palette.shrub
                    generated.append(
                        {"kind": "shrub", "at": [x, y], "rule": zone.id}
                    )
            elif "flowers" in zone.tags and roll < zone.density * 0.34:
                ground[y][x] = palette.grass_flower
                if zone_rng.random() < 0.32:
                    objects[y][x] = palette.flower
                generated.append(
                    {"kind": "flower_patch", "at": [x, y], "rule": zone.id}
                )

    # River stones cluster at banks, never in the player corridor.
    if river_cells:
        for x in range(2, map_spec.width - 2):
            for y in (
                min(y for _, y in river_cells) - 1,
                max(y for _, y in river_cells) + 1,
            ):
                if (x, y) in reserved or rng.random() > 0.14:
                    continue
                objects[y][x] = palette.rock
                blocked.add((x, y))
                generated.append(
                    {
                        "kind": "river_rock",
                        "at": [x, y],
                        "rule": "riverbank_cluster",
                    }
                )

    # Fence geometry is mechanical; entrances are authored content.
    for feature in map_spec.environmental_features:
        if feature.kind != "fence":
            continue
        rect = feature.bounds
        opening = {(point.x, point.y) for point in feature.entrances}
        perimeter = {
            (x, y)
            for y in range(rect.y, rect.y + rect.height)
            for x in range(rect.x, rect.x + rect.width)
            if x in {rect.x, rect.x + rect.width - 1}
            or y in {rect.y, rect.y + rect.height - 1}
        } - opening
        for x, y in perimeter:
            objects[y][x] = (
                palette.fence_vertical
                if x in {rect.x, rect.x + rect.width - 1}
                else palette.fence_horizontal
            )
            blocked.add((x, y))
            generated.append(
                {"kind": "fence", "at": [x, y], "rule": feature.id}
            )

    prop_tiles = {
        "shrub": palette.shrub,
        "flower": palette.flower,
        "rock": palette.rock,
        "boulder": palette.boulder,
    }
    for prop in map_spec.props:
        x, y = prop.at.x, prop.at.y
        if prop.kind == "tree":
            objects[y][x] = palette.pine_base
            above[y - 1][x] = palette.pine_top
        elif prop.kind == "sign":
            above[y - 2][x] = palette.sign_top
            above[y - 1][x] = palette.sign_middle
            objects[y][x] = palette.sign_bottom
        elif prop.kind == "building":
            for oy, row in enumerate(palette.building):
                for ox, tile in enumerate(row):
                    target_y = y - 4 + oy
                    if oy < 4:
                        above[target_y][x + ox] = tile
                    else:
                        objects[target_y][x + ox] = tile
                    if prop.blocks_movement:
                        blocked.add((x + ox, target_y))
        else:
            objects[y][x] = prop_tiles[prop.kind]
        if prop.blocks_movement and prop.kind != "building":
            blocked.add((x, y))
        generated.append(
            {"kind": prop.kind, "at": [x, y], "rule": f"prop:{prop.id}"}
        )

    return CompiledLayout(
        map_spec=map_spec,
        layers=layers,
        experiment_id=world.metadata.experiment_id,
        starter_monster=world.metadata.starter_monster,
        starter_level=world.metadata.starter_level,
        blocked=blocked,
        path_cells=path_cells,
        bridge_cells=bridge_cells,
        generated_objects=generated,
    )


def merge_blocked_cells(
    cells: set[tuple[int, int]],
) -> list[tuple[int, int, int, int]]:
    """Merge cells into exact non-overlapping rectangles without semantic change."""
    remaining = set(cells)
    rectangles: list[tuple[int, int, int, int]] = []
    while remaining:
        x, y = min(remaining, key=lambda cell: (cell[1], cell[0]))
        width = 1
        while (x + width, y) in remaining:
            width += 1
        height = 1
        while all((cx, y + height) in remaining for cx in range(x, x + width)):
            height += 1
        rect = (x, y, width, height)
        rectangles.append(rect)
        remaining -= {
            (cx, cy)
            for cy in range(y, y + height)
            for cx in range(x, x + width)
        }
    return rectangles


def _csv_data(grid: list[list[int]]) -> str:
    rows = [
        ",".join(str(tile + 1 if tile else 0) for tile in row) for row in grid
    ]
    # TMX CSV is a single comma-delimited stream; line breaks are cosmetic and
    # therefore must also be separated by a comma.
    return ",\n".join(rows)


def _properties(parent: ET.Element, values: list[tuple[str, str]]) -> None:
    props = ET.SubElement(parent, "properties")
    for key, value in values:
        ET.SubElement(props, "property", {"name": key, "value": value})


def _event(
    group: ET.Element,
    object_id: int,
    name: str,
    x: int,
    y: int,
    props: list[tuple[str, str]],
    width: int = 1,
    height: int = 1,
) -> int:
    obj = ET.SubElement(
        group,
        "object",
        {
            "id": str(object_id),
            "name": name,
            "type": "event",
            "x": str(x * TILE_SIZE),
            "y": str(y * TILE_SIZE),
            "width": str(width * TILE_SIZE),
            "height": str(height * TILE_SIZE),
        },
    )
    _properties(obj, props)
    return object_id + 1


def layout_to_tmx(layout: CompiledLayout) -> str:
    spec = layout.map_spec
    root = ET.Element(
        "map",
        {
            "version": "1.10",
            "tiledversion": "1.10.2",
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "width": str(spec.width),
            "height": str(spec.height),
            "tilewidth": str(TILE_SIZE),
            "tileheight": str(TILE_SIZE),
            "infinite": "0",
            "nextlayerid": "7",
            "nextobjectid": "1000",
        },
    )
    ET.SubElement(root, "tileset", {"firstgid": "1", "source": TILESET_SOURCE})
    for index, (name, grid) in enumerate(layout.layers.items(), start=1):
        layer = ET.SubElement(
            root,
            "layer",
            {
                "id": str(index),
                "name": name,
                "width": str(spec.width),
                "height": str(spec.height),
            },
        )
        data = ET.SubElement(layer, "data", {"encoding": "csv"})
        data.text = "\n" + _csv_data(grid) + "\n"

    collisions = ET.SubElement(
        root,
        "objectgroup",
        {"id": "5", "name": "Collisions", "color": "#ff0000"},
    )
    next_id = 1
    for x, y, width, height in merge_blocked_cells(layout.blocked):
        ET.SubElement(
            collisions,
            "object",
            {
                "id": str(next_id),
                "type": "collision",
                "x": str(x * TILE_SIZE),
                "y": str(y * TILE_SIZE),
                "width": str(width * TILE_SIZE),
                "height": str(height * TILE_SIZE),
            },
        )
        next_id += 1

    events = ET.SubElement(
        root, "objectgroup", {"id": "6", "name": "Events", "color": "#ffff00"}
    )
    for warp in spec.warps:
        next_id = _event(
            events,
            next_id,
            warp.id,
            warp.at.x,
            warp.at.y,
            [
                (
                    "act10",
                    f"transition_teleport player,{warp.target_map}.tmx,{warp.target.x},{warp.target.y},0.3",
                ),
                ("act20", f"char_face player,{warp.facing}"),
                ("cond10", "is char_at player"),
                ("cond20", f"is char_facing player,{warp.facing}"),
            ],
        )
    for encounter in spec.encounter_zones:
        next_id = _event(
            events,
            next_id,
            encounter.id,
            encounter.bounds.x,
            encounter.bounds.y,
            [
                (
                    "act1",
                    f"random_encounter {encounter.table},{encounter.probability}",
                )
            ],
            encounter.bounds.width,
            encounter.bounds.height,
        )
    for npc in spec.npcs:
        next_id = _event(
            events,
            next_id,
            f"Create {npc.id}",
            npc.at.x,
            npc.at.y,
            [
                ("act1", f"create_npc {npc.id},{npc.at.x},{npc.at.y}"),
                ("cond1", f"not char_exists {npc.id}"),
            ],
        )
        talk_props: list[tuple[str, str]] = [
            ("act1", f"char_talk {npc.id},pre_battle"),
            ("behav1", f"talk {npc.id}"),
        ]
        if npc.trainer:
            for index, monster in enumerate(npc.party, start=2):
                talk_props.append(
                    (f"act{index}", f"add_monster {monster},8,{npc.id},5,10")
                )
            talk_props.extend(
                [
                    (
                        f"act{len(npc.party) + 2}",
                        f"start_battle player,{npc.id}",
                    ),
                    (
                        f"act{len(npc.party) + 3}",
                        f"char_talk {npc.id},post_battle_lose",
                    ),
                    ("cond1", f"not battle_outcome player,won,{npc.id}"),
                ]
            )
        next_id = _event(
            events, next_id, f"Talk {npc.id}", npc.at.x, npc.at.y, talk_props
        )
    for story_event in spec.events:
        props = [
            (f"act{index}", action)
            for index, action in enumerate(story_event.actions, start=1)
        ]
        props.extend(
            (f"cond{index + 20}", condition)
            for index, condition in enumerate(story_event.conditions, start=1)
        )
        props.extend(
            [
                ("cond10", "is char_facing_tile player"),
                ("cond20", "is button_pressed INTERACT"),
            ]
        )
        next_id = _event(
            events,
            next_id,
            story_event.id,
            story_event.at.x,
            story_event.at.y,
            props,
        )
    for secret in spec.secrets:
        next_id = _event(
            events,
            next_id,
            secret.id,
            secret.at.x,
            secret.at.y,
            [
                ("act1", f"translated_dialog You find {secret.clue.lower()}"),
                ("act2", f"add_item {secret.reward}"),
                ("act3", f"set_variable {secret.id}:found"),
                ("cond10", "is char_facing_tile player"),
                ("cond20", "is button_pressed INTERACT"),
                ("cond1", f"not variable_set {secret.id}:found"),
            ],
        )
    next_id = _event(
        events,
        next_id,
        "Environment",
        0,
        0,
        [
            ("act1", "set_environment grass"),
            ("cond1", "not environment_is grass"),
        ],
    )
    if spec.grant_starter:
        starter_variable = f"{layout.experiment_id}_starter_given:yes"
        _event(
            events,
            next_id,
            "Give experiment starter",
            0,
            0,
            [
                (
                    "act1",
                    f"add_monster {layout.starter_monster},{layout.starter_level}",
                ),
                ("act2", f"set_variable {starter_variable}"),
                ("cond1", f"not variable_set {starter_variable}"),
            ],
        )

    ET.indent(root, space=" ")
    return (
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n"
    )


def _npc_records(world: WorldSpec) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for map_spec in world.region.maps:
        for npc in map_spec.npcs:
            combat = "miner" if npc.sprite.startswith("miner") else npc.sprite
            template_slug = (
                "miner" if npc.sprite.startswith("miner") else npc.sprite
            )
            records.append(
                {
                    "slug": npc.id,
                    "speech": {
                        "profile": {
                            "default": {
                                "pre_battle": f"{npc.id}_dialog",
                                "post_battle_win": None,
                                "post_battle_lose": (
                                    f"{npc.id}_post_battle"
                                    if npc.trainer
                                    else None
                                ),
                                "post_battle_draw": None,
                            }
                        }
                    },
                    "combat": {},
                    "audio": {},
                    "template": {
                        "sprite_name": npc.sprite,
                        "combat_sheet": combat,
                        "slug": template_slug,
                    },
                }
            )
    return records


def _encounter_records(world: WorldSpec) -> dict[str, dict[str, object]]:
    return {
        table.id: {
            "monsters": [
                {
                    "encounter_rate": entry.encounter_rate,
                    "exp_req_mod": 3,
                    "held_items": [],
                    "level_range": [entry.level_min, entry.level_max],
                    "monster": entry.monster,
                    "variables": [],
                }
                for entry in table.entries
            ],
            "slug": table.id,
        }
        for table in world.encounter_tables
    }


def _po_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _translation_catalog(world: WorldSpec) -> str:
    entries = {
        npc.id + "_dialog": npc.dialogue
        for map_spec in world.region.maps
        for npc in map_spec.npcs
    }
    for map_spec in world.region.maps:
        for npc in map_spec.npcs:
            if npc.trainer:
                entries[f"{npc.id}_post_battle"] = (
                    npc.post_battle_dialogue
                    or world.metadata.trainer_post_battle_dialogue
                )
    entries["world_synthesis_campaign"] = world.metadata.campaign_name
    header = (
        'msgid ""\nmsgstr ""\n'
        f'"Project-Id-Version: {world.metadata.experiment_id} 0.1.0\\n"\n'
        '"Language: en_US\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n\n'
    )
    return header + "\n".join(
        f'msgid "{_po_quote(key)}"\nmsgstr "{_po_quote(value)}"\n'
        for key, value in sorted(entries.items())
    )


def build_world(spec_path: Path, repo: Path) -> dict[str, CompiledLayout]:
    world = load_world_spec(spec_path)
    mod = repo / "mods" / "world_synthesis"
    maps_dir = mod / "maps"
    npc_dir = mod / "db" / "npc"
    encounter_dir = mod / "db" / "encounter"
    locale_dir = mod / "l18n" / "en_US" / "LC_MESSAGES"
    manifest_dir = repo / "artifacts" / "world_synthesis" / "manifests"
    for directory in (
        maps_dir,
        npc_dir,
        encounter_dir,
        locale_dir,
        manifest_dir,
    ):
        directory.mkdir(parents=True, exist_ok=True)

    layouts: dict[str, CompiledLayout] = {}
    for map_spec in world.region.maps:
        layout = compile_layout(world, map_spec)
        layouts[map_spec.id] = layout
        tmx = layout_to_tmx(layout)
        (maps_dir / f"{map_spec.id}.tmx").write_text(
            tmx, encoding="utf-8", newline="\n"
        )
        content_hash = hashlib.sha256(tmx.encode()).hexdigest()
        manifest = {
            "format_version": "1.0",
            "map_id": map_spec.id,
            "source": str(spec_path.relative_to(repo)).replace("\\", "/"),
            "source_seed": world.metadata.seed,
            "revision": map_spec.revision,
            "tmx_sha256": content_hash,
            "blocked_cells": sorted(
                [list(cell) for cell in layout.blocked],
                key=lambda cell: (cell[1], cell[0]),
            ),
            "collision_rectangles": [
                list(rect) for rect in merge_blocked_cells(layout.blocked)
            ],
            "path_cells": sorted(
                [list(cell) for cell in layout.path_cells],
                key=lambda cell: (cell[1], cell[0]),
            ),
            "generated_objects": layout.generated_objects,
        }
        (manifest_dir / f"{map_spec.id}.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    experiment_id = world.metadata.experiment_id
    (npc_dir / f"{experiment_id}_npcs.yaml").write_text(
        yaml.safe_dump(_npc_records(world), sort_keys=False), encoding="utf-8"
    )
    for table_id, record in _encounter_records(world).items():
        (encounter_dir / f"{table_id}.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False), encoding="utf-8"
        )
    # A separate gettext domain avoids overwriting upstream's base catalogue.
    (locale_dir / f"{experiment_id}.po").write_text(
        _translation_catalog(world), encoding="utf-8", newline="\n"
    )
    stale_base = locale_dir / "base.po"
    if stale_base.exists():
        stale_base.unlink()
    return layouts
