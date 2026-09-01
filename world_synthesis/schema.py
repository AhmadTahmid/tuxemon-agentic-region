"""Typed, engine-agnostic design contracts for the synthesis experiment."""

from __future__ import annotations

from enum import StrEnum
from pathlib import Path
from typing import Annotated, Literal

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


class MapType(StrEnum):
    ROUTE = "route"
    SETTLEMENT_THRESHOLD = "settlement_threshold"
    SETTLEMENT = "settlement"
    DUNGEON = "dungeon"


class Metadata(StrictModel):
    format_version: Literal["1.0"] = "1.0"
    experiment_id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    seed: int
    authoring_status: Literal["draft", "reviewed"]


class Settlement(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    role: str
    economy: list[str]
    visual_motifs: list[str]


class Landmark(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    role: Literal["dominant", "secondary"]
    kind: str
    anchor: Point
    footprint: Rect
    description: str


class PathSpec(StrictModel):
    id: str
    role: Literal["critical", "optional"]
    width: int = Field(ge=1, le=7)
    points: list[Point] = Field(min_length=2)


class Zone(StrictModel):
    id: str
    kind: Literal["meadow", "forest", "river", "encounter", "safe", "secret"]
    bounds: Rect
    density: float = Field(ge=0, le=1, default=0)
    tags: list[str] = Field(default_factory=list)


class Warp(StrictModel):
    id: str
    at: Point
    facing: Literal["up", "down", "left", "right"]
    target_map: str
    target: Point
    mandatory: bool = True


class Character(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    role: str
    at: Point
    sprite: str
    dialogue: str
    trainer: bool = False
    party: list[str] = Field(default_factory=list)
    mandatory: bool = False


class EncounterZone(StrictModel):
    id: str
    bounds: Rect
    table: str
    probability: int = Field(ge=0, le=100)


class Secret(StrictModel):
    id: str
    at: Point
    reward: str
    clue: str


class EnvironmentalFeature(StrictModel):
    id: str
    kind: Literal["river", "bridge", "pond", "grove", "fence", "flowers"]
    bounds: Rect
    blocks_movement: bool
    notes: str = ""


class StoryEvent(StrictModel):
    id: str
    at: Point
    trigger: str
    actions: list[str]


class QuestStep(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    kind: Literal["npc", "event", "warp", "secret"]
    reference: str


class Quest(StrictModel):
    id: str
    summary: str
    steps: list[QuestStep] = Field(min_length=1)
    reward: str


class MapSpec(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    map_type: MapType
    narrative_role: str
    emotional_role: str
    visual_identity: str
    width: int = Field(ge=8, le=200)
    height: int = Field(ge=8, le=200)
    player_spawn: Point
    primary_path: PathSpec
    secondary_paths: list[PathSpec] = Field(default_factory=list)
    landmarks: list[Landmark] = Field(default_factory=list)
    zones: list[Zone] = Field(default_factory=list)
    warps: list[Warp] = Field(default_factory=list)
    npcs: list[Character] = Field(default_factory=list)
    encounter_zones: list[EncounterZone] = Field(default_factory=list)
    secrets: list[Secret] = Field(default_factory=list)
    environmental_features: list[EnvironmentalFeature] = Field(
        default_factory=list
    )
    events: list[StoryEvent] = Field(default_factory=list)
    pacing_notes: list[str] = Field(default_factory=list)
    revision: int = Field(ge=1)

    @model_validator(mode="after")
    def coordinates_fit(self) -> MapSpec:
        def point_ok(point: Point) -> bool:
            return point.x < self.width and point.y < self.height

        points = [self.player_spawn]
        points.extend(
            p
            for path in [self.primary_path, *self.secondary_paths]
            for p in path.points
        )
        points.extend(item.anchor for item in self.landmarks)
        points.extend(item.at for item in self.warps)
        points.extend(item.at for item in self.npcs)
        points.extend(item.at for item in self.secrets)
        points.extend(item.at for item in self.events)
        if any(not point_ok(point) for point in points):
            raise ValueError(
                f"map {self.id!r} contains a point outside its bounds"
            )
        rects = [item.footprint for item in self.landmarks]
        rects.extend(item.bounds for item in self.zones)
        rects.extend(item.bounds for item in self.encounter_zones)
        rects.extend(item.bounds for item in self.environmental_features)
        if any(
            rect.x + rect.width > self.width
            or rect.y + rect.height > self.height
            for rect in rects
        ):
            raise ValueError(
                f"map {self.id!r} contains a rectangle outside its bounds"
            )
        return self


class Region(StrictModel):
    id: str = Field(pattern=r"^[a-z][a-z0-9_]*$")
    name: str
    theme: str
    history: str
    environment: str
    economy: list[str]
    conflict: str
    story_hook: str
    progression: list[str]
    visual_motifs: list[str]
    creature_ecology: list[str]
    settlements: list[Settlement]
    maps: list[MapSpec]
    quests: list[Quest] = Field(default_factory=list)


class WorldSpec(StrictModel):
    metadata: Metadata
    region: Region

    @model_validator(mode="after")
    def references_are_unique_and_valid(self) -> WorldSpec:
        map_ids = [item.id for item in self.region.maps]
        if len(map_ids) != len(set(map_ids)):
            raise ValueError("map IDs must be unique")
        ids = set(map_ids)
        for map_spec in self.region.maps:
            missing = [
                warp.target_map
                for warp in map_spec.warps
                if warp.target_map not in ids
            ]
            if missing:
                raise ValueError(
                    f"map {map_spec.id!r} has missing warp targets: {missing}"
                )
        return self


def load_world_spec(path: Path) -> WorldSpec:
    data = yaml.safe_load(path.read_text(encoding="utf-8"))
    return WorldSpec.model_validate(data)


WorldEntity = Annotated[
    Landmark
    | Zone
    | Warp
    | Character
    | EncounterZone
    | Secret
    | EnvironmentalFeature,
    Field(discriminator=None),
]
