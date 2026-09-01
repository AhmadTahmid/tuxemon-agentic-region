"""Repeatable design-grammar critic for revision history.

This is intentionally transparent. It does not pretend a formula can replace
human playtesting; it catches missing authored ingredients and records concrete
revision advice.
"""

from __future__ import annotations

import json
from pathlib import Path

from world_synthesis.compiler import CompiledLayout

RUBRIC = (
    "visual_composition",
    "navigation_readability",
    "landmark_quality",
    "exploration",
    "environmental_storytelling",
    "gameplay_pacing",
    "npc_placement",
    "world_coherence",
    "secret_reward_placement",
    "memorability",
)


def critique(layout: CompiledLayout) -> dict[str, object]:
    spec = layout.map_spec
    dominant = sum(item.role == "dominant" for item in spec.landmarks)
    secondary = sum(item.role == "secondary" for item in spec.landmarks)
    loops = sum(item.role == "optional" for item in spec.secondary_paths)
    trainers = sum(item.trainer for item in spec.npcs)
    scores = {
        "visual_composition": min(
            10, 5 + dominant + secondary + (1 if loops else 0)
        ),
        "navigation_readability": min(
            10,
            6
            + bool(spec.warps)
            + (1 if len(spec.primary_path.points) >= 5 else 0),
        ),
        "landmark_quality": min(10, 4 + dominant * 3 + min(secondary, 2)),
        "exploration": min(10, 3 + loops * 2 + len(spec.secrets) * 2),
        "environmental_storytelling": min(
            10,
            4
            + len(spec.landmarks)
            + min(len(spec.events), 2)
            + bool(spec.pacing_notes),
        ),
        "gameplay_pacing": min(
            10, 4 + min(len(spec.pacing_notes), 4) + bool(spec.encounter_zones)
        ),
        "npc_placement": min(10, 4 + min(len(spec.npcs), 4) + bool(trainers)),
        "world_coherence": min(
            10, 6 + bool(spec.visual_identity) + bool(spec.warps)
        ),
        "secret_reward_placement": min(
            10, 3 + min(len(spec.secrets), 2) * 3 + bool(loops)
        ),
        "memorability": min(
            10, 4 + dominant * 2 + secondary + bool(spec.events)
        ),
    }
    average = round(sum(scores.values()) / len(scores), 2)
    strengths: list[str] = []
    weaknesses: list[str] = []
    recommendations: list[str] = []
    if dominant:
        strengths.append(
            "A dominant landmark anchors both composition and traversal."
        )
    if len(spec.primary_path.points) >= 5:
        strengths.append(
            "The critical path changes direction and creates staged reveals."
        )
    if len(spec.npcs) >= 3:
        strengths.append(
            "NPC roles cluster around plausible route activities rather than random spacing."
        )
    if not loops:
        weaknesses.append(
            "There is no true optional exploration loop; leaving the road only creates open-field wandering."
        )
        recommendations.append(
            "Add a secondary path that departs and rejoins the critical path around a distinct sub-area."
        )
    if not secondary:
        weaknesses.append(
            "The bridge has no secondary landmark to balance its visual weight."
        )
        recommendations.append(
            "Compose a smaller activity landmark off-axis from the bridge."
        )
    if spec.secrets and not loops:
        weaknesses.append(
            "The secret is mechanically reachable but weakly telegraphed by circulation."
        )
        recommendations.append(
            "Place the secret along the optional loop and frame it with a visible gap or prop clue."
        )
    if not weaknesses:
        weaknesses.extend(
            [
                "Tile-level edge treatment remains limited by the selected prototype atlas.",
                "Static rendering cannot judge moment-to-moment trainer interruption pacing.",
                "Threshold maps prove topology but do not yet deliver settlement context.",
            ]
        )
        recommendations.extend(
            [
                "Playtest encounter frequency and trainer sightline timing in the real client.",
                "Replace the prototype atlas only after the experimental design comparison is stable.",
                "Do not expand the region until navigation feedback from this route is recorded.",
            ]
        )
    return {
        "format_version": "1.0",
        "map_id": spec.id,
        "revision": spec.revision,
        "structural_rubric_scores": scores,
        "structural_design_score": average,
        "structural_threshold": 7.5,
        "passes_structural_threshold": average >= 7.5,
        "three_strongest_aspects": strengths[:3],
        "three_weakest_aspects": weaknesses[:3],
        "recommended_modifications": recommendations[:3],
        "limitations": "Structural heuristic only; visual review and playtesting remain required.",
    }


def write_critique(layout: CompiledLayout, output: Path) -> Path:
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        json.dumps(critique(layout), indent=2) + "\n", encoding="utf-8"
    )
    return output
