from __future__ import annotations

import json
import re
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
MAPS = ROOT / "mods" / "tuxemon" / "maps"


def command_name(value: str) -> str:
    value = value.removeprefix("is ").removeprefix("not ")
    return re.split(r"[ ,]", value.strip(), maxsplit=1)[0]


def analyze_map(path: Path) -> dict[str, Any]:
    root = ET.parse(path).getroot()
    properties = {item.get("name", ""): item.get("value", item.text or "") for item in root.findall("./properties/property")}
    layer_names = [layer.get("name", "") for layer in root.findall("layer")]
    object_groups = Counter()
    actions = Counter()
    conditions = Counter()
    behaviors = Counter()
    event_count = 0
    collision_count = 0
    for group in root.findall("objectgroup"):
        for obj in group.findall("object"):
            object_type = obj.get("type", "")
            object_groups[object_type or "untyped"] += 1
            collision_count += int(object_type.lower().startswith("collision"))
            if object_type in {"event", "init"}:
                event_count += 1
                for prop in obj.findall("./properties/property"):
                    key = prop.get("name", "")
                    value = prop.get("value", prop.text or "")
                    if key.startswith("act"):
                        actions[command_name(value)] += 1
                    elif key.startswith("cond"):
                        conditions[command_name(value)] += 1
                    elif key.startswith("behav"):
                        behaviors[command_name(value)] += 1
    return {
        "path": path.relative_to(ROOT).as_posix(),
        "dimensions": [int(root.get("width", "0")), int(root.get("height", "0"))],
        "tile_size": [int(root.get("tilewidth", "0")), int(root.get("tileheight", "0"))],
        "properties": properties,
        "tilesets": [item.get("source", "embedded") for item in root.findall("tileset")],
        "layers": layer_names,
        "object_types": dict(object_groups),
        "event_count": event_count,
        "collision_object_count": collision_count,
        "actions": dict(actions),
        "conditions": dict(conditions),
        "behaviors": dict(behaviors),
    }


def build_report() -> dict[str, Any]:
    maps = [analyze_map(path) for path in sorted(MAPS.glob("*.tmx"))]
    totals: dict[str, Counter[str]] = {key: Counter() for key in ("actions", "conditions", "behaviors", "object_types")}
    layer_names: Counter[str] = Counter()
    tilesets: Counter[str] = Counter()
    for item in maps:
        layer_names.update(item["layers"])
        tilesets.update(item["tilesets"])
        for key in totals:
            totals[key].update(item[key])
    return {
        "format_version": 1,
        "map_count": len(maps),
        "aggregate": {
            **{key: dict(value.most_common()) for key, value in totals.items()},
            "layer_names": dict(layer_names.most_common()),
            "tilesets": dict(tilesets.most_common()),
        },
        "representative_maps": {item["path"]: item for item in maps if Path(item["path"]).name in {"spyder_route3.tmx", "route5.tmx", "spyder_paper_town.tmx", "spyder_cotton_tunnel.tmx"}},
        "maps": maps,
    }


def main() -> None:
    destination = ROOT / "artifacts" / "analysis" / "upstream_map_metrics.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(json.dumps(build_report(), indent=2, sort_keys=True) + "\n", encoding="utf-8")
    print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
