# Ashenbell R2 revision instructions

Revise content once; do not change compiler or schema.

1. Expand the South Route bridge by one cell east. Evidence: ordinary validation reports `path_blocked` at `(21, 17)`, where the critical road clips Bellwater outside the authored bridge.
2. Reroute the village residential/garden lane through declared fence entrances and move the west plinth boulder off that lane. Evidence: `path_blocked` at `(9,20)`, `(10,20)`, `(11,20)`, `(12,21)`, and `(14,17)`.
3. Move the pass scree rock away from the unlocked ridge stair. Evidence: `path_blocked` at `(8,32)`.
4. Make the quarry hoist produce `r2_shortcut:open`, the exact monotonic variable consumed by both maps. Evidence: the consistency audit finds consumers but no matching producer and a produced variable with no matching consumer.
5. Anchor every player-facing story interaction to visible collision and leave a reachable adjacent tile. Evidence: in-client hoist verification showed that a traversable event cell makes directional input move the player onto the cell instead of leaving the player facing it. The generic follow-up audit found the same blind spot at the shortcut gates, pass echo, quarry evidence, and cache.
6. Move the village and pass shortcut interactions to dedicated signs beside, rather than on, their approach paths.
7. Attach the pass echo to the west cairn stone, the quarry evidence to an existing worked stone, and the hoist interaction to its existing warning sign.
8. Move the potion cache off the lower-cut centerline and add a blocking rock marker at the same cell.

Retain the sparse-decoration warning for the exposed pass. Do not add ornamental density merely to suppress a heuristic. Do not alter topology, story facts, encounters, reward, map dimensions, or optionality.
