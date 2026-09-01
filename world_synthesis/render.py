"""Static composited map renderer for the visual inspection loop."""

from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

from world_synthesis.compiler import TILE_SIZE, TILESET_COLUMNS, CompiledLayout


def _tile(atlas: Image.Image, tile_id: int) -> Image.Image:
    x = (tile_id % TILESET_COLUMNS) * TILE_SIZE
    y = (tile_id // TILESET_COLUMNS) * TILE_SIZE
    return atlas.crop((x, y, x + TILE_SIZE, y + TILE_SIZE))


def render_layout(
    layout: CompiledLayout,
    repo: Path,
    output: Path,
    *,
    debug: bool = False,
    scale: int = 2,
) -> Path:
    spec = layout.map_spec
    atlas_path = (
        repo
        / "mods"
        / "tuxemon"
        / "gfx"
        / "tilesets"
        / "prototyping_outdoor.png"
    )
    atlas = Image.open(atlas_path).convert("RGBA")
    canvas = Image.new(
        "RGBA", (spec.width * TILE_SIZE, spec.height * TILE_SIZE), "#1e1724"
    )
    for grid in layout.layers.values():
        for y, row in enumerate(grid):
            for x, tile_id in enumerate(row):
                if tile_id:
                    canvas.alpha_composite(
                        _tile(atlas, tile_id), (x * TILE_SIZE, y * TILE_SIZE)
                    )

    draw = ImageDraw.Draw(canvas, "RGBA")
    if debug:
        for x, y in layout.blocked:
            draw.rectangle(
                (
                    x * TILE_SIZE,
                    y * TILE_SIZE,
                    (x + 1) * TILE_SIZE - 1,
                    (y + 1) * TILE_SIZE - 1,
                ),
                fill=(220, 35, 60, 75),
                outline=(255, 70, 70, 170),
            )
        for encounter in spec.encounter_zones:
            rect = encounter.bounds
            draw.rectangle(
                (
                    rect.x * TILE_SIZE,
                    rect.y * TILE_SIZE,
                    (rect.x + rect.width) * TILE_SIZE - 1,
                    (rect.y + rect.height) * TILE_SIZE - 1,
                ),
                outline=(255, 210, 0, 230),
                width=2,
            )
        for warp in spec.warps:
            x, y = warp.at.x * TILE_SIZE, warp.at.y * TILE_SIZE
            draw.rectangle(
                (x, y, x + TILE_SIZE - 1, y + TILE_SIZE - 1),
                fill=(40, 180, 255, 130),
            )
        for npc in spec.npcs:
            x, y = npc.at.x * TILE_SIZE + 8, npc.at.y * TILE_SIZE + 8
            draw.ellipse(
                (x - 5, y - 5, x + 5, y + 5),
                fill=(255, 255, 255, 230),
                outline=(25, 20, 30, 255),
            )
        spawn = spec.player_spawn
        x, y = spawn.x * TILE_SIZE, spawn.y * TILE_SIZE
        draw.polygon(
            [(x + 8, y + 1), (x + 15, y + 14), (x + 1, y + 14)],
            fill=(60, 255, 140, 240),
        )
        for secret in spec.secrets:
            x, y = secret.at.x * TILE_SIZE, secret.at.y * TILE_SIZE
            draw.text(
                (x + 3, y),
                "?",
                fill="white",
                stroke_width=2,
                stroke_fill="#7a175f",
            )

    output.parent.mkdir(parents=True, exist_ok=True)
    canvas = canvas.resize(
        (canvas.width * scale, canvas.height * scale), Image.Resampling.NEAREST
    )
    canvas.convert("RGB").save(output, optimize=True)
    return output


def write_contact_sheet(images: list[Path], output: Path) -> Path:
    opened = [Image.open(path).convert("RGB") for path in images]
    width = sum(image.width for image in opened)
    height = max(image.height for image in opened) + 52
    sheet = Image.new("RGB", (width, height), "#17121c")
    draw = ImageDraw.Draw(sheet)
    cursor = 0
    for path, image in zip(images, opened):
        sheet.paste(image, (cursor, 52))
        draw.text(
            (cursor + 12, 16),
            path.stem.replace("_", " ").title(),
            fill="#f4e6c5",
        )
        cursor += image.width
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output, optimize=True)
    return output
