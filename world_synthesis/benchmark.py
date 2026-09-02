"""Build and blindly play the controlled world-synthesis benchmark."""

from __future__ import annotations

import argparse
import difflib
import hashlib
import json
import random
import secrets
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4

import yaml

from world_synthesis.compiler import build_world
from world_synthesis.critic import critique, write_critique
from world_synthesis.procedural_baseline import write_baseline
from world_synthesis.render import render_layout
from world_synthesis.schema import MapType, WorldSpec, load_world_spec
from world_synthesis.validate import write_report

REPO = Path(__file__).resolve().parents[1]
BENCHMARK_ROOT = REPO / "benchmarks"
HUMAN_RESULTS = (
    REPO / "artifacts" / "world_synthesis" / "human_evaluation"
)


@dataclass(frozen=True)
class Variant:
    method: str
    spec: Path
    map_id: str
    spawn: tuple[int, int]


VARIANTS = {
    "A": Variant(
        "A",
        BENCHMARK_ROOT
        / "generated"
        / "a_procedural"
        / "deep_forest"
        / "world_spec.yaml",
        "deep_forest_a_route",
        (20, 40),
    ),
    "B": Variant(
        "B",
        BENCHMARK_ROOT
        / "generated"
        / "b_one_shot"
        / "deep_forest"
        / "world_spec.yaml",
        "deep_forest_b_route",
        (20, 40),
    ),
    "C": Variant(
        "C",
        BENCHMARK_ROOT
        / "generated"
        / "c_agentic"
        / "deep_forest"
        / "final_world_spec.yaml",
        "deep_forest_c_route",
        (20, 40),
    ),
}


def _materialize_c_revision() -> Path:
    directory = (
        BENCHMARK_ROOT / "generated" / "c_agentic" / "deep_forest"
    )
    base_path = directory / "initial_world_spec.yaml"
    patch_path = directory / "final_revision.yaml"
    output = directory / "final_world_spec.yaml"
    raw: dict[str, Any] = yaml.safe_load(base_path.read_text(encoding="utf-8"))
    revision: dict[str, Any] = yaml.safe_load(
        patch_path.read_text(encoding="utf-8")
    )
    raw["metadata"].update(revision.get("metadata_updates", {}))
    raw["region"].update(revision.get("region_updates", {}))

    map_renames = revision.get("renames", {}).get("maps", {})
    table_renames = revision.get("renames", {}).get("encounter_tables", {})
    npc_renames = revision.get("renames", {}).get("npcs", {})
    for table in raw["encounter_tables"]:
        table["id"] = table_renames.get(table["id"], table["id"])
    for map_spec in raw["region"]["maps"]:
        map_spec["id"] = map_renames.get(map_spec["id"], map_spec["id"])
        for warp in map_spec.get("warps", []):
            warp["target_map"] = map_renames.get(
                warp["target_map"], warp["target_map"]
            )
        for encounter in map_spec.get("encounter_zones", []):
            encounter["table"] = table_renames.get(
                encounter["table"], encounter["table"]
            )
        for npc in map_spec.get("npcs", []):
            npc["id"] = npc_renames.get(npc["id"], npc["id"])

    maps = {item["id"]: item for item in raw["region"]["maps"]}
    for map_id, updates in revision.get("map_updates", {}).items():
        candidate = maps[map_id]
        for key, value in updates.items():
            if key != "props":
                candidate[key] = value
                continue
            props = {item["id"]: item for item in candidate.get("props", [])}
            for prop_id, prop_updates in value.items():
                props[prop_id].update(prop_updates)

    # Validation happens before the final artifact is accepted or written.
    validated = WorldSpec.model_validate(raw)
    dumped = validated.model_dump(mode="json")
    for map_spec in dumped["region"]["maps"]:
        for event in map_spec.get("events", []):
            if not event.get("conditions"):
                event.pop("conditions", None)
    encoded = yaml.safe_dump(dumped, sort_keys=False)
    output.write_text(encoded, encoding="utf-8")
    diff = difflib.unified_diff(
        base_path.read_text(encoding="utf-8").splitlines(keepends=True),
        encoded.splitlines(keepends=True),
        fromfile="initial_world_spec.yaml",
        tofile="final_world_spec.yaml",
    )
    (directory / "revision_diff.patch").write_text(
        "".join(diff), encoding="utf-8"
    )
    return output


