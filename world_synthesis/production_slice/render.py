"""Deterministic static rendering for production-map composition review."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

from PIL import Image, ImageDraw

from world_synthesis.production_slice.compiler import (
    CompiledProductionMap,
    compile_map,
)
from world_synthesis.production_slice.schema import EpisodeSpec, PaletteSpec

TILE_SIZE = 16


def _tileset_image(
    episode: EpisodeSpec, palette: PaletteSpec, repo: Path
) -> tuple[Image.Image, int]:
    maps_dir = repo / "mods" / episode.metadata.slug / "maps"
    tsx_path = (maps_dir / palette.source).resolve()
    root = ET.parse(tsx_path).getroot()
    image_node = root.find("image")
    if image_node is None or "source" not in image_node.attrib:
        raise ValueError(f"tileset {tsx_path} has no image")
    image_path = (tsx_path.parent / image_node.attrib["source"]).resolve()
    atlas = Image.open(image_path).convert("RGBA")
    columns = int(root.attrib.get("columns", atlas.width // TILE_SIZE))
    return atlas, columns


def _tile(atlas: Image.Image, columns: int, tile_id: int) -> Image.Image:
    x = (tile_id % columns) * TILE_SIZE
    y = (tile_id // columns) * TILE_SIZE
    return atlas.crop((x, y, x + TILE_SIZE, y + TILE_SIZE))


def render_map(
    episode: EpisodeSpec,
    layout: CompiledProductionMap,
    repo: Path,
    output: Path,
    *,
    debug: bool = False,
    scale: int = 2,
) -> Path:
    palette = episode.palettes[layout.spec.palette]
    atlas, columns = _tileset_image(episode, palette, repo)
    canvas = Image.new(
        "RGBA",
        (layout.spec.width * TILE_SIZE, layout.spec.height * TILE_SIZE),
        "#17121c",
    )
    for grid in layout.layers.values():
        for y, row in enumerate(grid):
            for x, tile_id in enumerate(row):
                if tile_id:
                    canvas.alpha_composite(
                        _tile(atlas, columns, tile_id),
                        (x * TILE_SIZE, y * TILE_SIZE),
                    )

    if debug:
        draw = ImageDraw.Draw(canvas, "RGBA")
        for x, y in layout.blocked:
            draw.rectangle(
                (
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    (x + 1) * TILE_SIZE - 1,
                    (y + 1) * TILE_SIZE - 1,
                ),
                fill=(220, 35, 60, 72),
                outline=(255, 70, 70, 160),
            )
        for zone in layout.spec.encounters:
            bounds = zone.bounds
            draw.rectangle(
                (
                    bounds.x * TILE_SIZE,
                    bounds.y * TILE_SIZE,
                    (bounds.x + bounds.width) * TILE_SIZE - 1,
                    (bounds.y + bounds.height) * TILE_SIZE - 1,
                ),
                outline=(255, 210, 0, 235),
                width=2,
            )
        for warp in layout.spec.warps:
            x, y = warp.at.x * TILE_SIZE, warp.at.y * TILE_SIZE
            draw.rectangle(
                (x, y, x + TILE_SIZE - 1, y + TILE_SIZE - 1),
                fill=(40, 180, 255, 140),
            )
        for npc in layout.spec.npcs:
            x, y = npc.at.x * TILE_SIZE + 8, npc.at.y * TILE_SIZE + 8
            draw.ellipse(
                (x - 5, y - 5, x + 5, y + 5),
                fill=(255, 255, 255, 235),
                outline=(25, 20, 30, 255),
            )
        for event in layout.spec.events:
            if event.trigger.value == "init":
                continue
            x, y = event.at.x * TILE_SIZE + 8, event.at.y * TILE_SIZE + 8
            color = (
                (230, 80, 255, 230) if event.mandatory else (80, 255, 180, 210)
            )
            draw.rectangle((x - 3, y - 3, x + 3, y + 3), fill=color)

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = canvas.resize(
        (canvas.width * scale, canvas.height * scale), Image.Resampling.NEAREST
    )
    canvas.convert("RGB").save(output, optimize=True)
    return output


def render_episode(episode: EpisodeSpec, repo: Path) -> list[Path]:
    root = (
        repo
        / "artifacts"
        / "production_slice"
        / episode.metadata.slug
        / "renders"
    )
    outputs: list[Path] = []
    for map_spec in episode.maps:
        layout = compile_map(episode, map_spec)
        outputs.append(
            render_map(
                episode, layout, repo, root / "full" / f"{map_spec.slug}.png"
            )
        )
        outputs.append(
            render_map(
                episode,
                layout,
                repo,
                root / "debug" / f"{map_spec.slug}.png",
                debug=True,
            )
        )
    return outputs


def render_palette_index(
    episode: EpisodeSpec, palette_slug: str, repo: Path, output: Path
) -> Path:
    palette = episode.palettes[palette_slug]
    atlas, columns = _tileset_image(episode, palette, repo)
    scale = 3
    canvas = atlas.resize(
        (atlas.width * scale, atlas.height * scale), Image.Resampling.NEAREST
    ).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    rows = atlas.height // TILE_SIZE
    for tile_id in range(columns * rows):
        x = (tile_id % columns) * TILE_SIZE * scale
        y = (tile_id // columns) * TILE_SIZE * scale
        draw.rectangle(
            (x, y, x + TILE_SIZE * scale - 1, y + TILE_SIZE * scale - 1),
            outline=(255, 255, 255),
        )
        draw.text(
            (x + 1, y + 1),
            str(tile_id),
            fill=(255, 255, 0),
            stroke_width=1,
            stroke_fill=(0, 0, 0),
        )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output


def render_palette_window(
    episode: EpisodeSpec,
    palette_slug: str,
    repo: Path,
    output: Path,
    *,
    start_row: int,
    row_count: int,
) -> Path:
    """Render a labelled review window without changing the source atlas."""
    palette = episode.palettes[palette_slug]
    atlas, columns = _tileset_image(episode, palette, repo)
    top = start_row * TILE_SIZE
    bottom = min(atlas.height, (start_row + row_count) * TILE_SIZE)
    window = atlas.crop((0, top, atlas.width, bottom))
    scale = 4
    canvas = window.resize(
        (window.width * scale, window.height * scale), Image.Resampling.NEAREST
    ).convert("RGB")
    draw = ImageDraw.Draw(canvas)
    rows = (bottom - top) // TILE_SIZE
    for relative_row in range(rows):
        for column in range(columns):
            tile_id = (start_row + relative_row) * columns + column
            x = column * TILE_SIZE * scale
            y = relative_row * TILE_SIZE * scale
            draw.rectangle(
                (x, y, x + TILE_SIZE * scale - 1, y + TILE_SIZE * scale - 1),
                outline=(255, 255, 255),
            )
            draw.text(
                (x + 1, y + 1),
                str(tile_id),
                fill=(255, 255, 0),
                stroke_width=1,
                stroke_fill=(0, 0, 0),
            )
    output.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output, optimize=True)
    return output
