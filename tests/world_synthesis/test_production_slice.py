from __future__ import annotations

import hashlib
import xml.etree.ElementTree as ET
from pathlib import Path

import pygame as pg

from tuxemon.database.data import ModData
from tuxemon.database.loader import ModelLoader
from tuxemon.database.utils import load_config
from tuxemon.db import load_model_map
from tuxemon.map.loader import TMXMapLoader
from tuxemon.prepare import headless_init
from tuxemon.user_config import CONFIG
from world_synthesis.production_slice.compiler import build_episode
from world_synthesis.production_slice.schema import EventTrigger, load_episode

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "production_slice" / "low_bell" / "episode.yaml"


def test_low_bell_design_lock_loads_as_production_episode() -> None:
    episode = load_episode(SPEC)
    assert episode.metadata.slug == "low_bell"
    assert episode.metadata.target_minutes == (60, 90)
    assert len(episode.maps) == 7
    assert len(episode.npcs) == 14
    assert {item.slug for item in episode.encounters} == {
        "low_bell_south_wild",
        "low_bell_highland_wild",
        "low_bell_quarry_wild",
    }


def test_golden_path_has_real_battles_and_resolution_action() -> None:
    episode = load_episode(SPEC)
    events = {event.slug: event for map_spec in episode.maps for event in map_spec.events}
    assert "choice_monster anoleaf:flounce:rockitten,low_bell_starter_choice" in events[
        "choose_starter"
    ].actions
    assert "wild_encounter shybulb,3" in events["frightened_shybulb_tutorial"].actions
    assert "start_battle player,low_bell_rook" in events["rook_challenge"].actions
    assert "start_battle player,low_bell_jemuar" in events["jemuar_climax"].actions
    assert events["damp_resonant_assembly"].trigger == EventTrigger.INTERACT
    assert "set_variable low_bell_story:resolved" in events[
        "damp_resonant_assembly"
    ].actions
    assert "set_variable low_bell_episode_complete:yes" in events[
        "resolution_prompt"
    ].actions


def test_main_progression_does_not_consume_side_quest_state() -> None:
    episode = load_episode(SPEC)
    mandatory = [
        event
        for map_spec in episode.maps
        for event in map_spec.events
        if event.mandatory
    ]
    assert mandatory
    assert all("sq_" not in condition for event in mandatory for condition in event.conditions)
    assert all("sq_" not in action for event in mandatory for action in event.actions)


def test_all_interactions_declare_anchors() -> None:
    episode = load_episode(SPEC)
    for map_spec in episode.maps:
        for event in map_spec.events:
            if event.trigger in {EventTrigger.INTERACT, EventTrigger.TALK}:
                assert event.anchor_required, f"{map_spec.slug}:{event.slug}"


def test_build_is_deterministic() -> None:
    build_episode(SPEC, REPO)
    maps = REPO / "mods" / "low_bell" / "maps"
    before = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(maps.glob("*.tmx"))
    }
    build_episode(SPEC, REPO)
    after = {
        path.name: hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(maps.glob("*.tmx"))
    }
    assert before == after
    assert len(after) == 7


def test_generated_tmx_references_only_declared_maps() -> None:
    episode = load_episode(SPEC)
    map_ids = {item.slug for item in episode.maps}
    build_episode(SPEC, REPO)
    for path in (REPO / "mods" / "low_bell" / "maps").glob("*.tmx"):
        root = ET.parse(path).getroot()
        assert int(root.attrib["width"]) >= 8
        assert int(root.attrib["height"]) >= 8
        assert root.find("objectgroup[@name='Collisions']") is not None
        assert root.find("objectgroup[@name='Events']") is not None
        for prop in root.findall(".//property"):
            action = prop.attrib.get("value", "")
            if not action.startswith("transition_teleport "):
                continue
            target = action.split(",", 2)[1].removesuffix(".tmx")
            assert target in map_ids


def test_real_tuxemon_loader_reads_all_production_maps(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    episode = load_episode(SPEC)
    build_episode(SPEC, REPO)
    context = headless_init()
    pg.display.set_mode((320, 240))
    try:
        loader = TMXMapLoader()
        for map_spec in episode.maps:
            path = REPO / "mods" / "low_bell" / "maps" / f"{map_spec.slug}.tmx"
            loaded = loader.load(str(path), context)
            assert loaded.size == (map_spec.width, map_spec.height)
            assert loaded.events
            assert loaded.collision_map
    finally:
        pg.display.quit()


def test_low_bell_database_overlay_activates(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    monkeypatch.setattr(CONFIG, "mods", ["tuxemon", "low_bell"])
    build_episode(SPEC, REPO)
    headless_init()
    base = load_config(str(REPO / "mods" / "db_config.yaml"))
    tables = dict(base.mod_tables)
    tables["low_bell"] = ["npc", "encounter"]
    config = base.model_copy(
        update={
            "active_mods": ["tuxemon", "low_bell"],
            "mod_activation": {**base.mod_activation, "low_bell": True},
            "mod_tables": tables,
            "mod_dependencies": {**base.mod_dependencies, "low_bell": ["tuxemon"]},
        }
    )
    database = ModData(config, ModelLoader(load_model_map(config.model_map)))
    database.preload()
    database.load()
    assert "low_bell_nera" in database.database["npc"]
    assert "low_bell_rook" in database.database["npc"]
    assert "low_bell_south_wild" in database.database["encounter"]
