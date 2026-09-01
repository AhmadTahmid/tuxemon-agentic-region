from __future__ import annotations

import json
import xml.etree.ElementTree as ET
from collections import Counter
from pathlib import Path
from typing import Any

import yaml
from PIL import Image

ROOT = Path(__file__).resolve().parents[1]
MOD = ROOT / "mods" / "tuxemon"

SEMANTIC_PATTERNS: dict[str, tuple[str, ...]] = {
    "grass": ("grass", "meadow"),
    "forest": ("forest", "tree", "woodland", "vegetation", "plant"),
    "water": ("water", "river", "ocean", "beach", "sand"),
    "bridge": ("bridge",),
    "path": ("path", "road", "route", "terrain", "ground"),
    "cliff": ("cliff", "mountain", "cave"),
    "building": ("building", "city", "town", "house"),
    "interior": ("interior", "furniture", "floor", "wall", "door"),
    "industrial": ("factory", "electronics", "machine"),
    "sign": ("sign",),
}


def semantic_tags(name: str) -> tuple[list[str], str]:
    lowered = name.lower().replace("_", " ").replace("-", " ")
    tags = [
        tag
        for tag, terms in SEMANTIC_PATTERNS.items()
        if any(term in lowered for term in terms)
    ]
    return tags or ["unclassified"], "medium" if tags else "low"


def image_record(path: Path) -> dict[str, Any]:
    with Image.open(path) as image:
        width, height = image.size
    tags, confidence = semantic_tags(path.stem)
    tsx = path.with_suffix(".tsx")
    record: dict[str, Any] = {
        "path": path.relative_to(ROOT).as_posix(),
        "dimensions_px": [width, height],
        "semantic_tags": tags,
        "classification_confidence": confidence,
        "classification_basis": "filename heuristic; requires visual review"
        if confidence == "low"
        else "filename plus visual-family naming",
    }
    if tsx.exists():
        root = ET.parse(tsx).getroot()
        record["tsx"] = tsx.relative_to(ROOT).as_posix()
        record["tile_size"] = [
            int(root.get("tilewidth", "0")),
            int(root.get("tileheight", "0")),
        ]
        record["tile_count"] = int(root.get("tilecount", "0"))
        properties: Counter[str] = Counter()
        animated = 0
        for tile in root.findall("tile"):
            if tile.find("animation") is not None:
                animated += 1
            for prop in tile.findall("./properties/property"):
                properties[prop.get("name", "unknown")] += 1
        record["tile_property_counts"] = dict(sorted(properties.items()))
        record["animated_tiles"] = animated
    return record


def yaml_records(folder: Path, kind: str) -> list[dict[str, Any]]:
    records: list[dict[str, Any]] = []
    for path in sorted(folder.glob("*.yaml")):
        try:
            payload = yaml.safe_load(path.read_text(encoding="utf-8"))
        except (UnicodeDecodeError, yaml.YAMLError):
            continue
        entries = payload if isinstance(payload, list) else [payload]
        for entry in entries:
            if not isinstance(entry, dict) or "slug" not in entry:
                continue
            record: dict[str, Any] = {
                "slug": entry["slug"],
                "source": path.relative_to(ROOT).as_posix(),
            }
            if kind == "monster":
                record.update(
                    {
                        key: entry.get(key, [])
                        for key in ("types", "terrains", "tags")
                    }
                )
                record["shape"] = entry.get("shape")
            elif kind == "npc":
                template = entry.get("template") or {}
                record["sprite"] = template.get("sprite_name")
                record["combat_sheet"] = template.get("combat_sheet")
                record["has_monsters"] = bool(entry.get("monsters"))
                record["dialogue_fields"] = sorted(
                    ((entry.get("speech") or {}).get("profile") or {})
                    .get("default", {})
                    .keys()
                )
            elif kind == "item":
                record["category"] = entry.get("category")
                record["sprite"] = entry.get("sprite")
            records.append(record)
    return records


def build_catalog() -> dict[str, Any]:
    tilesets = [
        image_record(path)
        for path in sorted((MOD / "gfx" / "tilesets").glob("*"))
        if path.suffix.lower() in {".png", ".gif", ".bmp"}
    ]
    sprites = []
    for path in sorted((MOD / "sprites").glob("*.png")):
        with Image.open(path) as image:
            size = list(image.size)
        tags, confidence = semantic_tags(path.stem)
        sprites.append(
            {
                "id": path.stem,
                "path": path.relative_to(ROOT).as_posix(),
                "dimensions_px": size,
                "semantic_tags": tags,
                "classification_confidence": confidence,
            }
        )
    monsters = yaml_records(MOD / "db" / "monster", "monster")
    npcs = yaml_records(MOD / "db" / "npc", "npc")
    items = yaml_records(MOD / "db" / "item", "item")
    return {
        "format_version": 1,
        "upstream_commit": "59a34164f",
        "methodology": {
            "semantic_classification": "Conservative filename heuristics plus structured TSX/YAML metadata.",
            "uncertainty_policy": "Unclassified and low-confidence entries are retained for human review; no visual meaning is invented.",
        },
        "counts": {
            "tilesets": len(tilesets),
            "overworld_sprites": len(sprites),
            "npc_records": len(npcs),
            "monsters": len(monsters),
            "items": len(items),
        },
        "tilesets": tilesets,
        "overworld_sprites": sprites,
        "npc_records": npcs,
        "monsters": monsters,
        "items": items,
    }


def main() -> None:
    destination = ROOT / "docs" / "world_synthesis" / "ASSET_CATALOG.json"
    destination.parent.mkdir(parents=True, exist_ok=True)
    destination.write_text(
        json.dumps(build_catalog(), indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )
    print(f"Wrote {destination.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
