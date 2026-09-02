from __future__ import annotations

import hashlib
import json
import xml.etree.ElementTree as ET
from collections import deque
from pathlib import Path

import pygame as pg

from tuxemon.database.data import ModData
from tuxemon.database.loader import ModelLoader
from tuxemon.database.utils import load_config
from tuxemon.db import load_model_map
from tuxemon.map.loader import TMXMapLoader
from tuxemon.prepare import headless_init
from tuxemon.user_config import CONFIG
from world_synthesis.production_slice.compiler import (
    build_episode,
    compile_map,
)
from world_synthesis.production_slice.playtest import (
    collect_evaluation,
    create_session,
)
from world_synthesis.production_slice.render import render_episode
from world_synthesis.production_slice.schema import EventTrigger, load_episode
from world_synthesis.production_slice.validation import validate_episode

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "production_slice" / "low_bell" / "episode.yaml"


def test_low_bell_design_lock_loads_as_production_episode() -> None:
    episode = load_episode(SPEC)
    assert episode.metadata.slug == "low_bell"
    assert episode.metadata.target_minutes == (60, 90)
    assert len(episode.maps) == 7
    assert len(episode.npcs) == 17
    assert {item.slug for item in episode.encounters} == {
        "low_bell_south_wild",
        "low_bell_highland_wild",
        "low_bell_quarry_wild",
    }


def test_golden_path_has_real_battles_and_resolution_action() -> None:
    episode = load_episode(SPEC)
    events = {
        event.slug: event
        for map_spec in episode.maps
        for event in map_spec.events
    }
    assert (
        "choice_monster anoleaf:flounce:rockitten,low_bell_starter_choice"
        in events["choose_starter"].actions
    )
    tutorial = events["frightened_shybulb_tutorial"]
    assert "wild_encounter shybulb,3" in tutorial.actions
    assert "set_variable low_bell_tutorial_cleared:yes" in tutorial.actions
    assert tutorial.actions.index(
        "wild_encounter shybulb,3"
    ) < tutorial.actions.index("set_variable low_bell_tutorial_cleared:yes")
    assert (
        "not variable_set low_bell_tutorial_cleared:yes" in tutorial.conditions
    )
    assert all(
        "battle_outcome player,won,wild_encounter" not in condition
        for event in events.values()
        for condition in event.conditions
    )
    assert (
        "start_battle player,low_bell_rook" in events["rook_challenge"].actions
    )
    assert (
        "start_battle player,low_bell_jemuar"
        in events["jemuar_climax"].actions
    )
    assert events["damp_resonant_assembly"].trigger == EventTrigger.INTERACT
    assert (
        "set_variable low_bell_story:resolved"
        in events["damp_resonant_assembly"].actions
    )
    assert (
        "set_variable low_bell_episode_complete:yes"
        in events["resolution_prompt"].actions
    )


def test_village_arrival_is_reentry_safe_and_nonmodal() -> None:
    episode = load_episode(SPEC)
    events = {
        event.slug: event
        for map_spec in episode.maps
        for event in map_spec.events
    }
    arrival = events["village_arrival_scene"]
    assert arrival.trigger == EventTrigger.TOUCH
    assert arrival.actions[0] == "set_variable low_bell_story:investigation"
    assert all(
        not action.startswith("translated_dialog ")
        for action in arrival.actions
    )


def test_touch_events_do_not_chain_adjacent_modal_dialog_states() -> None:
    episode = load_episode(SPEC)
    for map_spec in episode.maps:
        for event in map_spec.events:
            if event.trigger != EventTrigger.TOUCH:
                continue
            has_adjacent_dialogs = any(
                first.startswith("translated_dialog ")
                and second.startswith("translated_dialog ")
                for first, second in zip(event.actions, event.actions[1:])
            )
            assert not has_adjacent_dialogs, f"{map_spec.slug}:{event.slug}"


