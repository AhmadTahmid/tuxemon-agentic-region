"""Build and launch an isolated production episode with upstream assets."""

from __future__ import annotations

from pathlib import Path


def launch(spec_path: Path, repo: Path) -> None:
    from world_synthesis.production_slice.compiler import build_episode
    from world_synthesis.production_slice.schema import load_episode

    build_episode(spec_path, repo)
    episode = load_episode(spec_path)

    from tuxemon.user_config import CONFIG

    CONFIG.mods = ["tuxemon", episode.metadata.slug]

    from tuxemon.platform import platform
    from tuxemon.prepare import pygame_init

    platform.init()
    context = pygame_init()

    from tuxemon.locale.locale import T

    base_translation = T._translators["base"]._real_translate
    if hasattr(base_translation, "_catalog"):
        for domain, translator in T._translators.items():
            production_translation = translator._real_translate
            if domain != "base" and hasattr(
                production_translation, "_catalog"
            ):
                base_translation._catalog.update(
                    production_translation._catalog
                )

    import tuxemon.database.runtime as runtime
    from tuxemon.database.data import ModData
    from tuxemon.database.loader import ModelLoader
    from tuxemon.database.registry import validator
    from tuxemon.database.utils import load_config
    from tuxemon.database.validator import Validator
    from tuxemon.db import load_model_map

    base = load_config(str(repo / "mods" / "db_config.yaml"))
    mod_slug = episode.metadata.slug
    tables = dict(base.mod_tables)
    tables[mod_slug] = ["npc", "encounter"]
    database_config = base.model_copy(
        update={
            "active_mods": ["tuxemon", mod_slug],
            "mod_activation": {**base.mod_activation, mod_slug: True},
            "mod_tables": tables,
            "mod_dependencies": {
                **base.mod_dependencies,
                mod_slug: ["tuxemon"],
            },
        }
    )
    production_db = ModData(
        database_config, ModelLoader(load_model_map(database_config.model_map))
    )
    production_db.preload()
    production_db.load()
    metadata = production_db.mod_metadata.get_mod_metadata(mod_slug)
    production_db.mod_metadata._mod_metadata[mod_slug] = metadata.model_copy(
        update={
            "starting_map": f"{episode.metadata.start_map}.tmx",
            "starting_position": episode.metadata.start_position,
        }
    )
    runtime.db = production_db
    validator.reset()
    validator.set(Validator(production_db))

    from tuxemon import main as tuxemon_main

    config = CONFIG.copy()
    config.mods = [mod_slug]
    config.config_model.game.skip_titlescreen = True
    config.config_model.display.splash = False
    config.logging.configure()
    tuxemon_main.main(config=config, context=context, load_slot=None)
