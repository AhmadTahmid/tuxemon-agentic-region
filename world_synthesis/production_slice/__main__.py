"""Build or play an isolated production slice."""

from __future__ import annotations

import argparse
from pathlib import Path

from world_synthesis.production_slice.compiler import build_episode

EPISODES = {"low_bell": Path("content/production_slice/low_bell/episode.yaml")}


def _resolve_episode(repo: Path, slug: str) -> Path:
    try:
        relative = EPISODES[slug]
    except KeyError as error:
        raise SystemExit(f"unknown production episode: {slug}") from error
    return repo / relative


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "command", choices=("build", "render", "validate", "play", "playtest")
    )
    parser.add_argument("episode", choices=tuple(EPISODES))
    parser.add_argument("--dry-run", action="store_true")
    args = parser.parse_args()
    repo = Path(__file__).resolve().parents[2]
    spec_path = _resolve_episode(repo, args.episode)
    if args.command == "build":
        layouts = build_episode(spec_path, repo)
        print(f"Built {args.episode}: {len(layouts)} maps")
        return 0
    if args.command == "render":
        from world_synthesis.production_slice.render import render_episode
        from world_synthesis.production_slice.schema import load_episode

        build_episode(spec_path, repo)
        outputs = render_episode(load_episode(spec_path), repo)
        print(f"Rendered {args.episode}: {len(outputs)} images")
        return 0
    if args.command == "validate":
        from world_synthesis.production_slice.validation import (
            validate_episode,
        )

        contract_path = spec_path.with_name("acceptance.yaml")
        report = validate_episode(spec_path, contract_path, repo)
        print(
            f"Validated {args.episode}: "
            f"{'PASS' if report['passed'] else 'FAIL'}"
        )
        return 0 if report["passed"] else 1
    if args.command == "playtest":
        from world_synthesis.production_slice.playtest import run_playtest

        return run_playtest(spec_path, repo, dry_run=args.dry_run)

    from world_synthesis.production_slice.launcher import launch

    launch(spec_path, repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