def test_main_progression_does_not_consume_side_quest_state() -> None:
    episode = load_episode(SPEC)
    mandatory = [
        event
        for map_spec in episode.maps
        for event in map_spec.events
        if event.mandatory
    ]
    assert mandatory
    assert all(
        "sq_" not in condition
        for event in mandatory
        for condition in event.conditions
    )
    assert all(
        "sq_" not in action for event in mandatory for action in event.actions
    )


def test_content_completion_budget_and_optional_quests() -> None:
    episode = load_episode(SPEC)
    events = {
        event.slug: event
        for map_spec in episode.maps
        for event in map_spec.events
    }
    battle_actions = [
        action
        for event in events.values()
        for action in event.actions
        if action.startswith(("start_battle ", "wild_encounter "))
    ]
    assert len(battle_actions) == 7
    assert (
        "set_variable low_bell_sq_squabbit_complete:yes"
        in events["jori_squabbit_return"].actions
    )
    assert (
        "set_variable low_bell_sq_names_complete:yes"
        in events["mara_names_complete"].actions
    )
    assert all(
        not event.mandatory
        for event in (
            events["jori_squabbit_return"],
            events["mara_names_complete"],
        )
    )
    assert {
        "low_bell_secret_south:yes",
        "low_bell_secret_pass:yes",
        "low_bell_secret_quarry:yes",
    } <= {
        action.removeprefix("set_variable ")
        for event in events.values()
        for action in event.actions
        if action.startswith("set_variable low_bell_secret_")
    }


def test_puzzle_and_shortcut_are_stateful_and_nonmandatory() -> None:
    episode = load_episode(SPEC)
    maps = {map_spec.slug: map_spec for map_spec in episode.maps}
    events = {
        event.slug: event
        for map_spec in episode.maps
        for event in map_spec.events
    }
    assert (
        "set_variable low_bell_puzzle_stage:runoff"
        in events["puzzle_runoff_first"].actions
    )
    assert (
        "set_variable low_bell_puzzle_stage:brace"
        in events["puzzle_cradle_correct"].actions
    )
    assert (
        "set_variable low_bell_shortcut_unlocked:yes"
        in events["puzzle_hoist_correct"].actions
    )
    shortcut_warps = [
        warp
        for map_spec in maps.values()
        for warp in map_spec.warps
        if "shortcut" in warp.slug
    ]
    assert len(shortcut_warps) == 2
    assert all(not warp.mandatory for warp in shortcut_warps)
    assert all(
        "is variable_set low_bell_shortcut_unlocked:yes" in warp.conditions
        for warp in shortcut_warps
    )


def test_six_or_more_village_characters_have_resolved_dialogue() -> None:
    episode = load_episode(SPEC)
    village = next(
        item for item in episode.maps if item.slug == "low_bell_ashenbell"
    )
    resolved_npcs = {
        event.npc
        for event in village.events
        if event.trigger == EventTrigger.TALK
        and "is variable_set low_bell_story:resolved" in event.conditions
    }
    assert len(resolved_npcs - {None}) >= 6


