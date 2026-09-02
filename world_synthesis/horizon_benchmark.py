"""Build, audit, and blindly play the Ashenbell horizon benchmark."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import os
import random
import re
import runpy
import secrets
import shutil
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

from PIL import Image, ImageDraw

from world_synthesis.compiler import (
    TILE_SIZE,
    TILESET_COLUMNS,
    build_world,
)
from world_synthesis.render import render_layout
from world_synthesis.schema import load_world_spec
from world_synthesis.validate import Diagnostic, write_report

REPO = Path(__file__).resolve().parents[1]
GENERATED = REPO / "benchmarks" / "generated"
ARTIFACTS = REPO / "artifacts" / "world_synthesis"
HUMAN_RESULTS = ARTIFACTS / "human_evaluation"
COMPILER_HASH = (
    "4e94b1ae4e531dd70da33b162b8329a0d0d2cc5a71190633e4a560b1ff7f156a"
)
ROLES = ("south_route", "ashenbell", "highland_pass", "old_bell_quarry")
DIMENSIONS = {
    "south_route": (36, 34),
    "ashenbell": (34, 30),
    "highland_pass": (36, 36),
    "old_bell_quarry": (30, 28),
}


@dataclass(frozen=True)
class HorizonVariant:
    method: str
    directory: Path
    prefix: str
    spec: Path | None
    start_map: str
    spawn: tuple[int, int]

    @property
    def map_ids(self) -> dict[str, str]:
        return {role: f"{self.prefix}_{role}" for role in ROLES}


VARIANTS = {
    "R0": HorizonVariant(
        "R0",
        GENERATED / "r0_direct" / "ashenbell",
        "r0",
        None,
        "r0_south_route",
        (18, 31),
    ),
    "R1": HorizonVariant(
        "R1",
        GENERATED / "r1_worldspec_one_shot" / "ashenbell",
        "r1",
        GENERATED / "r1_worldspec_one_shot" / "ashenbell" / "world_spec.yaml",
        "r1_south_route",
        (18, 31),
    ),
    "R2": HorizonVariant(
        "R2",
        GENERATED / "r2_agentic" / "ashenbell",
        "r2",
        GENERATED / "r2_agentic" / "ashenbell" / "final_world_spec.yaml",
        "r2_south_route",
        (18, 31),
    ),
}


@dataclass(frozen=True)
class TmxEvent:
    name: str
    x: int
    y: int
    width: int
    height: int
    properties: dict[str, str]


@dataclass(frozen=True)
class TmxInfo:
    map_id: str
    width: int
    height: int
    layers: dict[str, list[list[int]]]
    blocked: set[tuple[int, int]]
    events: tuple[TmxEvent, ...]
    tileset_source: str


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _copy_tree_files(source: Path, destination: Path) -> None:
    for path in sorted(item for item in source.rglob("*") if item.is_file()):
        target = destination / path.relative_to(source)
        target.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(path, target)


def _install_r0() -> dict[str, Path]:
    variant = VARIANTS["R0"]
    runpy.run_path(
        str(variant.directory / "raw_first_output.py"), run_name="__main__"
    )
    raw = variant.directory / "raw_output"
    maps_out = REPO / "mods" / "world_synthesis" / "maps"
    maps_out.mkdir(parents=True, exist_ok=True)
    installed: dict[str, Path] = {}
    repaired_dir = variant.directory / "tmx"
    repaired_dir.mkdir(parents=True, exist_ok=True)
    for source in sorted((raw / "maps").glob("*.tmx")):
        # The direct response wrote a source path relative to its evidence
        # directory. Installation changes only that mechanical relative path.
        text = source.read_text(encoding="utf-8").replace(
            "../../../../../../mods/tuxemon/gfx/tilesets/prototyping_outdoor.tsx",
            "../../tuxemon/gfx/tilesets/prototyping_outdoor.tsx",
        )
        text = text.replace('value="variable_set ', 'value="is variable_set ')
        target = maps_out / source.name
        target.write_text(text, encoding="utf-8", newline="\n")
        evidence = repaired_dir / source.name
        evidence.write_text(text, encoding="utf-8", newline="\n")
        installed[source.stem] = target
    _copy_tree_files(raw / "db", REPO / "mods" / "world_synthesis" / "db")
    _copy_tree_files(raw / "l18n", REPO / "mods" / "world_synthesis" / "l18n")
    npc_path = (
        REPO
        / "mods"
        / "world_synthesis"
        / "db"
        / "npc"
        / "ashenbell_r0_npcs.yaml"
    )
    npc_path.write_text(
        npc_path.read_text(encoding="utf-8").replace("botanist", "scientist"),
        encoding="utf-8",
    )
    return installed


def _copy_compiled_tmx(
    variant: HorizonVariant, directory_name: str = "tmx"
) -> dict[str, Path]:
    output: dict[str, Path] = {}
    directory = variant.directory / directory_name
    directory.mkdir(parents=True, exist_ok=True)
    for map_id in variant.map_ids.values():
        source = REPO / "mods" / "world_synthesis" / "maps" / f"{map_id}.tmx"
        target = directory / source.name
        shutil.copyfile(source, target)
        output[map_id] = target
    return output


def _parse_tmx(path: Path) -> TmxInfo:
    root = ET.parse(path).getroot()
    width, height = int(root.attrib["width"]), int(root.attrib["height"])
    layers: dict[str, list[list[int]]] = {}
    for node in root.findall("layer"):
        raw = (node.findtext("data") or "").replace("\n", "").split(",")
        gids = [int(item.strip()) for item in raw if item.strip()]
        layers[node.attrib["name"]] = [
            gids[index : index + width] for index in range(0, len(gids), width)
        ]
    blocked: set[tuple[int, int]] = set()
    collision_group = next(
        (
            item
            for item in root.findall("objectgroup")
            if item.attrib.get("name") == "Collisions"
        ),
        None,
    )
    if collision_group is not None:
        for obj in collision_group.findall("object"):
            x = int(float(obj.attrib.get("x", 0))) // TILE_SIZE
            y = int(float(obj.attrib.get("y", 0))) // TILE_SIZE
            obj_width = (
                int(float(obj.attrib.get("width", TILE_SIZE))) // TILE_SIZE
            )
            obj_height = (
                int(float(obj.attrib.get("height", TILE_SIZE))) // TILE_SIZE
            )
            blocked.update(
                (cx, cy)
                for cy in range(y, y + obj_height)
                for cx in range(x, x + obj_width)
            )
    events: list[TmxEvent] = []
    event_group = next(
        (
            item
            for item in root.findall("objectgroup")
            if item.attrib.get("name") == "Events"
        ),
        None,
    )
    if event_group is not None:
        for obj in event_group.findall("object"):
            props = {
                prop.attrib["name"]: prop.attrib.get("value", "")
                for prop in obj.findall("./properties/property")
            }
            events.append(
                TmxEvent(
                    obj.attrib.get("name", ""),
                    int(float(obj.attrib.get("x", 0))) // TILE_SIZE,
                    int(float(obj.attrib.get("y", 0))) // TILE_SIZE,
                    max(
                        1,
                        int(float(obj.attrib.get("width", TILE_SIZE)))
                        // TILE_SIZE,
                    ),
                    max(
                        1,
                        int(float(obj.attrib.get("height", TILE_SIZE)))
                        // TILE_SIZE,
                    ),
                    props,
                )
            )
    tileset = root.find("tileset")
    return TmxInfo(
        path.stem,
        width,
        height,
        layers,
        blocked,
        tuple(events),
        "" if tileset is None else tileset.attrib.get("source", ""),
    )


def _reachable(info: TmxInfo, start: tuple[int, int]) -> set[tuple[int, int]]:
    if start in info.blocked:
        return set()
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for candidate in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            cx, cy = candidate
            if (
                0 <= cx < info.width
                and 0 <= cy < info.height
                and candidate not in info.blocked
                and candidate not in seen
            ):
                seen.add(candidate)
                queue.append(candidate)
    return seen


def _interaction_anchor_failures(
    info: TmxInfo, start: tuple[int, int]
) -> list[dict[str, Any]]:
    """Find facing interactions the player cannot reliably stand beside.

    ``char_facing_tile`` targets must be occupied by collision or by a spawned
    NPC. Otherwise directional input walks the player onto the event tile
    instead of leaving them beside it and facing it.
    """
    reachable = _reachable(info, start)
    dynamic_anchors = {
        (item.x + x, item.y + y)
        for item in info.events
        if item.name.startswith("Create ")
        for x in range(item.width)
        for y in range(item.height)
    }
    stable_anchors = info.blocked | dynamic_anchors
    failures: list[dict[str, Any]] = []
    for item in info.events:
        values = tuple(item.properties.values())
        if not (
            any("char_facing_tile player" in value for value in values)
            and any("button_pressed INTERACT" in value for value in values)
        ):
            continue
        cells = {
            (item.x + x, item.y + y)
            for x in range(item.width)
            for y in range(item.height)
        }
        anchored = cells & stable_anchors
        adjacent = {
            candidate
            for x, y in anchored
            for candidate in (
                (x - 1, y),
                (x + 1, y),
                (x, y - 1),
                (x, y + 1),
            )
            if candidate in reachable
        }
        if not anchored or not adjacent:
            failures.append(
                {
                    "event": item.name,
                    "at": [item.x, item.y],
                    "stable_anchor": bool(anchored),
                    "reachable_adjacent_tiles": [
                        list(cell) for cell in sorted(adjacent)
                    ],
                }
            )
    return failures


def _render_tmx(
    path: Path,
    output: Path,
    *,
    debug: bool,
    spawn: tuple[int, int] | None = None,
) -> Path:
    info = _parse_tmx(path)
    atlas = Image.open(
        REPO
        / "mods"
        / "tuxemon"
        / "gfx"
        / "tilesets"
        / "prototyping_outdoor.png"
    ).convert("RGBA")
    canvas = Image.new(
        "RGBA", (info.width * TILE_SIZE, info.height * TILE_SIZE), "#1e1724"
    )
    for grid in info.layers.values():
        for y, row in enumerate(grid):
            for x, gid in enumerate(row):
                if not gid:
                    continue
                tile_id = gid - 1
                left = (tile_id % TILESET_COLUMNS) * TILE_SIZE
                top = (tile_id // TILESET_COLUMNS) * TILE_SIZE
                tile = atlas.crop(
                    (left, top, left + TILE_SIZE, top + TILE_SIZE)
                )
                canvas.alpha_composite(tile, (x * TILE_SIZE, y * TILE_SIZE))
    if debug:
        draw = ImageDraw.Draw(canvas, "RGBA")
        for x, y in info.blocked:
            draw.rectangle(
                (
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    (x + 1) * TILE_SIZE - 1,
                    (y + 1) * TILE_SIZE - 1,
                ),
                fill=(220, 35, 60, 70),
                outline=(255, 70, 70, 150),
            )
        for item in info.events:
            color = (255, 210, 0, 180)
            if any(
                value.startswith("transition_teleport")
                for value in item.properties.values()
            ):
                color = (40, 180, 255, 180)
            elif item.name.startswith("Create "):
                color = (255, 255, 255, 210)
            draw.rectangle(
                (
                    item.x * TILE_SIZE,
                    item.y * TILE_SIZE,
                    (item.x + item.width) * TILE_SIZE - 1,
                    (item.y + item.height) * TILE_SIZE - 1,
                ),
                outline=color,
                width=2,
            )
        if spawn:
            x, y = spawn
            draw.polygon(
                [
                    (x * TILE_SIZE + 8, y * TILE_SIZE + 1),
                    (x * TILE_SIZE + 15, y * TILE_SIZE + 14),
                    (x * TILE_SIZE + 1, y * TILE_SIZE + 14),
                ],
                fill=(60, 255, 140, 240),
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.resize(
        (canvas.width * 2, canvas.height * 2), Image.Resampling.NEAREST
    ).convert("RGB").save(output, optimize=True)
    return output


def _render_variant(
    variant: HorizonVariant,
    tmxs: dict[str, Path],
    layouts: dict[str, Any] | None = None,
    *,
    prefix: str = "",
) -> None:
    render_dir = variant.directory / f"{prefix}renders"
    debug_dir = variant.directory / f"{prefix}debug_renders"
    for role, map_id in variant.map_ids.items():
        spawn = variant.spawn if role == "south_route" else None
        if layouts is None:
            _render_tmx(
                tmxs[map_id],
                render_dir / f"{role}.png",
                debug=False,
                spawn=spawn,
            )
            _render_tmx(
                tmxs[map_id],
                debug_dir / f"{role}.png",
                debug=True,
                spawn=spawn,
            )
        else:
            render_layout(layouts[map_id], REPO, render_dir / f"{role}.png")
            render_layout(
                layouts[map_id], REPO, debug_dir / f"{role}.png", debug=True
            )
    _write_render_grid(render_dir, variant.directory / f"{prefix}overview.png")
    _write_render_grid(
        debug_dir, variant.directory / f"{prefix}debug_overview.png"
    )


def _write_render_grid(source: Path, output: Path) -> Path:
    images = [
        Image.open(source / f"{role}.png").convert("RGB") for role in ROLES
    ]
    cell_width = max(image.width for image in images)
    cell_height = max(image.height for image in images)
    canvas = Image.new("RGB", (cell_width * 2, cell_height * 2), "#17121c")
    draw = ImageDraw.Draw(canvas)
    for index, (role, image) in enumerate(zip(ROLES, images)):
        left = (index % 2) * cell_width
        top = (index // 2) * cell_height
        canvas.paste(image, (left, top))
        draw.rectangle((left, top, left + 210, top + 25), fill="#17121c")
        draw.text(
            (left + 7, top + 6),
            role.replace("_", " ").title(),
            fill="#f4e6c5",
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def _validate_direct(
    variant: HorizonVariant, tmxs: dict[str, Path]
) -> tuple[Path, list[Diagnostic]]:
    diagnostics: list[Diagnostic] = []
    infos = {map_id: _parse_tmx(path) for map_id, path in tmxs.items()}
    spawns = {
        f"{variant.prefix}_south_route": variant.spawn,
        f"{variant.prefix}_ashenbell": (17, 27),
        f"{variant.prefix}_highland_pass": (14, 33),
        f"{variant.prefix}_old_bell_quarry": (2, 14),
    }
    transition_re = re.compile(
        r"^transition_teleport player,([^,]+)\.tmx,(\d+),(\d+),"
    )
    for role, map_id in variant.map_ids.items():
        info = infos[map_id]
        if (info.width, info.height) != DIMENSIONS[role]:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "dimension_mismatch",
                    map_id,
                    f"Expected {DIMENSIONS[role]}, found {(info.width, info.height)}.",
                )
            )
        if (
            info.tileset_source
            != "../../tuxemon/gfx/tilesets/prototyping_outdoor.tsx"
        ):
            diagnostics.append(
                Diagnostic(
                    "error", "tileset_reference", map_id, info.tileset_source
                )
            )
        if set(info.layers) != {
            "Ground",
            "Terrain",
            "Objects",
            "Above Player",
        }:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "layer_contract",
                    map_id,
                    f"Unexpected layers: {sorted(info.layers)}",
                )
            )
        invalid = [
            gid
            for grid in info.layers.values()
            for row in grid
            for gid in row
            if gid < 0 or gid > 2048
        ]
        if invalid:
            diagnostics.append(
                Diagnostic(
                    "error",
                    "invalid_gid",
                    map_id,
                    f"Invalid GIDs: {invalid[:4]}",
                )
            )
        reachable = _reachable(info, spawns[map_id])
        if not reachable:
            diagnostics.append(
                Diagnostic(
                    "error", "spawn_blocked", map_id, "Spawn is blocked."
                )
            )
        for item in info.events:
            for value in item.properties.values():
                match = transition_re.match(value)
                if not match:
                    continue
                target, x, y = (
                    match.group(1),
                    int(match.group(2)),
                    int(match.group(3)),
                )
                if target not in infos:
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "missing_transition_target",
                            map_id,
                            f"{item.name} targets {target}.",
                        )
                    )
                elif not (
                    0 <= x < infos[target].width
                    and 0 <= y < infos[target].height
                ):
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "transition_target_bounds",
                            map_id,
                            f"{item.name} targets {(x, y)} outside {target}.",
                        )
                    )
                if (item.x, item.y) not in reachable:
                    diagnostics.append(
                        Diagnostic(
                            "error",
                            "unreachable_transition",
                            map_id,
                            f"{item.name} at {(item.x, item.y)} is unreachable.",
                        )
                    )
            if (
                item.name.startswith("Create ")
                and (item.x, item.y) not in reachable
            ):
                diagnostics.append(
                    Diagnostic(
                        "error",
                        "unreachable_npc",
                        map_id,
                        f"{item.name} is unreachable.",
                    )
                )
    directory = variant.directory / "validation"
    directory.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "format_version": "1.0",
        "method": "R0",
        "summary": {
            "errors": sum(item.severity == "error" for item in diagnostics),
            "warnings": sum(
                item.severity == "warning" for item in diagnostics
            ),
            "maps": 4,
        },
        "diagnostics": [asdict(item) for item in diagnostics],
    }
    output = directory / "validation.json"
    output.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    (directory / "validation.txt").write_text(
        "\n".join(
            [
                f"Direct low-level validation: {payload['summary']['errors']} error(s)",
                *(
                    f"[{item.severity.upper()}] {item.map_id} {item.code}: {item.message}"
                    for item in diagnostics
                ),
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    return output, diagnostics


def _event_transitions(
    info: TmxInfo,
) -> list[tuple[TmxEvent, str, tuple[int, int], bool]]:
    pattern = re.compile(
        r"^transition_teleport player,([^,]+)\.tmx,(\d+),(\d+),"
    )
    transitions = []
    for item in info.events:
        conditional = any(
            "variable_set " in value
            for key, value in item.properties.items()
            if key.startswith("cond")
        )
        for value in item.properties.values():
            match = pattern.match(value)
            if match:
                transitions.append(
                    (
                        item,
                        match.group(1),
                        (int(match.group(2)), int(match.group(3))),
                        conditional,
                    )
                )
    return transitions


def _semantic_review(
    method: str,
    *,
    initial: bool = False,
    validation_errors: list[Diagnostic] | None = None,
) -> list[dict[str, Any]]:
    path_failures = [
        item.message
        for item in validation_errors or []
        if item.code == "path_blocked"
    ]
    common = {
        "geographic_continuity": "The old bell road crosses the mandatory maps; Split Crown changes from distant paired stones to village frame to physical pass cairn; the quarry track leaves the pass eastward.",
        "story_consistency": "All variants retain quarry production, three-valley warnings, the closing slide, a retired chain, and a recent lower tone linked cautiously to west wind and runoff.",
        "npc_factual_consistency": "Shepherd, keeper, surveyor, and quarry worker have different evidence access without changing the immutable history.",
        "ecological_progression": "Tables remove shybulb from village/pass, increase elofly with exposure, and return shybulb only in the damp quarry cut.",
        "optional_content_integration": "The quarry adds material evidence, potion context, and the hoist shortcut without replacing the ordinary village/pass route.",
        "landmark_reuse": "Split Crown is reused as one regional landform rather than copied as an unrelated prop label.",
        "regional_identity": "Road, warning signs, paired stones, civic memory, weather talk, and quarry material recur with different functions.",
    }
    reviews = [
        {
            "category": key,
            "status": "supported",
            "evidence": value,
            "contradiction": None,
        }
        for key, value in common.items()
    ]
    if method == "R0":
        reviews.extend(
            [
                {
                    "category": "map_identity",
                    "status": "supported_with_limitation",
                    "evidence": "Direct grids distinguish wooded river approach, house-and-garden village, sparse rock pass, and dense quarry.",
                    "contradiction": "Low-level tile arrays do not preserve authored semantic intent, so later maintenance must infer why placements exist.",
                },
                {
                    "category": "progression_logic",
                    "status": "contradicted",
                    "evidence": "TMX events contain one monotonic producer and paired conditional shortcut consumers; ordinary warps remain unconditional.",
                    "contradiction": "The hoist producer and both shortcut consumers use traversable player-facing event cells, so the intended interaction anchors are not reliable in the client.",
                },
                {
                    "category": "repetition_across_maps",
                    "status": "concern",
                    "evidence": "The direct source reuses the same paint_path helper and similarly sized coordinate lists across all maps.",
                    "contradiction": "Distinct tiles reduce visual sameness, but the representation makes repeated geometry harder to notice before rendering.",
                },
            ]
        )
    elif method == "R1":
        reviews.extend(
            [
                {
                    "category": "map_identity",
                    "status": "supported_with_defects",
                    "evidence": "WorldSpec names functional village clusters and composition/density changes by archetype.",
                    "contradiction": "Three maps retain path/prop collision diagnostics because the one-shot received no design revision.",
                },
                {
                    "category": "progression_logic",
                    "status": "supported_with_defects",
                    "evidence": "The hoist producer is anchored to a blocking sign and the state variable names are consistent.",
                    "contradiction": "Both shortcut consumers remain on traversable event cells. "
                    + ("; ".join(path_failures) if path_failures else ""),
                },
                {
                    "category": "repetition_across_maps",
                    "status": "concern",
                    "evidence": "South and pass both use eight-node central S-curves, while village and quarry use similarly staged center-to-edge polylines.",
                    "contradiction": "Semantic labels differ more strongly than the underlying circulation grammar.",
                },
            ]
        )
    else:
        reviews.extend(
            [
                {
                    "category": "map_identity",
                    "status": "supported",
                    "evidence": "R2 varies path direction, encounter geometry, settlement circulation, negative space, and quarry density according to the region model.",
                    "contradiction": "The pass remains visually sparse under the frozen vocabulary; this is reported rather than padded.",
                },
                {
                    "category": "progression_logic",
                    "status": "contradiction"
                    if initial
                    else "supported_after_revision",
                    "evidence": "Initial ordinary topology remained optional-safe; final state naming matches all consumers.",
                    "contradiction": "Initial hoist produced r2_hoist:raised while consumers required r2_shortcut:open."
                    if initial
                    else None,
                },
                {
                    "category": "repetition_across_maps",
                    "status": "supported",
                    "evidence": "The four critical paths use different turn sequences and lateral biases, while repeated road/ridge motifs preserve regional continuity.",
                    "contradiction": None,
                },
            ]
        )
    order = (
        "geographic_continuity",
        "story_consistency",
        "npc_factual_consistency",
        "ecological_progression",
        "map_identity",
        "progression_logic",
        "optional_content_integration",
        "repetition_across_maps",
        "landmark_reuse",
        "regional_identity",
    )
    by_category = {item["category"]: item for item in reviews}
    return [by_category[name] for name in order]


def _consistency_report(
    variant: HorizonVariant,
    tmxs: dict[str, Path],
    *,
    initial: bool = False,
    validation_errors: list[Diagnostic] | None = None,
) -> dict[str, Any]:
    infos = {map_id: _parse_tmx(path) for map_id, path in tmxs.items()}
    ids = variant.map_ids
    checks: list[dict[str, Any]] = []

    def check(name: str, passed: bool, evidence: Any) -> None:
        checks.append(
            {
                "check": name,
                "status": "PASS" if passed else "FAIL",
                "evidence": evidence,
            }
        )

    transitions = {
        map_id: _event_transitions(info) for map_id, info in infos.items()
    }
    ordinary_edges = {
        tuple(sorted((source, target)))
        for source, values in transitions.items()
        for _, target, _, conditional in values
        if not conditional
    }
    expected_edges = {
        tuple(sorted((ids["south_route"], ids["ashenbell"]))),
        tuple(sorted((ids["ashenbell"], ids["highland_pass"]))),
        tuple(sorted((ids["highland_pass"], ids["old_bell_quarry"]))),
    }
    directed = {
        (source, target)
        for source, values in transitions.items()
        for _, target, _, conditional in values
        if not conditional
    }
    unpaired = sorted(
        (source, target)
        for source, target in directed
        if (target, source) not in directed
    )
    check("paired ordinary warps", not unpaired, {"unpaired": unpaired})
    check(
        "map topology matches declared region graph",
        ordinary_edges == expected_edges,
        {"expected": sorted(expected_edges), "actual": sorted(ordinary_edges)},
    )
    missing_targets = []
    for source, values in transitions.items():
        for item, target, (x, y), _ in values:
            if target not in infos or not (
                0 <= x < infos[target].width and 0 <= y < infos[target].height
            ):
                missing_targets.append(
                    {
                        "source": source,
                        "event": item.name,
                        "target": target,
                        "at": [x, y],
                    }
                )
    check(
        "referenced transition targets exist and fit",
        not missing_targets,
        missing_targets,
    )
    main_nodes = {ids["south_route"], ids["ashenbell"], ids["highland_pass"]}
    main_edges = {edge for edge in ordinary_edges if set(edge) <= main_nodes}
    reachable = {ids["south_route"]}
    changed = True
    while changed:
        changed = False
        for left, right in main_edges:
            if left in reachable and right not in reachable:
                reachable.add(right)
                changed = True
            if right in reachable and left not in reachable:
                reachable.add(left)
                changed = True
    check(
        "optional area remains optional",
        ids["highland_pass"] in reachable
        and ids["old_bell_quarry"] not in main_nodes,
        {"main_reachable_without_quarry": sorted(reachable)},
    )
    check(
        "mandatory progression does not require quarry",
        main_nodes <= reachable,
        {"mandatory_nodes": sorted(main_nodes)},
    )
    all_events = {
        item.name: (map_id, item)
        for map_id, info in infos.items()
        for item in info.events
    }
    actions_dir = REPO / "tuxemon" / "event" / "actions"
    unknown_actions = [
        {
            "map_id": map_id,
            "event": item.name,
            "property": key,
            "action": value,
        }
        for map_id, info in infos.items()
        for item in info.events
        for key, value in item.properties.items()
        if key.startswith("act")
        and not (actions_dir / f"{value.partition(' ')[0]}.py").exists()
    ]
    check(
        "event action verbs resolve in the active engine",
        not unknown_actions,
        {"unknown_actions": unknown_actions},
    )
    spawns = {
        ids["south_route"]: variant.spawn,
        ids["ashenbell"]: (17, 27),
        ids["highland_pass"]: (14, 33),
        ids["old_bell_quarry"]: (2, 14),
    }
    interaction_failures = [
        {"map_id": map_id, **failure}
        for map_id, info in infos.items()
        for failure in _interaction_anchor_failures(info, spawns[map_id])
    ]
    check(
        "player-facing interactions have stable reachable anchors",
        not interaction_failures,
        {"failures": interaction_failures},
    )
    required_events = {
        f"{variant.prefix}_raise_hoist",
        f"{variant.prefix}_village_shortcut_locked",
        f"{variant.prefix}_village_shortcut_open",
        f"{variant.prefix}_pass_shortcut_locked",
        f"{variant.prefix}_pass_shortcut_open",
        f"{variant.prefix}_read_bell_plinth",
        f"{variant.prefix}_pass_echo",
    }
    check(
        "referenced events exist",
        required_events <= set(all_events),
        {"missing": sorted(required_events - set(all_events))},
    )
    producers: dict[str, list[str]] = {}
    consumers: dict[str, list[str]] = {}
    for name, (_, item) in all_events.items():
        for key, value in item.properties.items():
            if key.startswith("act") and value.startswith("set_variable "):
                producers.setdefault(
                    value.removeprefix("set_variable "), []
                ).append(name)
            if key.startswith("cond"):
                normalized = value.removeprefix("not ").removeprefix("is ")
                if normalized.startswith("variable_set "):
                    consumers.setdefault(
                        normalized.removeprefix("variable_set "), []
                    ).append(name)
    shortcut = f"{variant.prefix}_shortcut:open"
    history = f"{variant.prefix}_bell_history:read"
    check(
        "required state variable producer exists",
        bool(producers.get(shortcut)) and bool(producers.get(history)),
        {
            "shortcut": producers.get(shortcut, []),
            "history": producers.get(history, []),
        },
    )
    check(
        "required state variable consumers exist",
        len(consumers.get(shortcut, [])) >= 4 and bool(consumers.get(history)),
        {
            "shortcut": consumers.get(shortcut, []),
            "history": consumers.get(history, []),
        },
    )
    shortcut_transitions = [
        (source, target, item.name)
        for source, values in transitions.items()
        for item, target, _, conditional in values
        if conditional
        and any(
            value
            in {f"variable_set {shortcut}", f"is variable_set {shortcut}"}
            for value in item.properties.values()
        )
    ]
    shortcut_pairs = {
        (source, target) for source, target, _ in shortcut_transitions
    }
    expected_shortcuts = {
        (ids["ashenbell"], ids["highland_pass"]),
        (ids["highland_pass"], ids["ashenbell"]),
    }
    check(
        "shortcut is two-way after unlock",
        shortcut_pairs == expected_shortcuts,
        {
            "expected": sorted(expected_shortcuts),
            "actual": sorted(shortcut_pairs),
        },
    )
    conflicting_shortcut_writes = sorted(
        variable
        for variable in producers
        if variable.startswith(f"{variant.prefix}_shortcut:")
        and variable != shortcut
    )
    check(
        "shortcut cannot become permanently inaccessible",
        not conflicting_shortcut_writes and main_nodes <= reachable,
        {
            "conflicting_writes": conflicting_shortcut_writes,
            "ordinary_route_available": main_nodes <= reachable,
        },
    )
    semantic = _semantic_review(
        variant.method, initial=initial, validation_errors=validation_errors
    )
    unverifiable = [
        "Whether first traversal lasts 20–35 minutes for a first-time player.",
        "Whether navigation feels clear moment to moment in the real client.",
        "Whether dialogue feels natural rather than merely fact-consistent.",
        "Whether landmarks are memorable and curiosity feels rewarded.",
        "Whether the low tone interpretation is understood without over-explanation.",
        "Fun and overall enjoyment.",
    ]
    return {
        "format_version": "1.0",
        "family": "ashenbell",
        "method": variant.method,
        "version": "initial" if initial else "final",
        "MECHANICALLY_VERIFIED": checks,
        "SEMANTICALLY_REVIEWED": semantic,
        "UNVERIFIABLE": unverifiable,
        "mechanical_summary": {
            "passed": sum(item["status"] == "PASS" for item in checks),
            "failed": sum(item["status"] == "FAIL" for item in checks),
        },
        "warning": "No aggregate world-quality or fun score is computed.",
    }


def _write_consistency(
    variant: HorizonVariant,
    tmxs: dict[str, Path],
    *,
    initial: bool = False,
    validation_errors: list[Diagnostic] | None = None,
) -> tuple[Path, dict[str, Any]]:
    report = _consistency_report(
        variant, tmxs, initial=initial, validation_errors=validation_errors
    )
    name = (
        "initial_consistency_report.json"
        if initial
        else "consistency_report.json"
    )
    output = variant.directory / name
    output.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    critic_name = (
        "initial_consistency_critic.json"
        if initial
        else "consistency_critic.json"
    )
    (variant.directory / critic_name).write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "method": variant.method,
                "version": report["version"],
                "review": report["SEMANTICALLY_REVIEWED"],
                "limitations": report["UNVERIFIABLE"],
                "aggregate_score": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return output, report


def _verify_real_loader(tmx_paths: list[Path]) -> list[dict[str, str]]:
    os.environ["SDL_VIDEODRIVER"] = "dummy"
    import pygame as pg

    from tuxemon.user_config import CONFIG

    CONFIG.mods = ["tuxemon", "world_synthesis"]

    from tuxemon.map.loader import TMXMapLoader
    from tuxemon.prepare import headless_init

    context = headless_init()
    pg.display.set_mode((320, 240))
    issues = []
    try:
        for path in tmx_paths:
            try:
                loaded = TMXMapLoader().load(str(path), context)
                if not loaded.collision_map or not loaded.events:
                    issues.append(
                        {
                            "map": path.stem,
                            "error": "loader returned no collision or events",
                        }
                    )
            except (
                Exception
            ) as exc:  # loader evidence must preserve the exact failure
                issues.append(
                    {"map": path.stem, "error": f"{type(exc).__name__}: {exc}"}
                )
    finally:
        pg.display.quit()
    return issues


def _verify_database_activation() -> list[dict[str, str]]:
    from tuxemon.database.data import ModData
    from tuxemon.database.loader import ModelLoader
    from tuxemon.database.utils import load_config
    from tuxemon.db import load_model_map
    from tuxemon.locale.locale import T

    try:
        base_translation = T._translators["base"]._real_translate
        if hasattr(base_translation, "_catalog"):
            # Tests may initialize T before Ashenbell files are built. Merge
            # the installed single-line PO entries explicitly, just as the
            # real launcher merges already-discovered experiment domains.
            locale = (
                REPO
                / "mods"
                / "world_synthesis"
                / "l18n"
                / "en_US"
                / "LC_MESSAGES"
            )
            for po_path in sorted(locale.glob("*.po")):
                lines = po_path.read_text(encoding="utf-8").splitlines()
                for index, line in enumerate(lines[:-1]):
                    if not line.startswith('msgid "'):
                        continue
                    following = lines[index + 1]
                    if not following.startswith('msgstr "'):
                        continue
                    msgid = json.loads(line.removeprefix("msgid "))
                    msgstr = json.loads(following.removeprefix("msgstr "))
                    if msgid:
                        base_translation._catalog[msgid] = msgstr
            for domain, translator in T._translators.items():
                experiment_translation = translator._real_translate
                if domain != "base" and hasattr(
                    experiment_translation, "_catalog"
                ):
                    base_translation._catalog.update(
                        experiment_translation._catalog
                    )
        base = load_config(str(REPO / "mods" / "db_config.yaml"))
        config = base.model_copy(
            update={
                "active_mods": ["tuxemon", "world_synthesis"],
                "mod_activation": {
                    **base.mod_activation,
                    "world_synthesis": True,
                },
                "mod_tables": {
                    **base.mod_tables,
                    "world_synthesis": ["npc", "encounter"],
                },
                "mod_dependencies": {
                    **base.mod_dependencies,
                    "world_synthesis": ["tuxemon"],
                },
            }
        )
        database = ModData(
            config, ModelLoader(load_model_map(config.model_map))
        )
        database.preload()
        database.load()
    except Exception as exc:
        return [
            {
                "table": "world_synthesis",
                "error": f"{type(exc).__name__}: {exc}",
            }
        ]
    return []


def _write_diff() -> None:
    directory = VARIANTS["R2"].directory
    initial = (
        (directory / "initial_world_spec.yaml")
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
    )
    final = (
        (directory / "final_world_spec.yaml")
        .read_text(encoding="utf-8")
        .splitlines(keepends=True)
    )
    diff = difflib.unified_diff(
        initial,
        final,
        fromfile="initial_world_spec.yaml",
        tofile="final_world_spec.yaml",
        n=0,
    )
    (directory / "revision_diff.patch").write_text(
        "".join(diff), encoding="utf-8", newline="\n"
    )


def build_ashenbell(*, quiet: bool = False) -> int:
    digest = _sha256(REPO / "world_synthesis" / "compiler.py")
    if digest != COMPILER_HASH:
        raise RuntimeError(
            f"Ashenbell compiler freeze changed: expected {COMPILER_HASH}, found {digest}"
        )
    _write_diff()
    outputs: dict[str, dict[str, Path]] = {}
    validation: dict[str, tuple[Path, list[Diagnostic]]] = {}

    outputs["R0"] = _install_r0()
    _render_variant(VARIANTS["R0"], outputs["R0"])
    validation["R0"] = _validate_direct(VARIANTS["R0"], outputs["R0"])

    r1 = VARIANTS["R1"]
    assert r1.spec is not None
    r1_world = load_world_spec(r1.spec)
    r1_layouts = build_world(r1.spec, REPO)
    outputs["R1"] = _copy_compiled_tmx(r1)
    _render_variant(r1, outputs["R1"], r1_layouts)
    validation["R1"] = write_report(
        r1_world, r1_layouts, REPO, r1.directory / "validation"
    )

    r2 = VARIANTS["R2"]
    initial_spec = r2.directory / "initial_world_spec.yaml"
    initial_world = load_world_spec(initial_spec)
    initial_layouts = build_world(initial_spec, REPO)
    initial_tmx = _copy_compiled_tmx(r2, "initial_tmx")
    _render_variant(r2, initial_tmx, initial_layouts, prefix="initial_")
    initial_validation = write_report(
        initial_world,
        initial_layouts,
        REPO,
        r2.directory / "initial_validation",
    )
    _write_consistency(
        r2, initial_tmx, initial=True, validation_errors=initial_validation[1]
    )
    assert r2.spec is not None
    r2_world = load_world_spec(r2.spec)
    r2_layouts = build_world(r2.spec, REPO)
    outputs["R2"] = _copy_compiled_tmx(r2)
    _render_variant(r2, outputs["R2"], r2_layouts)
    validation["R2"] = write_report(
        r2_world, r2_layouts, REPO, r2.directory / "validation"
    )

    consistency: dict[str, dict[str, Any]] = {}
    for method, variant in VARIANTS.items():
        _, consistency[method] = _write_consistency(
            variant, outputs[method], validation_errors=validation[method][1]
        )
    combined = {
        "format_version": "1.0",
        "family": "ashenbell",
        "compiler_sha256": digest,
        "MECHANICALLY_VERIFIED": {
            method: report["MECHANICALLY_VERIFIED"]
            for method, report in consistency.items()
        },
        "SEMANTICALLY_REVIEWED": {
            method: report["SEMANTICALLY_REVIEWED"]
            for method, report in consistency.items()
        },
        "UNVERIFIABLE": consistency["R2"]["UNVERIFIABLE"],
        "warning": "Automated evidence is not a world-quality score and does not establish fun.",
    }
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    (ARTIFACTS / "ashenbell_consistency_report.json").write_text(
        json.dumps(combined, indent=2) + "\n", encoding="utf-8"
    )
    loader_issues = _verify_real_loader(
        [
            REPO / "mods" / "world_synthesis" / "maps" / f"{map_id}.tmx"
            for method in ("R0", "R1", "R2")
            for map_id in VARIANTS[method].map_ids.values()
        ]
    )
    database_issues = _verify_database_activation()
    results = []
    for method, variant in VARIANTS.items():
        errors = [
            item for item in validation[method][1] if item.severity == "error"
        ]
        results.append(
            {
                "method": method,
                "representation": "direct low-level TMX/Tuxemon"
                if method == "R0"
                else "one-shot WorldSpec"
                if method == "R1"
                else "staged agentic WorldSpec",
                "map_dimensions": {
                    role: list(DIMENSIONS[role]) for role in ROLES
                },
                "validation_errors": [asdict(item) for item in errors],
                "validation_warnings": [
                    asdict(item)
                    for item in validation[method][1]
                    if item.severity == "warning"
                ],
                "consistency_failures": [
                    item
                    for item in consistency[method]["MECHANICALLY_VERIFIED"]
                    if item["status"] == "FAIL"
                ],
                "tmx_sha256": {
                    map_id: _sha256(path)
                    for map_id, path in outputs[method].items()
                },
            }
        )
    summary = {
        "format_version": "1.0",
        "family": "ashenbell",
        "masked_display_name": "Ashenbell Highlands",
        "compiler_sha256": digest,
        "results": results,
        "real_tuxemon_loader": {"maps_checked": 12, "issues": loader_issues},
        "real_database_activation": {"issues": database_issues},
        "human_evaluation_status": "pending",
        "warning": "R0/R1 interaction-anchor failures and R1 path-collision errors are preserved experimental findings; no aggregate winner is declared.",
    }
    for variant in VARIANTS.values():
        (variant.directory / "compiler_freeze.json").write_text(
            json.dumps(
                {
                    "format_version": "1.0",
                    "experiment": "ashenbell_horizon",
                    "compiler_sha256": digest,
                    "compiler_changed_during_variant_authoring": False,
                },
                indent=2,
            )
            + "\n",
            encoding="utf-8",
        )
    (ARTIFACTS / "ashenbell_horizon_benchmark.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    gallery = [
        "# Ashenbell horizon benchmark gallery",
        "",
        "Method identity is exposed here only for post-test analysis. Do not inspect before a blind session.",
        "",
    ]
    labels = {
        "R0": "Direct low-level",
        "R1": "One-shot WorldSpec",
        "R2": "Structured agentic",
    }
    for method, variant in VARIANTS.items():
        relative = variant.directory.relative_to(REPO).as_posix()
        gallery.extend(
            [
                f"## {method} — {labels[method]}",
                "",
                f"![Four-map overview](../../{relative}/overview.png)",
                "",
                f"![Four-map debug overview](../../{relative}/debug_overview.png)",
                "",
                f"![Village live capture](game_screenshots/ashenbell_{method.lower()}_village.png)",
                "",
                f"![Quarry live capture](game_screenshots/ashenbell_{method.lower()}_quarry.png)",
                "",
            ]
        )
        if method == "R2":
            gallery.extend(
                [
                    "![Corrected hoist approach](game_screenshots/ashenbell_r2_hoist_interaction.png)",
                    "",
                ]
            )
    (ARTIFACTS / "ashenbell_gallery.md").write_text(
        "\n".join(gallery), encoding="utf-8"
    )
    if not quiet:
        print(json.dumps(summary, indent=2))
    fatal = (
        bool(loader_issues)
        or bool(database_issues)
        or any(item.severity == "error" for item in validation["R2"][1])
        or bool(consistency["R2"]["mechanical_summary"]["failed"])
    )
    return 1 if fatal else 0


def choose_variant(rng: random.Random | None = None) -> HorizonVariant:
    chooser = rng.choice if rng is not None else secrets.choice
    return chooser(list(VARIANTS.values()))


def create_session(variant: HorizonVariant) -> tuple[str, Path]:
    session_id = f"ashenbell_{uuid4().hex[:10]}"
    directory = HUMAN_RESULTS / "sessions"
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / f"{session_id}.json"
    output.write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "session_id": session_id,
                "family": "ashenbell",
                "masked_display_name": "Ashenbell Highlands",
                "method": variant.method,
                "map_id": variant.start_map,
                "started_at": datetime.now(UTC).isoformat(),
                "evaluation_file": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return session_id, output


def _score(prompt: str) -> int:
    while True:
        raw = input(f"{prompt} (1-10): ").strip()
        if raw.isdigit() and 1 <= int(raw) <= 10:
            return int(raw)
        print("Enter a whole number from 1 to 10.")


def _yes_no(prompt: str) -> bool:
    while True:
        raw = input(f"{prompt} (yes/no): ").strip().lower()
        if raw in {"yes", "y"}:
            return True
        if raw in {"no", "n"}:
            return False
        print("Enter yes or no.")


def collect_evaluation(session_id: str, session_path: Path) -> Path:
    score_names = (
        "navigation_clarity",
        "sense_of_regional_coherence",
        "desire_to_explore",
        "settlement_believability",
        "environmental_variety",
        "story_coherence",
        "npc_naturalness",
        "landmark_memorability",
        "reward_for_curiosity",
        "overall_enjoyment",
        "repetition_artificiality",
    )
    print("\nPlaytest complete. Method identity remains hidden.")
    print(
        "For repetition/artificiality, 1 means natural and 10 means extremely artificial; other ratings use 1=poor and 10=excellent."
    )
    scores = {
        name: _score(name.replace("_", " ").capitalize())
        for name in score_names
    }
    questions = {
        "four_areas_geographically_connected": "Did the four areas feel geographically connected?",
        "npcs_inhabit_same_world": "Did NPCs seem to inhabit the same world?",
        "creature_distribution_differs": "Did creature distribution feel meaningfully different across environments?",
        "quarry_felt_optional": "Did the quarry feel optional rather than mandatory?",
        "quarry_changed_understanding": "Did the quarry change your understanding of the main story/world?",
        "felt_intentionally_authored": "Did the world feel intentionally authored?",
        "plausible_classic_monster_rpg": "Would this feel plausible as a coherent segment of a competent classic monster-catching RPG?",
    }
    answers: dict[str, Any] = {
        key: _yes_no(prompt) for key, prompt in questions.items()
    }
    answers.update(
        {
            "bell_interpretation": input(
                "What did you think was happening with the Ashenbell bells? "
            ).strip(),
            "most_memorable_location": input(
                "Which location do you remember most? "
            ).strip(),
            "contradiction_noticed": input(
                "Did anything contradict something you learned earlier? "
            ).strip(),
        }
    )
    directory = HUMAN_RESULTS / "responses"
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / f"{session_id}.json"
    output.write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "session_id": session_id,
                "scores": scores,
                "score_scale": {
                    "default": "1=poor, 10=excellent",
                    "repetition_artificiality": "1=natural, 10=extremely repetitive/artificial",
                },
                "answers": answers,
                "note": "Human results are intentionally separate from automated reports.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    session = json.loads(session_path.read_text(encoding="utf-8"))
    session["evaluation_file"] = str(output.relative_to(REPO)).replace(
        "\\", "/"
    )
    session["completed_at"] = datetime.now(UTC).isoformat()
    session_path.write_text(
        json.dumps(session, indent=2) + "\n", encoding="utf-8"
    )
    return output


def play_ashenbell(*, dry_run: bool = False) -> int:
    if build_ashenbell(quiet=True):
        return 1
    variant = choose_variant()
    session_id, session_path = create_session(variant)
    print(f"Blind session: {session_id}")
    print("Launching Ashenbell Highlands. Generation method is masked.")
    if dry_run:
        print("Dry run selected and logged; game was not launched.")
        return 0
    from world_synthesis.play import launch

    launch(variant.start_map, variant.spawn)
    output = collect_evaluation(session_id, session_path)
    print(f"Evaluation saved to {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser(
        "build", help="Build all Ashenbell R0/R1/R2 variants."
    )
    play_parser = subparsers.add_parser(
        "play", help="Blindly select, launch, and evaluate a variant."
    )
    play_parser.add_argument("family", choices=("ashenbell",))
    play_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        return build_ashenbell()
    return play_ashenbell(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
