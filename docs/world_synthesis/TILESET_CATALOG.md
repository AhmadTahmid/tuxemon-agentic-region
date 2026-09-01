# Tileset Catalogue

The automated catalogue covers 79 tileset images and records dimensions, TSX contracts, animation counts, tile-property names, semantic guesses, and uncertainty in `ASSET_CATALOG.json`.

## Recommended coherent outdoor family

The first milestone uses Tuxemon's existing `prototyping_outdoor.tsx` family because it provides a visually coherent compact vocabulary: multiple grass/path surfaces, water, bridges/planks, conifer and broadleaf trees, shrubs, flowers, rocks, fences, signs, stairs, and building fragments. It is deliberately preferable to mixing unrelated packs merely for asset count.

The richer `core_outdoor*.tsx` family is suitable for later maps and is heavily used upstream:

- `core_outdoor.tsx`: general ground, paths, flowers, fences, and set dressing;
- `core_outdoor_nature.tsx`: tree, rock, vegetation, seasonal, and cliff families;
- `core_outdoor_water.tsx`: animated water, banks, waterfalls, rocks, and coast transitions;
- `core_buildings.tsx`: exterior structures and doors;
- `core_set pieces.tsx`: specialized landmark and interior pieces.

These are atlases, not semantic APIs. Individual IDs require visual review. The milestone compiler therefore defines a small reviewed palette with screenshots/atlas coordinates and leaves uncertain tiles unregistered.

## Collision-bearing metadata

Some TSX tiles define `enter_from`, `exit_from`, `endure`, `surfable`, speed modifiers, or embedded colliders. The catalogue records counts of these properties. Generated gameplay collision remains explicit in the map unless a selected tile's behavior is intentionally relied upon and tested.

## NPCs and creatures

The upstream mod contains 209 overworld sprite sheets and 1,141 NPC records. Semantic role cannot be safely inferred from color or filename alone, so the catalogue records names and low confidence where appropriate. The milestone reuses reviewed sprites (`adventurer`, `botanist`, `fisher`, and `ranger`-like existing sheets) and creates new NPC database records that reference them.

There are 411 monster records with structured types, terrains, tags, and shapes. Encounter selection uses ecology metadata first, not visual guessing.

## Uncertainty policy

`unclassified` means exactly that. It is not treated as an error, and the planner must not claim a visual meaning until a human or visual review assigns one. This prevents filename archaeology from becoming fabricated asset semantics.