def test_all_mandatory_anchors_are_statically_reachable() -> None:
    episode = load_episode(SPEC)
    entries: dict[str, set[tuple[int, int]]] = {
        map_spec.slug: set() for map_spec in episode.maps
    }
    entries[episode.metadata.start_map].add(episode.metadata.start_position)
    for map_spec in episode.maps:
        for warp in map_spec.warps:
            entries[warp.target_map].add((warp.target.x, warp.target.y))

    for map_spec in episode.maps:
        layout = compile_map(episode, map_spec)
        queue = deque(entries[map_spec.slug])
        reachable = set(queue)
        while queue:
            x, y = queue.popleft()
            for cell in ((x - 1, y), (x + 1, y), (x, y - 1), (x, y + 1)):
                cx, cy = cell
                if not (
                    0 <= cx < map_spec.width and 0 <= cy < map_spec.height
                ):
                    continue
                if cell in layout.blocked or cell in reachable:
                    continue
                reachable.add(cell)
                queue.append(cell)

        for event in (item for item in map_spec.events if item.mandatory):
            if event.trigger == EventTrigger.INIT:
                continue
            bounds = (
                event.bounds.cells()
                if event.bounds
                else {(event.at.x, event.at.y)}
            )
            adjacent = {
                neighbor
                for x, y in bounds
                for neighbor in (
                    (x - 1, y),
                    (x + 1, y),
                    (x, y - 1),
                    (x, y + 1),
                )
            }
            assert reachable & (bounds | adjacent), (
                f"{map_spec.slug}:{event.slug}"
            )
        for warp in (item for item in map_spec.warps if item.mandatory):
            assert (warp.at.x, warp.at.y) in reachable, (
                f"{map_spec.slug}:{warp.slug}"
            )


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
            "mod_dependencies": {
                **base.mod_dependencies,
                "low_bell": ["tuxemon"],
            },
        }
    )
    database = ModData(config, ModelLoader(load_model_map(config.model_map)))
    database.preload()
    database.load()
    assert "low_bell_nera" in database.database["npc"]
    assert "low_bell_rook" in database.database["npc"]
    assert "low_bell_south_wild" in database.database["encounter"]


def test_area_palettes_use_reviewed_existing_assets() -> None:
    episode = load_episode(SPEC)
    palettes = {map_spec.slug: map_spec.palette for map_spec in episode.maps}
    assert "prototype_outdoor" not in palettes.values()
    assert palettes["low_bell_south_approach"] == "core_outdoor"
    assert palettes["low_bell_ashenbell"] == "core_city"
    assert palettes["low_bell_highland_pass"] == "core_highland"
    assert palettes["low_bell_quarry_exterior"] == "core_quarry"
    assert palettes["low_bell_quarry_lower"] == "core_quarry"
    for palette_slug in set(palettes.values()):
        source = episode.palettes[palette_slug].source
        assert (
            (REPO / "mods" / "low_bell" / "maps" / source).resolve().is_file()
        )


def test_static_review_renders_are_deterministic() -> None:
    episode = load_episode(SPEC)
    first = render_episode(episode, REPO)
    before = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in first
    }
    second = render_episode(episode, REPO)
    after = {
        path: hashlib.sha256(path.read_bytes()).hexdigest() for path in second
    }
    assert before == after
    assert len(second) == len(episode.maps) * 2


def test_flow_style_battle_conditions_survive_tmx_compilation() -> None:
    build_episode(SPEC, REPO)
    expected = {
        "not battle_outcome player,won,low_bell_garden_caper",
        "not battle_outcome player,won,low_bell_rockat_guard",
    }
    actual = {
        prop.attrib.get("value", "")
        for path in (REPO / "mods" / "low_bell" / "maps").glob("*.tmx")
        for prop in ET.parse(path).getroot().findall(".//property")
    }
    assert expected <= actual


def test_automated_acceptance_passes() -> None:
    contract = SPEC.with_name("acceptance.yaml")
    report = validate_episode(SPEC, contract, REPO)
    assert report["passed"]
    assert all(check["passed"] for check in report["mechanically_verified"])
    assert report["requires_human_playtest"]


def test_human_questionnaire_is_separate_and_has_no_aggregate(
    tmp_path: Path, monkeypatch
) -> None:
    session_id, session_path = create_session(tmp_path)
    answers = iter(
        [
            "yes",
            "8",
            "7",
            "8",
            "9",
            "7",
            "8",
            "6",
            "8",
            "The lower pass dragged.",
            "Nera, Mara, Tovin",
            "yes",
            "Iven's first explanation.",
            "no",
            "",
            "Dampening the assembly.",
            "yes",
        ]
    )
    monkeypatch.setattr("builtins.input", lambda _prompt: next(answers))
    output = collect_evaluation(session_id, session_path, tmp_path)
    assert output is not None
    response = json.loads(output.read_text(encoding="utf-8"))
    assert response["aggregate_score"] is None
    assert len(response["ratings"]) == 8
    assert "answers" in response
