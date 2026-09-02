"""Deterministic production EpisodeSpec to isolated Tuxemon mod compiler."""

from __future__ import annotations

import hashlib
import json
import math
import xml.etree.ElementTree as ET
from collections.abc import Iterable
from dataclasses import dataclass, field
from pathlib import Path

import yaml

from world_synthesis.compiler import merge_blocked_cells
from world_synthesis.production_slice.schema import (
    EncounterTable,
    EpisodeSpec,
    EventSpec,
    EventTrigger,
    LayerName,
    MapSpec,
    PaletteSpec,
    Point,
    Rect,
    load_episode,
)

TILE_SIZE = 16


@dataclass
class CompiledProductionMap:
    spec: MapSpec
    layers: dict[str, list[list[int]]]
    blocked: set[tuple[int, int]] = field(default_factory=set)
    path_cells: set[tuple[int, int]] = field(default_factory=set)
    interaction_anchors: set[tuple[int, int]] = field(default_factory=set)


def _blank(width: int, height: int) -> list[list[int]]:
    return [[0 for _ in range(width)] for _ in range(height)]


def _line(a: Point, b: Point) -> Iterable[tuple[int, int]]:
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


def _path_cells(map_spec: MapSpec, points: list[Point], width: int) -> set[tuple[int, int]]:
    cells: set[tuple[int, int]] = set()
    radius = (width - 1) / 2
    for start, end in zip(points, points[1:]):
        for cx, cy in _line(start, end):
            for oy in range(-math.ceil(radius), math.ceil(radius) + 1):
                for ox in range(-math.ceil(radius), math.ceil(radius) + 1):
                    if math.hypot(ox, oy) > radius + 0.35:
                        continue
                    x, y = cx + ox, cy + oy
                    if 0 <= x < map_spec.width and 0 <= y < map_spec.height:
                        cells.add((x, y))
    return cells


def _visual_id(palette: PaletteSpec, visual: str) -> int:
    try:
        return palette.tiles[visual]
    except KeyError as error:
        raise ValueError(f"visual {visual!r} is not a single tile") from error


def compile_map(episode: EpisodeSpec, map_spec: MapSpec) -> CompiledProductionMap:
    palette = episode.palettes[map_spec.palette]
    layers = {
        layer.value: _blank(map_spec.width, map_spec.height) for layer in LayerName
    }
    base = _visual_id(palette, map_spec.base_tile)
    layers[LayerName.GROUND.value] = [
        [base for _ in range(map_spec.width)] for _ in range(map_spec.height)
    ]
    blocked: set[tuple[int, int]] = set()
    path_cells: set[tuple[int, int]] = set()

    for fill in map_spec.fills:
        grid = layers[fill.layer.value]
        tile = _visual_id(palette, fill.tile)
        for x, y in fill.bounds.cells():
            grid[y][x] = tile

    for path in map_spec.paths:
        cells = _path_cells(map_spec, path.points, path.width)
        path_cells |= cells
        tile = _visual_id(palette, path.tile)
        grid = layers[LayerName.TERRAIN.value]
        for x, y in cells:
            grid[y][x] = tile

    if map_spec.boundary:
        boundary = map_spec.boundary
        openings = set().union(*(item.cells() for item in boundary.openings)) if boundary.openings else set()
        cells = {
            (x, y)
            for y in range(map_spec.height)
            for x in range(map_spec.width)
            if min(x, y, map_spec.width - 1 - x, map_spec.height - 1 - y)
            < boundary.depth
        } - openings
        tile = _visual_id(palette, boundary.tile)
        for x, y in cells:
            layers[LayerName.OBJECTS.value][y][x] = tile
        if boundary.collision:
            blocked |= cells

    for collision in map_spec.collisions:
        blocked |= collision.bounds.cells()

    for prop in map_spec.props:
        grid = layers[prop.layer.value]
        x, y = prop.at.x, prop.at.y
        occupied: set[tuple[int, int]] = set()
        if prop.visual in palette.stamps:
            stamp = palette.stamps[prop.visual]
            for oy, row in enumerate(stamp):
                for ox, tile in enumerate(row):
                    tx, ty = x + ox, y + oy
                    if not (0 <= tx < map_spec.width and 0 <= ty < map_spec.height):
                        raise ValueError(f"prop {prop.slug!r} stamp leaves map")
                    if tile >= 0:
                        grid[ty][tx] = tile
                        occupied.add((tx, ty))
        else:
            grid[y][x] = _visual_id(palette, prop.visual)
            occupied.add((x, y))
        if prop.blocks_movement:
            blocked |= occupied

    anchors: set[tuple[int, int]] = set()
    for event in map_spec.events:
        if event.trigger in {EventTrigger.INTERACT, EventTrigger.TALK}:
            anchors.add((event.at.x, event.at.y))
    anchors.update(
        (prop.interaction_anchor.x, prop.interaction_anchor.y)
        for prop in map_spec.props
        if prop.interaction_anchor
    )

    return CompiledProductionMap(
        spec=map_spec,
        layers=layers,
        blocked=blocked,
        path_cells=path_cells,
        interaction_anchors=anchors,
    )