def _route(world: WorldSpec):
    routes = [item for item in world.region.maps if item.map_type == MapType.ROUTE]
    if len(routes) != 1:
        raise ValueError("benchmark WorldSpec must contain exactly one route")
    return routes[0]


def _build_variant(variant: Variant) -> dict[str, Any]:
    world = load_world_spec(variant.spec)
    layouts = build_world(variant.spec, REPO)
    route = _route(world)
    layout = layouts[route.id]
    directory = variant.spec.parent
    prefix = "final_" if variant.method == "C" else ""
    normal = render_layout(layout, REPO, directory / f"{prefix}render.png")
    debug = render_layout(
        layout, REPO, directory / f"{prefix}debug.png", debug=True
    )
    report, diagnostics = write_report(
        world,
        layouts,
        REPO,
        directory / f"{prefix}validation",
    )
    critic_path = directory / f"{prefix}structural_critic.json"
    write_critique(layout, critic_path)
    tmx = REPO / "mods" / "world_synthesis" / "maps" / f"{route.id}.tmx"
    return {
        "method": variant.method,
        "map_id": route.id,
        "dimensions": [route.width, route.height],
        "npc_count": len(route.npcs),
        "trainer_count": sum(item.trainer for item in route.npcs),
        "encounter_zone_count": len(route.encounter_zones),
        "secret_count": len(route.secrets),
        "dominant_landmark_count": sum(
            item.role == "dominant" for item in route.landmarks
        ),
        "errors": sum(item.severity == "error" for item in diagnostics),
        "warnings": sum(item.severity == "warning" for item in diagnostics),
        "tmx_sha256": hashlib.sha256(tmx.read_bytes()).hexdigest(),
        "structural_design_score": critique(layout)[
            "structural_design_score"
        ],
        "render": str(normal.relative_to(REPO)).replace("\\", "/"),
        "debug_render": str(debug.relative_to(REPO)).replace("\\", "/"),
        "validation_report": str(report.relative_to(REPO)).replace("\\", "/"),
    }


def build_deep_forest(*, quiet: bool = False) -> int:
    write_baseline(VARIANTS["A"].spec)
    _materialize_c_revision()

    initial_dir = VARIANTS["C"].spec.parent
    initial_spec = initial_dir / "initial_world_spec.yaml"
    initial_world = load_world_spec(initial_spec)
    initial_layouts = build_world(initial_spec, REPO)
    initial_route = _route(initial_world)
    initial = initial_layouts[initial_route.id]
    render_layout(initial, REPO, initial_dir / "initial_render.png")
    render_layout(
        initial, REPO, initial_dir / "initial_debug.png", debug=True
    )
    write_critique(
        initial, initial_dir / "initial_structural_critic.json"
    )
    write_report(
        initial_world,
        initial_layouts,
        REPO,
        initial_dir / "initial_validation",
    )

    results = [_build_variant(VARIANTS[key]) for key in ("A", "B", "C")]
    artifact_root = REPO / "artifacts" / "world_synthesis"
    artifact_root.mkdir(parents=True, exist_ok=True)
    summary = {
        "format_version": "1.0",
        "family": "deep_forest",
        "compiler_freeze_commit": "1ded0461f423639f06adc5fd3990cd2f4b65467f",
        "results": results,
        "human_evaluation_status": "pending",
        "warning": "Structural scores are not visual-quality or enjoyment scores.",
    }
    (artifact_root / "deep_forest_benchmark.json").write_text(
        json.dumps(summary, indent=2) + "\n", encoding="utf-8"
    )
    gallery = [
        "# Deep Forest benchmark gallery",
        "",
        "Method identity is exposed here only for post-test analysis. The blind",
        "launcher masks these labels from players.",
        "",
    ]
    labels = {"A": "Procedural", "B": "One-shot", "C": "Structured agentic"}
    for result in results:
        method_key = result["method"].lower()
        gallery.extend(
            [
                f"## {result['method']} — {labels[result['method']]}",
                "",
                f"![Full render](../../{result['render']})",
                "",
                f"![Semantic debug render](../../{result['debug_render']})",
                "",
                "### In-game captures",
                "",
                f"![Landmark view](game_screenshots/deep_forest_{method_key}_landmark.png)",
                "",
                f"![Optional-loop view](game_screenshots/deep_forest_{method_key}_optional_loop.png)",
                "",
            ]
        )
    (artifact_root / "benchmark_gallery.md").write_text(
        "\n".join(gallery), encoding="utf-8"
    )
    if not quiet:
        print(json.dumps(summary, indent=2))
    return 1 if any(result["errors"] for result in results) else 0


