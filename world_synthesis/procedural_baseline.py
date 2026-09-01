"""Fair deterministic baseline generator for the Deep Forest benchmark.

This generator receives the common brief and applies generic outdoor rules. It
does not use the structured design reasoning, critique, or revision loop used
by variant C.
"""

from __future__ import annotations

import random
from pathlib import Path

import yaml

from world_synthesis.schema import WorldSpec


def generate_deep_forest(seed: int = 1937) -> WorldSpec:
    """Create a competent but deliberately single-pass forest route."""
    rng = random.Random(seed)
    bends = [
        (20, 43),
        (20 + rng.randint(-2, 2), 37),
        (17 + rng.randint(-2, 2), 31),
        (20 + rng.randint(-2, 2), 25),
        (18 + rng.randint(-2, 2), 18),
        (21 + rng.randint(-2, 2), 11),
        (20, 0),
    ]

    def points(values: list[tuple[int, int]]) -> list[dict[str, int]]:
        return [{"x": x, "y": y} for x, y in values]

    def threshold(
        map_id: str,
        name: str,
        target_map: str,
        at_y: int,
        target_y: int,
        facing: str,
    ) -> dict[str, object]:
        return {
            "id": map_id,
            "name": name,
            "map_type": "settlement_threshold",
            "narrative_role": "Benchmark transition fixture.",
            "emotional_role": "Safe threshold.",
            "visual_identity": "Forest gate using the frozen palette.",
            "width": 12,
            "height": 10,
            "base_terrain": "forest_floor",
            "boundary": {
                "kind": "forest",
                "depth": 3,
                "density": 0.58,
                "falloff_per_cell": 0.16,
            },
            "player_spawn": {"x": 6, "y": 5},
            "primary_path": {
                "id": "gate_path",
                "role": "critical",
                "width": 3,
                "points": points([(6, 9), (6, 0)]),
            },
            "warps": [
                {
                    "id": f"{map_id}_return",
                    "at": {"x": 6, "y": at_y},
                    "facing": facing,
                    "target_map": target_map,
                    "target": {"x": 20, "y": target_y},
                }
            ],
            "revision": 1,
        }

    main: dict[str, object] = {
        "id": "deep_forest_a_route",
        "name": "Mossveil Passage",
        "map_type": "route",
        "narrative_role": "Connect two unseen woodland settlements.",
        "emotional_role": "Compression, clearing, return to compression.",
        "visual_identity": "Dark forest floor, pine walls and pale trail.",
        "width": 40,
        "height": 44,
        "base_terrain": "forest_floor",
        "boundary": {
            "kind": "forest",
            "depth": 4,
            "density": 0.76,
            "falloff_per_cell": 0.13,
        },
        "player_spawn": {"x": 20, "y": 40},
        "grant_starter": True,
        "primary_path": {
            "id": "generated_spine",
            "role": "critical",
            "width": 3,
            "points": points(bends),
        },
        "secondary_paths": [
            {
                "id": "generated_west_loop",
                "role": "optional",
                "width": 2,
                "points": points(
                    [bends[2], (9, 29), (7, 23), (12, 19), bends[4]]
                ),
            }
        ],
        "landmarks": [
            {
                "id": "three_stones",
                "name": "The Three Stones",
                "role": "dominant",
                "kind": "standing_stones",
                "anchor": {"x": 23, "y": 22},
                "footprint": {"x": 20, "y": 19, "width": 8, "height": 7},
                "description": "A mechanically selected boulder clearing beside the trail.",
            }
        ],
        "zones": [
            {"id": "west_thicket", "kind": "forest", "bounds": {"x": 1, "y": 3, "width": 12, "height": 38}, "density": 0.55, "tags": ["pine"]},
            {"id": "east_thicket", "kind": "forest", "bounds": {"x": 27, "y": 3, "width": 12, "height": 38}, "density": 0.58, "tags": ["pine"]},
            {"id": "stone_clearing", "kind": "safe", "bounds": {"x": 19, "y": 18, "width": 10, "height": 9}, "density": 0.0, "tags": ["rest"]},
            {"id": "west_encounter_cover", "kind": "encounter", "bounds": {"x": 4, "y": 22, "width": 9, "height": 8}, "density": 0.52, "tags": ["tall_grass"]},
            {"id": "north_encounter_cover", "kind": "encounter", "bounds": {"x": 23, "y": 5, "width": 10, "height": 9}, "density": 0.48, "tags": ["tall_grass"]},
        ],
        "warps": [
            {"id": "south_exit", "at": {"x": 20, "y": 43}, "facing": "down", "target_map": "df_a_south_threshold", "target": {"x": 6, "y": 1}},
            {"id": "north_exit", "at": {"x": 20, "y": 0}, "facing": "up", "target_map": "df_a_north_threshold", "target": {"x": 6, "y": 8}},
        ],
        "npcs": [
            {"id": "df_a_ranger", "role": "Southern path guide", "at": {"x": bends[1][0], "y": bends[1][1]}, "sprite": "scientist", "dialogue": "The pale trail stays honest even when the trees crowd close.", "mandatory": True},
            {"id": "df_a_forager", "role": "Optional-loop trainer", "at": {"x": 9, "y": 27}, "sprite": "miner_green", "dialogue": "I came for shelf mushrooms and found a worthy detour.", "trainer": True, "party": ["shybulb"]},
            {"id": "df_a_scout", "role": "Northern trainer", "at": {"x": bends[5][0], "y": bends[5][1]}, "sprite": "knight", "dialogue": "The canopy opens ahead. First, show me your trail sense.", "trainer": True, "party": ["squabbit"]},
        ],
        "encounter_zones": [
            {"id": "west_encounters", "bounds": {"x": 4, "y": 22, "width": 9, "height": 8}, "table": "df_a_forest", "probability": 9},
            {"id": "north_encounters", "bounds": {"x": 23, "y": 5, "width": 10, "height": 9}, "table": "df_a_forest", "probability": 9},
        ],
        "secrets": [
            {"id": "df_a_hidden_tonic", "at": {"x": 7, "y": 23}, "reward": "potion", "clue": "A narrow western trail ends beside an unusually pale shrub."}
        ],
        "props": [
            {"id": "stone_north", "kind": "boulder", "at": {"x": 24, "y": 20}, "blocks_movement": True, "semantic_role": "Landmark component"},
            {"id": "stone_east", "kind": "boulder", "at": {"x": 26, "y": 22}, "blocks_movement": True, "semantic_role": "Landmark component"},
            {"id": "stone_south", "kind": "boulder", "at": {"x": 24, "y": 24}, "blocks_movement": True, "semantic_role": "Landmark component"},
            {"id": "loop_sign", "kind": "sign", "at": {"x": bends[2][0] - 3, "y": bends[2][1]}, "blocks_movement": True, "semantic_role": "Optional route cue"},
        ],
        "pacing_notes": [
            "A generic winding spine connects the paired exits.",
            "A generated western branch leaves and rejoins the spine.",
            "The central safe rectangle contains the selected landmark.",
        ],
        "revision": 1,
    }

    raw = {
        "metadata": {
            "format_version": "1.0",
            "experiment_id": "deep_forest_a",
            "seed": seed,
            "authoring_status": "reviewed",
            "campaign_name": "Mossveil Passage",
            "starter_monster": "cardiling",
            "starter_level": 7,
            "trainer_post_battle_dialogue": "You read this forest better than I expected.",
        },
        "encounter_tables": [
            {
                "id": "df_a_forest",
                "entries": [
                    {"monster": "shybulb", "encounter_rate": 4, "level_min": 4, "level_max": 6},
                    {"monster": "squabbit", "encounter_rate": 3, "level_min": 5, "level_max": 7},
                    {"monster": "elofly", "encounter_rate": 2, "level_min": 4, "level_max": 6},
                ],
            }
        ],
        "region": {
            "id": "deep_forest_a_region",
            "name": "Mossveil Passage",
            "theme": "A practical forest crossing generated from baseline rules.",
            "history": "No separate region bible was used for this baseline.",
            "environment": "Dense temperate woodland.",
            "economy": ["foraging", "courier traffic"],
            "conflict": "The trail is narrowing under new growth.",
            "story_hook": "Cross between two conceptual settlements.",
            "progression": ["Enter from the south.", "Follow the trail north."],
            "visual_motifs": ["pines", "pale path", "mossy stones"],
            "creature_ecology": ["Shybulb gather in damp understory."],
            "settlements": [
                {"id": "southstead", "name": "Southstead", "role": "Conceptual south settlement", "economy": ["foraging"], "visual_motifs": ["timber"]},
                {"id": "northstead", "name": "Northstead", "role": "Conceptual north settlement", "economy": ["couriers"], "visual_motifs": ["stone"]},
            ],
            "maps": [
                threshold("df_a_south_threshold", "Mossveil Threshold", "deep_forest_a_route", 0, 42, "up"),
                threshold("df_a_north_threshold", "Mossveil Threshold", "deep_forest_a_route", 9, 1, "down"),
                main,
            ],
        },
    }
    return WorldSpec.model_validate(raw)


def write_baseline(output: Path, seed: int = 1937) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    world = generate_deep_forest(seed)
    output.write_text(
        yaml.safe_dump(world.model_dump(mode="json"), sort_keys=False),
        encoding="utf-8",
    )
    return output


if __name__ == "__main__":
    root = Path(__file__).resolve().parents[1]
    print(
        write_baseline(
            root
            / "benchmarks"
            / "generated"
            / "a_procedural"
            / "deep_forest"
            / "world_spec.yaml"
        )
    )
