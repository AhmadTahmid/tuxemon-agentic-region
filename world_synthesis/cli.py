"""Command line entry point for the isolated world-synthesis experiment."""

from __future__ import annotations

import argparse
import json
from pathlib import Path

from world_synthesis.catalog import build_catalog
from world_synthesis.compiler import build_world, compile_layout
from world_synthesis.critic import write_critique
from world_synthesis.render import render_layout, write_contact_sheet
from world_synthesis.schema import WorldSpec, load_world_spec
from world_synthesis.validate import write_report

REPO = Path(__file__).resolve().parents[1]
DEFAULT_SPEC = REPO / "content" / "world_synthesis" / "glasswind_region.yaml"


def build(spec_path: Path = DEFAULT_SPEC) -> int:
    world = load_world_spec(spec_path)
    schema_path = REPO / "docs" / "world_synthesis" / "WORLD_SPEC_SCHEMA.json"
    schema_path.write_text(
        json.dumps(WorldSpec.model_json_schema(), indent=2) + "\n",
        encoding="utf-8",
    )
    route = next(
        item for item in world.region.maps if item.id == "glasswind_causeway"
    )

    # Preserve the pre-critique candidate as a reproducible artifact. Revision 1
    # lacks a true loop and balancing grove; revision 2 is the authored response.
    revision_one = route.model_copy(
        update={
            "revision": 1,
            "secondary_paths": [],
            "landmarks": [
                item for item in route.landmarks if item.role == "dominant"
            ],
        },
        deep=True,
    )
    baseline = compile_layout(world, revision_one)
    renders = REPO / "artifacts" / "map_renders"
    critiques = REPO / "artifacts" / "world_synthesis" / "critique"
    render_layout(
        baseline, REPO, renders / "glasswind_causeway_revision_1.png"
    )
    write_critique(baseline, critiques / "glasswind_causeway_revision_1.json")

    layouts = build_world(spec_path, REPO)
    final = layouts["glasswind_causeway"]
    normal = render_layout(
        final, REPO, renders / "glasswind_causeway_revision_2.png"
    )
    debug = render_layout(
        final,
        REPO,
        renders / "glasswind_causeway_revision_2_debug.png",
        debug=True,
    )
    write_contact_sheet(
        [normal, debug], renders / "glasswind_causeway_inspection.png"
    )
    write_critique(final, critiques / "glasswind_causeway_revision_2.json")
    report, diagnostics = write_report(world, layouts, REPO)
    errors = [item for item in diagnostics if item.severity == "error"]
    summary = {
        "maps": sorted(layouts),
        "validation_report": str(report.relative_to(REPO)),
        "errors": len(errors),
        "renders": [str(path.relative_to(REPO)) for path in (normal, debug)],
    }
    print(json.dumps(summary, indent=2))
    return 1 if errors else 0


def validate(spec_path: Path = DEFAULT_SPEC) -> int:
    world = load_world_spec(spec_path)
    layouts = build_world(spec_path, REPO)
    report, diagnostics = write_report(world, layouts, REPO)
    errors = sum(item.severity == "error" for item in diagnostics)
    print(f"{report}: {errors} blocking error(s)")
    return 1 if errors else 0


def main() -> int:
    parser = argparse.ArgumentParser(
        prog="python -m world_synthesis", description=__doc__
    )
    parser.add_argument("command", choices=("build", "validate", "catalog"))
    parser.add_argument("--spec", type=Path, default=DEFAULT_SPEC)
    args = parser.parse_args()
    if args.command == "build":
        return build(args.spec.resolve())
    if args.command == "validate":
        return validate(args.spec.resolve())
    output = REPO / "docs" / "world_synthesis" / "ASSET_CATALOG.json"
    output.write_text(
        json.dumps(build_catalog(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(output)
    return 0
