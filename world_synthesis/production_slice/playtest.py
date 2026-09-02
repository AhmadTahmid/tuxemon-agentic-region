"""Fresh-game human playtest sessions kept separate from automation."""

from __future__ import annotations

import json
from collections.abc import Callable
from datetime import UTC, datetime
from pathlib import Path
from typing import Any
from uuid import uuid4


def _rating(prompt: str) -> int:
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


def create_session(repo: Path) -> tuple[str, Path]:
    session_id = f"low_bell_{uuid4().hex[:10]}"
    directory = (
        repo
        / "artifacts"
        / "production_slice"
        / "low_bell"
        / "human_evaluation"
        / "sessions"
    )
    directory.mkdir(parents=True, exist_ok=True)
    path = directory / f"{session_id}.json"
    path.write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "session_id": session_id,
                "display_name": "Ashenbell: The Low Bell",
                "fresh_game": True,
                "started_at": datetime.now(UTC).isoformat(),
                "status": "launched",
                "response_file": None,
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return session_id, path


def collect_evaluation(
    session_id: str, session_path: Path, repo: Path
) -> Path | None:
    completed = _yes_no("Did you reach the episode ending hook in Ashenbell?")
    session = json.loads(session_path.read_text(encoding="utf-8"))
    if not completed:
        session["status"] = "incomplete"
        session["closed_at"] = datetime.now(UTC).isoformat()
        session_path.write_text(
            json.dumps(session, indent=2) + "\n", encoding="utf-8"
        )
        print(
            "Session recorded as incomplete; the completion questionnaire was not shown."
        )
        return None

    print(
        "\nEpisode complete. Ratings use 1=strongly disagree/poor and 10=strongly agree/excellent."
    )
    ratings = {
        "current_goal_clear": _rating("Was the current goal usually clear?"),
        "village_inhabited": _rating("Did the village feel inhabited?"),
        "village_changed_after_climax": _rating(
            "Did the village feel changed after the climax?"
        ),
        "quarry_reveal_changed_understanding": _rating(
            "Did the quarry reveal change your understanding of the low tone?"
        ),
        "optional_content_worth_exploring": _rating(
            "Did optional content feel worth exploring?"
        ),
        "battle_exploration_pacing": _rating(
            "Did battles and exploration feel well paced?"
        ),
        "emotional_investment": _rating(
            "Did you feel any emotional investment?"
        ),
        "competent_classic_rpg_chapter": _rating(
            "Did this feel like a competent early chapter of a classic monster-catching RPG?"
        ),
    }
    answers: dict[str, Any] = {
        "empty_or_pointless_stretch": input(
            "Was there any stretch that felt empty or pointless? Describe it: "
        ).strip(),
        "three_remembered_characters": input(
            "Which three characters do you remember? "
        ).strip(),
        "dialogue_filler_or_exposition": _yes_no(
            "Did any dialogue feel like filler or exposition?"
        ),
        "dialogue_filler_detail": input("If so, which dialogue? ").strip(),
        "map_felt_randomly_generated": _yes_no(
            "Did any map feel randomly generated?"
        ),
        "random_map_detail": input("If so, which map and why? ").strip(),
        "most_memorable_moment": input(
            "What was the most memorable moment? "
        ).strip(),
        "would_continue": _yes_no(
            "Would you continue playing another episode?"
        ),
    }
    directory = (
        repo
        / "artifacts"
        / "production_slice"
        / "low_bell"
        / "human_evaluation"
        / "responses"
    )
    directory.mkdir(parents=True, exist_ok=True)
    output = directory / f"{session_id}.json"
    output.write_text(
        json.dumps(
            {
                "format_version": "1.0",
                "session_id": session_id,
                "ratings": ratings,
                "rating_scale": "1=strongly disagree/poor, 10=strongly agree/excellent",
                "answers": answers,
                "aggregate_score": None,
                "note": "Human evidence is intentionally separate from automated validation.",
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    session["status"] = "complete"
    session["response_file"] = str(output.relative_to(repo)).replace("\\", "/")
    session["completed_at"] = datetime.now(UTC).isoformat()
    session_path.write_text(
        json.dumps(session, indent=2) + "\n", encoding="utf-8"
    )
    return output


def run_playtest(
    spec_path: Path,
    repo: Path,
    *,
    dry_run: bool = False,
    launch_fn: Callable[[Path, Path], None] | None = None,
) -> int:
    session_id, session_path = create_session(repo)
    print(f"Playtest session: {session_id}")
    print("Launching a fresh game: Ashenbell: The Low Bell")
    if dry_run:
        print("Dry run logged; the game and questionnaire were not started.")
        return 0
    if launch_fn is None:
        from world_synthesis.production_slice.launcher import launch

        launch_fn = launch
    launch_fn(spec_path, repo)
    output = collect_evaluation(session_id, session_path, repo)
    if output:
        print(f"Human response saved separately to {output}")
    return 0
