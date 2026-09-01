# Tuxemon Architecture for World Synthesis

Baseline: upstream `development` commit `59a34164f`, inspected 2026-09-01.

## Verified launch

The source checkout launches on Windows with Python 3.12.10, pygame-ce 2.5.7, and the pinned project requirements. `python run_tuxemon.py` opened a responsive `Tuxemon` native window and reported the expected Git hash. This is a real engine launch, not only an import test.

## Runtime path

`run_tuxemon.py` initializes pygame, loads the user configuration, builds a `LocalPygameClient`, and drives the startup state machine. `GameLauncher` reads a selected mod's `mod.yaml`, creates its starting player, loads the starting TMX map, teleports to the configured tile, and applies the player template.

Asset lookup is mod-based. `fetch_mod_asset_roots` resolves configured mod directories and `fetch_asset(category, path)` searches those roots. The experiment therefore lives in its own `mods/world_synthesis/` overlay while upstream `mods/tuxemon/` remains unchanged.

## Maps and rendering

- Source: `tuxemon/map/loader.py`, `tuxemon/map/tuxemon.py`, `tuxemon/map/view.py`.
- Format: finite orthogonal TMX, normally 16×16 tiles, loaded by `pytmx`.
- Rendering: `pyscroll.BufferedRenderer`; visible tile layers are drawn in Tiled order.
- Tall sprites: `TuxemonMap.SPRITE_LAYER_INDEX == 2`, so the convention is two ground/lower layers, then player/NPC sprites, then later overhang layers.
- Map properties: `slug`, `edges`, `inside`, `scenario`, `map_type`, plus optional cardinal description properties.

## Collision

Collision is semantic, not inferred from pixels. `TMXMapLoader.load_collision_data` combines:

1. tile properties such as `enter_from`, `exit_from`, `endure`, and movement surfaces;
2. embedded tile collider objects; and
3. map objects whose type begins with `collision`.

Closed rectangular collision objects are snapped to the tile grid and expanded into blocked cells. Open polylines become directional collision edges. For generated maps, explicit merged rectangles are the clearest and least fragile contract.

## Events, NPCs, and progression

Objects of type `event` or `init` are read from TMX. Their pixel bounding boxes are divided by the native tile size. Properties are naturally sorted, then grouped by prefixes:

- `cond*`: preconditions;
- `act*`: sequential actions;
- `behav*`: interaction behaviors such as `talk npc_slug`.

NPC definitions are YAML records under `db/npc/`. `create_npc slug,x,y` creates and places a database-defined NPC. Trainer parties may be defined in that NPC record or added by actions before `start_battle player,npc`.

Dialogue is either a translated message key passed to `translated_dialog` or an NPC dialogue profile selected by `char_talk`. Game flags/variables live on the player and are manipulated with `set_variable`, `clear_variable`, `variable_set`, and `variable_is`. Items and monsters are typed YAML database records referenced by slug.

Wild encounter objects call `random_encounter encounter_slug,total_prob`; the slug resolves to a YAML encounter table containing monster slugs, rates, level ranges, held items, modifiers, and optional variable conditions.

## Upstream inventory

The archaeology scripts found:

- 263 TMX maps;
- 79 tileset images;
- 209 overworld sprite sheets;
- 1,141 NPC records (many files contain lists);
- 411 monster records;
- 226 item records;
- 33 encounter-table files.

The complete inventory is `ASSET_CATALOG.json`; map metrics are in `artifacts/analysis/upstream_map_metrics.json`.

## Isolation decision

No engine rewrite is needed for the first milestone. New source content belongs in `mods/world_synthesis/`; specifications and compiler code live in `world_synthesis/`; generated TMX is clearly marked and remains editable in Tiled. Upstream remains available as the `upstream` Git remote.
