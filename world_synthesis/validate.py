"""Schema, reference, TMX and graph-playability validation."""

from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import deque
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any

from world_synthesis.compiler import (
    TILESET_COUNT,
    CompiledLayout,
    merge_blocked_cells,
)
from world_synthesis.schema import WorldSpec


@dataclass(frozen=True)
class Diagnostic:
    severity: str
    code: str
    map_id: str | None
    message: str


def _reachable(
    layout: CompiledLayout, start: tuple[int, int]
) -> set[tuple[int, int]]:
    spec = layout.map_spec
    if start in layout.blocked:
        return set()
    seen = {start}
    queue = deque([start])
    while queue:
        x, y = queue.popleft()
        for candidate in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
            cx, cy = candidate
            if (
                0 <= cx < spec.width
                and 0 <= cy < spec.height
                and candidate not in layout.blocked
                and candidate not in seen
            ):
                seen.add(candidate)
                queue.append(candidate)
    return seen


def validate_layout(
    world: WorldSpec, layout: CompiledLayout, repo: Path
) -> list[Diagnostic]:
    spec = layout.map_spec
    issues: list[Diagnostic] = []
    reachable = _reachable(layout, (spec.player_spawn.x, spec.player_spawn.y))
    if not reachable:
        issues.append(
            Diagnostic(
                "error", "spawn_blocked", spec.id, "Player spawn is blocked."
            )
        )
    critical: list[tuple[str, tuple[int, int]]] = []
    critical.extend(
        (f"warp:{item.id}", (item.at.x, item.at.y))
        for item in spec.warps
        if item.mandatory
    )
    critical.extend(
        (f"npc:{item.id}", (item.at.x, item.at.y))
        for item in spec.npcs
        if item.mandatory
    )
    critical.extend(
        (f"landmark:{item.id}", (item.anchor.x, item.anchor.y))
        for item in spec.landmarks
        if item.role == "dominant"
    )
    critical.extend(
        (f"secret:{item.id}", (item.at.x, item.at.y)) for item in spec.secrets
    )
    for label, cell in critical:
        if cell not in reachable:
            issues.append(
                Diagnostic(
                    "error",
                    "unreachable_critical",
                    spec.id,
                    f"{label} at {cell} is unreachable from spawn.",
                )
            )
    for npc in spec.npcs:
        cell = (npc.at.x, npc.at.y)
        if cell in layout.blocked:
            issues.append(
                Diagnostic(
                    "error",
                    "npc_blocked",
                    spec.id,
                    f"NPC {npc.id} is inside collision.",
                )
            )
    for warp in spec.warps:
        target = next(
            item for item in world.region.maps if item.id == warp.target_map
        )
        if warp.target.x >= target.width or warp.target.y >= target.height:
            issues.append(
                Diagnostic(
                    "error",
                    "warp_target_bounds",
                    spec.id,
                    f"Warp {warp.id} target is outside {target.id}.",
                )
            )
    source_tiles = (
        repo
        / "mods"
        / "tuxemon"
        / "gfx"
        / "tilesets"
        / "prototyping_outdoor.tsx"
    )
    if not source_tiles.exists():
        issues.append(
            Diagnostic("error", "missing_tileset", spec.id, str(source_tiles))
        )
    for layer_name, layer in layout.layers.items():
        invalid = [
            (x, y, tile)
            for y, row in enumerate(layer)
            for x, tile in enumerate(row)
            if tile < 0 or tile >= TILESET_COUNT
        ]
        if invalid:
            issues.append(
                Diagnostic(
                    "error",
                    "invalid_tile",
                    spec.id,
                    f"Layer {layer_name} contains invalid tile IDs: {invalid[:3]}",
                )
            )
    rectangles = merge_blocked_cells(layout.blocked)
    expanded = {
        (x, y)
        for rx, ry, width, height in rectangles
        for y in range(ry, ry + height)
        for x in range(rx, rx + width)
    }
    if expanded != layout.blocked:
        issues.append(
            Diagnostic(
                "error",
                "collision_merge_changed_semantics",
                spec.id,
                "Merged rectangles do not exactly cover blocked cells.",
            )
        )
    empty_ratio = 1 - len(layout.generated_objects) / max(
        1, spec.width * spec.height
    )
    if spec.map_type.value == "route" and empty_ratio > 0.93:
        issues.append(
            Diagnostic(
                "warning",
                "sparse_decoration",
                spec.id,
                "Less than 7% of cells contain generated composition details.",
            )
        )
    return issues


