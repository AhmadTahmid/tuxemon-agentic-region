"""Typed contracts for authored production episodes.

The benchmark WorldSpec remains frozen. These models add reusable production
concepts without teaching the compiler about any particular episode or map.
"""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Literal

import yaml
from pydantic import BaseModel, ConfigDict, Field, model_validator


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Point(StrictModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)


class Rect(StrictModel):
    x: int = Field(ge=0)
    y: int = Field(ge=0)
    width: int = Field(gt=0)
    height: int = Field(gt=0)

    def cells(self) -> set[tuple[int, int]]:
        return {
            (x, y)
            for y in range(self.y, self.y + self.height)
            for x in range(self.x, self.x + self.width)
        }


class LayerName(StrEnum):
    GROUND = "Ground"
    TERRAIN = "Terrain"
    OBJECTS = "Objects"
    ABOVE = "Above Player"


class EpisodeMetadata(StrictModel):
    format_version: Literal["1.0"] = "1.0"
    slug: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    title: str
    seed: int
    revision: int = Field(ge=1)
    target_minutes: tuple[int, int]
    start_map: str
    start_position: tuple[int, int]
    player_name: str
    player_sprite: str

    @model_validator(mode="after")
    def ordered_duration(self) -> EpisodeMetadata:
        if self.target_minutes[0] > self.target_minutes[1]:
            raise ValueError("target duration must be ordered")
        return self


class PaletteSpec(StrictModel):
    source: str
    tiles: dict[str, int]
    stamps: dict[str, list[list[int]]] = Field(default_factory=dict)

    @model_validator(mode="after")
    def stamps_are_rectangular(self) -> PaletteSpec:
        for slug, rows in self.stamps.items():
            if not rows or not rows[0]:
                raise ValueError(f"palette stamp {slug!r} is empty")
            widths = {len(row) for row in rows}
            if len(widths) != 1:
                raise ValueError(f"palette stamp {slug!r} is not rectangular")
        return self


class PathSpec(StrictModel):
    slug: str
    points: list[Point] = Field(min_length=2)
    width: int = Field(ge=1, le=9)
    tile: str = "path"


class FillSpec(StrictModel):
    slug: str
    bounds: Rect
    tile: str
    layer: LayerName = LayerName.TERRAIN


class BoundarySpec(StrictModel):
    depth: int = Field(ge=0, le=10)
    tile: str
    collision: bool = True
    openings: list[Rect] = Field(default_factory=list)


class PropSpec(StrictModel):
    slug: str
    at: Point
    visual: str
    layer: LayerName = LayerName.OBJECTS
    blocks_movement: bool = False
    interaction_anchor: Point | None = None


class CollisionSpec(StrictModel):
    slug: str
    bounds: Rect


class WarpSpec(StrictModel):
    slug: str
    at: Point
    facing: Literal["up", "down", "left", "right"]
    target_map: str
    target: Point
    conditions: list[str] = Field(default_factory=list)
    mandatory: bool = True


class NpcPlacement(StrictModel):
    slug: str
    at: Point
    behavior: str = "stand"
    conditions: list[str] = Field(default_factory=list)


class EventTrigger(StrEnum):
    INIT = "init"
    TOUCH = "touch"
    INTERACT = "interact"
    TALK = "talk"


class EventSpec(StrictModel):
    slug: str
    at: Point
    trigger: EventTrigger
    actions: list[str] = Field(min_length=1)
    conditions: list[str] = Field(default_factory=list)
    bounds: Rect | None = None
    npc: str | None = None
    anchor_required: bool = True
    purpose: str
    mandatory: bool = False

    @model_validator(mode="after")
    def talk_has_npc(self) -> EventSpec:
        if self.trigger == EventTrigger.TALK and not self.npc:
            raise ValueError(f"talk event {self.slug!r} requires npc")
        if self.trigger != EventTrigger.TALK and self.npc:
            raise ValueError(f"non-talk event {self.slug!r} cannot bind npc")
        return self


class EncounterZone(StrictModel):
    slug: str
    bounds: Rect
    table: str
    probability: int = Field(ge=0, le=100)


