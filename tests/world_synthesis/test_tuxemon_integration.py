from pathlib import Path

import pygame as pg

from tuxemon.map.loader import TMXMapLoader
from tuxemon.prepare import headless_init
from world_synthesis.compiler import build_world

REPO = Path(__file__).resolve().parents[2]
SPEC = REPO / "content" / "world_synthesis" / "glasswind_region.yaml"


def test_real_tuxemon_loader_reads_generated_map(monkeypatch) -> None:
    monkeypatch.setenv("SDL_VIDEODRIVER", "dummy")
    build_world(SPEC, REPO)
    context = headless_init()
    pg.display.set_mode((320, 240))
    path = (
        REPO / "mods" / "world_synthesis" / "maps" / "glasswind_causeway.tmx"
    )
    loaded = TMXMapLoader().load(str(path), context)
    assert loaded.size == (40, 48)
    assert len(loaded.collision_map) > 0
    assert len(loaded.events) >= 10
    pg.display.quit()