def validate_warp_pairs(world: WorldSpec) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    by_map = {item.id: item for item in world.region.maps}
    for source in world.region.maps:
        for warp in source.warps:
            target = by_map[warp.target_map]
            if not any(back.target_map == source.id for back in target.warps):
                issues.append(
                    Diagnostic(
                        "error",
                        "unpaired_warp",
                        source.id,
                        f"Warp {warp.id} to {target.id} has no return warp.",
                    )
                )
    return issues


def validate_quest_references(world: WorldSpec) -> list[Diagnostic]:
    references = {
        "npc": {
            item.id for map_spec in world.region.maps for item in map_spec.npcs
        },
        "event": {
            item.id
            for map_spec in world.region.maps
            for item in map_spec.events
        },
        "warp": {
            item.id
            for map_spec in world.region.maps
            for item in map_spec.warps
        },
        "secret": {
            item.id
            for map_spec in world.region.maps
            for item in map_spec.secrets
        },
    }
    issues: list[Diagnostic] = []
    for quest in world.region.quests:
        for step in quest.steps:
            if step.reference not in references[step.kind]:
                issues.append(
                    Diagnostic(
                        "error",
                        "missing_quest_reference",
                        None,
                        f"Quest {quest.id} step {step.id} refers to missing {step.kind} {step.reference}.",
                    )
                )
    return issues


def validate_compiled_tmx(path: Path) -> list[Diagnostic]:
    issues: list[Diagnostic] = []
    try:
        root = ET.parse(path).getroot()
    except ET.ParseError as exc:
        return [Diagnostic("error", "malformed_tmx", path.stem, str(exc))]
    if root.attrib.get("orientation") != "orthogonal":
        issues.append(
            Diagnostic(
                "error",
                "unsupported_orientation",
                path.stem,
                "Only orthogonal TMX is supported.",
            )
        )
    source = root.find("tileset")
    if source is None or not source.attrib.get("source"):
        issues.append(
            Diagnostic(
                "error",
                "missing_tileset_reference",
                path.stem,
                "TMX has no external tileset.",
            )
        )
    return issues


def write_report(
    world: WorldSpec, layouts: dict[str, CompiledLayout], repo: Path
) -> tuple[Path, list[Diagnostic]]:
    diagnostics = validate_warp_pairs(world) + validate_quest_references(world)
    for layout in layouts.values():
        diagnostics.extend(validate_layout(world, layout, repo))
        diagnostics.extend(
            validate_compiled_tmx(
                repo
                / "mods"
                / "world_synthesis"
                / "maps"
                / f"{layout.map_spec.id}.tmx"
            )
        )
    reports = repo / "artifacts" / "world_synthesis" / "reports"
    reports.mkdir(parents=True, exist_ok=True)
    payload: dict[str, Any] = {
        "format_version": "1.0",
        "world_id": world.region.id,
        "summary": {
            "errors": sum(item.severity == "error" for item in diagnostics),
            "warnings": sum(
                item.severity == "warning" for item in diagnostics
            ),
            "maps": len(layouts),
        },
        "diagnostics": [asdict(item) for item in diagnostics],
    }
    encoded = json.dumps(payload, indent=2) + "\n"
    output = reports / "validation.json"
    output.write_text(encoded, encoding="utf-8")
    lines = [
        f"World synthesis validation: {payload['summary']['errors']} error(s), {payload['summary']['warnings']} warning(s)"
    ]
    lines.extend(
        f"[{item.severity.upper()}] {item.map_id or 'world'} {item.code}: {item.message}"
        for item in diagnostics
    )
    (reports / "validation.txt").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )
    return output, diagnostics