def choose_variant(rng: random.Random | None = None) -> Variant:
    chooser = rng.choice if rng is not None else secrets.choice
    return chooser(list(VARIANTS.values()))


def create_session(variant: Variant) -> tuple[str, Path]:
    session_id = f"deep_forest_{uuid4().hex[:10]}"
    sessions = HUMAN_RESULTS / "sessions"
    sessions.mkdir(parents=True, exist_ok=True)
    path = sessions / f"{session_id}.json"
    path.write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "session_id": session_id,
                "family": "deep_forest",
                "masked_display_name": "Mossveil Passage",
                "method": variant.method,
                "map_id": variant.map_id,
                "started_at": datetime.now(UTC).isoformat(),
                "evaluation_file": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return session_id, path


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
        "desire_to_explore",
        "visual_composition",
        "sense_of_place",
        "environmental_storytelling",
        "landmark_memorability",
        "reward_for_curiosity",
        "npc_placement",
        "repetition_artificiality",
        "overall_enjoyment",
    )
    print("\nPlaytest complete. Method identity remains hidden.")
    print(
        "For most ratings, 1 is poor and 10 is excellent. For "
        "repetition/artificiality, 1 means natural and 10 means extremely artificial."
    )
    scores = {
        name: _score(name.replace("_", " ").capitalize())
        for name in score_names
    }
    answers = {
        "felt_intentionally_designed": _yes_no(
            "Did the map feel intentionally designed?"
        ),
        "discovered_optional_content": _yes_no(
            "Did you discover the optional content?"
        ),
        "became_lost_unintentionally": _yes_no(
            "Did you become lost unintentionally?"
        ),
        "most_memorable_place": input(
            "What place do you remember most? "
        ).strip(),
        "plausible_classic_monster_rpg": _yes_no(
            "Would this feel plausible in a competent classic monster-catching RPG?"
        ),
    }
    evaluations = HUMAN_RESULTS / "responses"
    evaluations.mkdir(parents=True, exist_ok=True)
    output = evaluations / f"{session_id}.json"
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
                "note": "Human results are intentionally separate from structural critic output.",
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


def play_deep_forest(*, dry_run: bool = False) -> int:
    build_result = build_deep_forest(quiet=True)
    if build_result:
        return build_result
    variant = choose_variant()
    session_id, session_path = create_session(variant)
    print(f"Blind session: {session_id}")
    print("Launching Mossveil Passage. Generation method is masked.")
    if dry_run:
        print("Dry run selected and logged; game was not launched.")
        return 0
    from world_synthesis.play import launch

    launch(variant.map_id, variant.spawn)
    output = collect_evaluation(session_id, session_path)
    print(f"Evaluation saved to {output}")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("build", help="Build all Deep Forest variants.")
    play_parser = subparsers.add_parser(
        "play", help="Blindly select, launch, and evaluate a variant."
    )
    play_parser.add_argument("family", choices=("deep_forest",))
    play_parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    if args.command == "build":
        return build_deep_forest()
    return play_deep_forest(dry_run=args.dry_run)


if __name__ == "__main__":
    raise SystemExit(main())