def _csv_data(grid: list[list[int]]) -> str:
    rows = [",".join(str(tile + 1 if tile else 0) for tile in row) for row in grid]
    return ",\n".join(rows)


def _properties(parent: ET.Element, values: list[tuple[str, str]]) -> None:
    properties = ET.SubElement(parent, "properties")
    for name, value in values:
        ET.SubElement(properties, "property", {"name": name, "value": value})


def _event_object(
    parent: ET.Element,
    object_id: int,
    name: str,
    bounds: Rect,
    properties: list[tuple[str, str]],
) -> int:
    obj = ET.SubElement(
        parent,
        "object",
        {
            "id": str(object_id),
            "name": name,
            "type": "event",
            "x": str(bounds.x * TILE_SIZE),
            "y": str(bounds.y * TILE_SIZE),
            "width": str(bounds.width * TILE_SIZE),
            "height": str(bounds.height * TILE_SIZE),
        },
    )
    _properties(obj, properties)
    return object_id + 1


def _trigger_properties(event: EventSpec) -> list[tuple[str, str]]:
    properties: list[tuple[str, str]] = []
    if event.trigger == EventTrigger.TOUCH:
        properties.append(("cond10", "is char_at player"))
    elif event.trigger == EventTrigger.INTERACT:
        properties.extend(
            [
                ("cond10", "is char_facing_tile player"),
                ("cond20", "is button_pressed INTERACT"),
            ]
        )
    elif event.trigger == EventTrigger.TALK:
        properties.append(("behav1", f"talk {event.npc}"))
    return properties


