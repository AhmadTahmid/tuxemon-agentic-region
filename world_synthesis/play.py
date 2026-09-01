"""Launch an experiment map while retaining upstream Tuxemon assets."""

from __future__ import annotations

import argparse
import sys


def launch(
    starting_map: str = "glasswind_causeway",
    starting_position: tuple[int, int] = (15, 36),
) -> None:
    # This must happen before display/database initialization. The database and
    # asset loader see both mods; the startup state machine receives only the
    # experimental campaign so it launches directly without a menu.
    from tuxemon.user_config import CONFIG

    CONFIG.mods = ["tuxemon", "world_synthesis"]

    from tuxemon.platform import platform
    from tuxemon.prepare import pygame_init

    platform.init()
    context = pygame_init()

    # NpcModel currently validates speech keys against the base domain only.
    # Merge our already-compiled isolated domain into the in-memory fallback;
    # source catalogues stay separate on disk.
    from tuxemon.locale.locale import T

    base_translation = T._translators["base"]._real_translate
    if hasattr(base_translation, "_catalog"):
        for domain, translator in T._translators.items():
            experiment_translation = translator._real_translate
            if domain != "base" and hasattr(experiment_translation, "_catalog"):
                base_translation._catalog.update(experiment_translation._catalog)

    # Upstream intentionally keeps its database activation in mods/db_config.yaml.
    # Build an in-memory derivative so the experiment contributes only NPC and
    # encounter records without editing the upstream configuration file.
    from pathlib import Path

    import tuxemon.database.runtime as runtime
    from tuxemon.database.data import ModData
    from tuxemon.database.loader import ModelLoader
    from tuxemon.database.registry import validator
    from tuxemon.database.utils import load_config
    from tuxemon.database.validator import Validator
    from tuxemon.db import load_model_map

    base = load_config(str(Path("mods/db_config.yaml")))
    active = ["tuxemon", "world_synthesis"]
    tables = dict(base.mod_tables)
    tables["world_synthesis"] = ["npc", "encounter"]
    database_config = base.model_copy(
        update={
            "active_mods": active,
            "mod_activation": {**base.mod_activation, "world_synthesis": True},
            "mod_tables": tables,
            "mod_dependencies": {
                **base.mod_dependencies,
                "world_synthesis": ["tuxemon"],
            },
        }
    )
    experiment_db = ModData(
        database_config, ModelLoader(load_model_map(database_config.model_map))
    )
    experiment_db.preload()
    experiment_db.load()
    metadata = experiment_db.mod_metadata.get_mod_metadata("world_synthesis")
    experiment_db.mod_metadata._mod_metadata["world_synthesis"] = (
        metadata.model_copy(
            update={
                "starting_map": f"{starting_map}.tmx",
                "starting_position": starting_position,
            }
        )
    )
    runtime.db = experiment_db
    validator.reset()
    validator.set(Validator(experiment_db))

    from tuxemon import main as tuxemon_main

    config = CONFIG.copy()
    config.mods = ["world_synthesis"]
    config.config_model.game.skip_titlescreen = True
    config.config_model.display.splash = False
    config.logging.configure()
    tuxemon_main.main(config=config, context=context, load_slot=None)


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--map", default="glasswind_causeway")
    parser.add_argument("--x", type=int, default=15)
    parser.add_argument("--y", type=int, default=36)
    args = parser.parse_args()
    launch(args.map, (args.x, args.y))


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        sys.exit(130)
