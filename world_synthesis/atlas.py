from __future__ import annotations

from pathlib import Path

from PIL import Image, ImageDraw

ROOT = Path(__file__).resolve().parents[1]


def render_index(start_row: int = 0, row_count: int = 32) -> Path:
    source = ROOT / "mods" / "tuxemon" / "gfx" / "tilesets" / "prototyping_outdoor.png"
    output = ROOT / "artifacts" / "analysis" / f"prototyping_tiles_{start_row}_{start_row + row_count - 1}.png"
    image = Image.open(source).convert("RGBA")
    columns = image.width // 16
    scale = 4
    cell = 16 * scale
    sheet = Image.new("RGBA", (columns * cell, row_count * cell), "#242329")
    draw = ImageDraw.Draw(sheet)
    for relative_row in range(row_count):
        row = start_row + relative_row
        for column in range(columns):
            tile_id = row * columns + column
            tile = image.crop((column * 16, row * 16, column * 16 + 16, row * 16 + 16)).resize((cell, cell), Image.Resampling.NEAREST)
            x, y = column * cell, relative_row * cell
            sheet.alpha_composite(tile, (x, y))
            draw.rectangle((x, y, x + 31, y + 10), fill=(0, 0, 0, 190))
            draw.text((x + 1, y), str(tile_id), fill="white")
    output.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output)
    return output


if __name__ == "__main__":
    for start in (0, 32):
        print(render_index(start, 32).relative_to(ROOT))