class MapSpec(StrictModel):
    slug: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    title: str
    role: str
    width: int = Field(ge=8, le=200)
    height: int = Field(ge=8, le=200)
    palette: str
    base_tile: str
    environment: str
    music: str | None = None
    boundary: BoundarySpec | None = None
    paths: list[PathSpec] = Field(default_factory=list)
    fills: list[FillSpec] = Field(default_factory=list)
    props: list[PropSpec] = Field(default_factory=list)
    collisions: list[CollisionSpec] = Field(default_factory=list)
    warps: list[WarpSpec] = Field(default_factory=list)
    npcs: list[NpcPlacement] = Field(default_factory=list)
    events: list[EventSpec] = Field(default_factory=list)
    encounters: list[EncounterZone] = Field(default_factory=list)

    @model_validator(mode="after")
    def content_fits_and_ids_are_unique(self) -> MapSpec:
        def point_ok(point: Point) -> bool:
            return point.x < self.width and point.y < self.height

        def rect_ok(rect: Rect) -> bool:
            return (
                rect.x + rect.width <= self.width
                and rect.y + rect.height <= self.height
            )

        points = [
            *(point for path in self.paths for point in path.points),
            *(item.at for item in self.props),
            *(item.at for item in self.warps),
            *(item.at for item in self.npcs),
            *(item.at for item in self.events),
        ]
        rects = [
            *(item.bounds for item in self.fills),
            *(item.bounds for item in self.collisions),
            *(item.bounds for item in self.events if item.bounds),
            *(item.bounds for item in self.encounters),
            *(self.boundary.openings if self.boundary else []),
        ]
        if any(not point_ok(point) for point in points):
            raise ValueError(f"map {self.slug!r} contains an out-of-bounds point")
        if any(not rect_ok(rect) for rect in rects):
            raise ValueError(f"map {self.slug!r} contains an out-of-bounds rectangle")
        ids = [
            *(item.slug for item in self.paths),
            *(item.slug for item in self.fills),
            *(item.slug for item in self.props),
            *(item.slug for item in self.collisions),
            *(item.slug for item in self.warps),
            *(item.slug for item in self.events),
            *(item.slug for item in self.encounters),
        ]
        if len(ids) != len(set(ids)):
            raise ValueError(f"map {self.slug!r} has duplicate authored IDs")
        return self


class PartyMonster(StrictModel):
    slug: str
    level: int = Field(ge=1, le=100)
    gender: Literal["male", "female", "neuter"] = "neuter"
    money_mod: float = Field(default=1, gt=0)
    exp_req_mod: float = Field(default=1, gt=0)


class NpcSpec(StrictModel):
    slug: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    sprite: str
    combat_sheet: str | None = None
    template: str | None = None
    party: list[PartyMonster] = Field(default_factory=list)
    persistence: bool = False


class EncounterEntry(StrictModel):
    monster: str
    encounter_rate: int = Field(gt=0)
    level_range: tuple[int, int]

    @model_validator(mode="after")
    def ordered_levels(self) -> EncounterEntry:
        if self.level_range[0] > self.level_range[1]:
            raise ValueError("encounter level range must be ordered")
        return self


class EncounterTable(StrictModel):
    slug: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    entries: list[EncounterEntry] = Field(min_length=1)


class EpisodeSpec(StrictModel):
    metadata: EpisodeMetadata
    palettes: dict[str, PaletteSpec]
    maps: list[MapSpec] = Field(min_length=1)
    npcs: list[NpcSpec] = Field(default_factory=list)
    encounters: list[EncounterTable] = Field(default_factory=list)
    dialogue: dict[str, str]

    @model_validator(mode="after")
    def references_exist(self) -> EpisodeSpec:
        map_ids = [item.slug for item in self.maps]
        if len(map_ids) != len(set(map_ids)):
            raise ValueError("map slugs must be unique")
        maps = set(map_ids)
        if self.metadata.start_map not in maps:
            raise ValueError("starting map does not exist")
        npc_ids = [item.slug for item in self.npcs]
        if len(npc_ids) != len(set(npc_ids)):
            raise ValueError("NPC slugs must be unique")
        npcs = set(npc_ids)
        tables = {item.slug for item in self.encounters}
        for map_spec in self.maps:
            if map_spec.palette not in self.palettes:
                raise ValueError(f"map {map_spec.slug!r} has missing palette")
            palette = self.palettes[map_spec.palette]
            visuals = {map_spec.base_tile}
            visuals.update(path.tile for path in map_spec.paths)
            visuals.update(fill.tile for fill in map_spec.fills)
            visuals.update(prop.visual for prop in map_spec.props)
            if map_spec.boundary:
                visuals.add(map_spec.boundary.tile)
            missing_visuals = visuals - set(palette.tiles) - set(palette.stamps)
            if missing_visuals:
                raise ValueError(
                    f"map {map_spec.slug!r} has missing palette visuals: "
                    f"{sorted(missing_visuals)}"
                )
            for warp in map_spec.warps:
                if warp.target_map not in maps:
                    raise ValueError(f"warp {warp.slug!r} targets missing map")
            missing_npcs = {item.slug for item in map_spec.npcs} - npcs
            if missing_npcs:
                raise ValueError(
                    f"map {map_spec.slug!r} places missing NPCs: {sorted(missing_npcs)}"
                )
            missing_tables = {item.table for item in map_spec.encounters} - tables
            if missing_tables:
                raise ValueError(
                    f"map {map_spec.slug!r} uses missing encounters: {sorted(missing_tables)}"
                )
        return self


def load_episode(path: Path) -> EpisodeSpec:
    raw = yaml.safe_load(path.read_text(encoding="utf-8"))
    return EpisodeSpec.model_validate(raw)
