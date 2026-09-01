# Map Grammar

## Tiled contract

Generated maps are finite orthogonal TMX with 16×16 tiles. They use external upstream TSX files and CSV layer data for readable diffs. The standard generated stack is:

1. `Ground`: base terrain;
2. `Paths and Water`: terrain transitions and traversal surfaces;
3. sprite insertion point used by Tuxemon;
4. `Objects`: vegetation, rocks, fences, and landmark bases;
5. `Above Player`: tree crowns or other overhangs;
6. `Collisions`: merged semantic rectangles;
7. `Events`: warps, NPC interactions, encounters, secrets, and initialization.

The map compiler uses Tiled global IDs correctly: `gid = firstgid + local_tile_id`. Gameplay truth is not inferred from the rendered tile.

## Authored-feeling outdoor grammar

Every route must declare:

- a dominant landmark visible from the critical path;
- at least two named sub-areas with different density/composition;
- a readable path joining paired exits;
- varied width and at least one compression/release sequence;
- one optional loop or branch with a reward;
- asymmetric boundaries and clustered, not uniform, decoration;
- encounter vegetation that communicates risk;
- NPC placement tied to a plausible activity;
- deliberate negative space around decisions and landmarks.

Recommended rhythm:

```text
settlement threshold → compression → first reveal → encounter pressure
→ rest/landmark → optional loop/secret → final reveal → destination threshold
```

## Compiler primitives

- `paint_region`: polygon or rectangle terrain fill;
- `rasterize_path`: deterministic polyline with authored width changes;
- `paint_water`: blocked water plus explicit crossings;
- `place_boundary`: clustered tree/rock edge with openings;
- `place_landmark`: explicit authored anchor and clearance;
- `scatter_cluster`: bounded seeded decoration inside a semantic zone;
- `place_object`: explicit meaningful prop;
- `merge_collision`: combine contiguous blocked cells into rectangles;
- `create_event`: typed Tuxemon event object;
- `create_warp`: paired, validated transition;
- `create_encounter_zone`: visible vegetation plus encounter event.

## Validation rules

Blocking errors include invalid TMX/tileset references, illegal GIDs, out-of-bounds objects, blocked spawns/warps, unreachable exits/NPCs/landmarks/rewards, missing event references, and progression dead ends. Warnings cover excessive empty space, overly straight paths, uniform decoration, weak landmark separation, excessive density, and unrewarded dead ends.

Generated TMX is inspectable and editable in Tiled. Manual edits are allowed for review, but durable changes should normally be brought back into MapSpec so rebuilding does not erase them.