def layout_to_tmx(
    episode: EpisodeSpec,
    layout: CompiledProductionMap,
) -> str:
    spec = layout.spec
    palette = episode.palettes[spec.palette]
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
            "nextobjectid": "10000",
        },
    )
    ET.SubElement(root, "tileset", {"firstgid": "1", "source": palette.source})
    for layer_id, (name, grid) in enumerate(layout.layers.items(), start=1):
        layer = ET.SubElement(
            root,
            "layer",
            {
                "id": str(layer_id),
                "name": name,
                "width": str(spec.width),
                "height": str(spec.height),
            },
        )
        data = ET.SubElement(layer, "data", {"encoding": "csv"})
        data.text = "\n" + _csv_data(grid) + "\n"

    collisions = ET.SubElement(
        root, "objectgroup", {"id": "5", "name": "Collisions", "color": "#ff0000"}
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
        properties = [
            (
                "act10",
                f"transition_teleport player,{warp.target_map}.tmx,{warp.target.x},{warp.target.y},0.3",
            ),
            ("act20", f"char_face player,{warp.facing}"),
            ("cond10", "is char_at player"),
            ("cond20", f"is char_facing player,{warp.facing}"),
        ]
        properties.extend(
            (f"cond{index + 30}", condition)
            for index, condition in enumerate(warp.conditions)
        )
        next_id = _event_object(
            events,
            next_id,
            warp.slug,
            Rect(x=warp.at.x, y=warp.at.y, width=1, height=1),
            properties,
        )

    for encounter in spec.encounters:
        next_id = _event_object(
            events,
            next_id,
            encounter.slug,
            encounter.bounds,
            [("act1", f"random_encounter {encounter.table},{encounter.probability}")],
        )

    for placement in spec.npcs:
        action = f"create_npc {placement.slug},{placement.at.x},{placement.at.y},{placement.behavior}"
        properties = [("act1", action), ("cond1", f"not char_exists {placement.slug}")]
        properties.extend(
            (f"cond{index + 10}", condition)
            for index, condition in enumerate(placement.conditions)
        )
        next_id = _event_object(
            events,
            next_id,
            f"Create {placement.slug}",
            Rect(x=placement.at.x, y=placement.at.y, width=1, height=1),
            properties,
        )

    for event in spec.events:
        properties = [
            (f"act{index}", action) for index, action in enumerate(event.actions, start=1)
        ]
        properties.extend(_trigger_properties(event))
        properties.extend(
            (f"cond{index + 30}", condition)
            for index, condition in enumerate(event.conditions)
        )
        bounds = event.bounds or Rect(x=event.at.x, y=event.at.y, width=1, height=1)
        next_id = _event_object(events, next_id, event.slug, bounds, properties)

    environment_properties = [
        ("act1", f"set_environment {spec.environment}"),
        ("cond1", f"not environment_is {spec.environment}"),
    ]
    next_id = _event_object(
        events,
        next_id,
        "Set environment",
        Rect(x=0, y=0, width=1, height=1),
        environment_properties,
    )
    if spec.music:
        _event_object(
            events,
            next_id,
            "Play music",
            Rect(x=0, y=0, width=1, height=1),
            [
                ("act1", f"play_music {spec.music},0.55"),
                ("cond1", f"not music_playing {spec.music}"),
            ],
        )

    ET.indent(root, space=" ")
    return '<?xml version="1.0" encoding="UTF-8"?>\n' + ET.tostring(
        root, encoding="unicode"
    ) + "\n"


def _npc_records(episode: EpisodeSpec) -> list[dict[str, object]]:
    records: list[dict[str, object]] = []
    for npc in episode.npcs:
        template = npc.template or npc.sprite.split("_")[0]
        record: dict[str, object] = {
            "slug": npc.slug,
            "persistence": npc.persistence,
            "speech": {"profile": {"default": {}}},
            "combat": {},
            "audio": {},
            "template": {
                "sprite_name": npc.sprite,
                "combat_sheet": npc.combat_sheet or template,
                "slug": template,
            },
        }
        if npc.party:
            record["monsters"] = [
                {
                    "slug": monster.slug,
                    "level": monster.level,
                    "money_mod": monster.money_mod,
                    "exp_req_mod": monster.exp_req_mod,
                    "gender": monster.gender,
                }
                for monster in npc.party
            ]
        records.append(record)
    return records


def _encounter_record(table: EncounterTable) -> dict[str, object]:
    # Kept separate so the output remains identical for the same authored table.
    return {
        "slug": table.slug,
        "monsters": [
            {
                "encounter_rate": entry.encounter_rate,
                "exp_req_mod": 3,
                "held_items": [],
                "level_range": list(entry.level_range),
                "monster": entry.monster,
                "variables": [],
            }
            for entry in table.entries
        ],
    }


def _po_quote(value: str) -> str:
    return value.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")


def _translation_catalog(episode: EpisodeSpec) -> str:
    entries = {**episode.dialogue, "low_bell_campaign": episode.metadata.title}
    header = (
        'msgid ""\nmsgstr ""\n'
        f'"Project-Id-Version: {episode.metadata.slug} 0.1.0\\n"\n'
        '"Language: en_US\\n"\n'
        '"Content-Type: text/plain; charset=UTF-8\\n"\n'
        '"Content-Transfer-Encoding: 8bit\\n"\n\n'
    )
    return header + "\n".join(
        f'msgid "{_po_quote(key)}"\nmsgstr "{_po_quote(value)}"\n'
        for key, value in sorted(entries.items())
    )


def build_episode(spec_path: Path, repo: Path) -> dict[str, CompiledProductionMap]:
    episode = load_episode(spec_path)
    mod = repo / "mods" / episode.metadata.slug
    maps_dir = mod / "maps"
    npc_dir = mod / "db" / "npc"
    encounter_dir = mod / "db" / "encounter"
    locale_dir = mod / "l18n" / "en_US" / "LC_MESSAGES"
    evidence_dir = repo / "artifacts" / "production_slice" / episode.metadata.slug
    manifest_dir = evidence_dir / "manifests"
    for directory in (maps_dir, npc_dir, encounter_dir, locale_dir, manifest_dir):
        directory.mkdir(parents=True, exist_ok=True)

    layouts: dict[str, CompiledProductionMap] = {}
    hashes: dict[str, str] = {}
    for map_spec in episode.maps:
        layout = compile_map(episode, map_spec)
        layouts[map_spec.slug] = layout
        tmx = layout_to_tmx(episode, layout)
        target = maps_dir / f"{map_spec.slug}.tmx"
        target.write_text(tmx, encoding="utf-8", newline="\n")
        digest = hashlib.sha256(tmx.encode()).hexdigest()
        hashes[map_spec.slug] = digest
        manifest = {
            "format_version": "1.0",
            "episode": episode.metadata.slug,
            "map": map_spec.slug,
            "source": str(spec_path.relative_to(repo)).replace("\\", "/"),
            "revision": episode.metadata.revision,
            "tmx_sha256": digest,
            "blocked_cells": sorted(
                [list(cell) for cell in layout.blocked], key=lambda cell: (cell[1], cell[0])
            ),
            "path_cells": sorted(
                [list(cell) for cell in layout.path_cells], key=lambda cell: (cell[1], cell[0])
            ),
            "interaction_anchors": sorted(
                [list(cell) for cell in layout.interaction_anchors],
                key=lambda cell: (cell[1], cell[0]),
            ),
        }
        (manifest_dir / f"{map_spec.slug}.json").write_text(
            json.dumps(manifest, indent=2) + "\n", encoding="utf-8"
        )

    (npc_dir / f"{episode.metadata.slug}_npcs.yaml").write_text(
        yaml.safe_dump(_npc_records(episode), sort_keys=False), encoding="utf-8"
    )
    for table in episode.encounters:
        (encounter_dir / f"{table.slug}.yaml").write_text(
            yaml.safe_dump(_encounter_record(table), sort_keys=False), encoding="utf-8"
        )
    (locale_dir / f"{episode.metadata.slug}.po").write_text(
        _translation_catalog(episode), encoding="utf-8", newline="\n"
    )
    build_manifest = {
        "episode": episode.metadata.slug,
        "revision": episode.metadata.revision,
        "source_sha256": hashlib.sha256(spec_path.read_bytes()).hexdigest(),
        "map_sha256": dict(sorted(hashes.items())),
    }
    (evidence_dir / "build_manifest.json").write_text(
        json.dumps(build_manifest, indent=2) + "\n", encoding="utf-8"
    )
    return layouts
