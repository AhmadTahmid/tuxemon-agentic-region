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
    parser.add_argument("command", choices=("build", "render", "play"))
    parser.add_argument("episode", choices=tuple(EPISODES))
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

    from world_synthesis.production_slice.launcher import launch

    launch(spec_path, repo)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
