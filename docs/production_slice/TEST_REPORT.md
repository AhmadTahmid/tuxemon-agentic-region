# Test report

## Milestone 1 — design lock and capability audit

Status: capability source audit complete; no Low Bell runtime exists yet.

Confirmed by source and existing content inspection:

- data-driven three-choice starter flow;
- real trainer and catchable wild combat;
- items and capture devices;
- variable- and mission-based quest state;
- conditional event dialogue;
- NPC create/remove staging;
- persistent variables, missions, inventory, party and battle history;
- conditional teleport shortcuts;
- resettable multi-step switch logic;
- existing music and relevant wind/stone/metal/bell SFX;
- save and ending-state mechanisms.

No capability is yet claimed as exercised in the Low Bell client. Milestone 5
will contain command output, deterministic hashes, loader checks and graphical
launch evidence.

## Milestone 2 — golden path

The isolated build command produced seven maps and reproducible SHA-256 hashes.
Eight focused production tests passed, covering schema/reference integrity,
real battle declarations, side-quest independence, interaction anchors,
two-build determinism, generated TMX topology, all-map loading through the
real `TMXMapLoader`, and activation of the Low Bell NPC/encounter database
overlay.

Ruff passed for the new package and test. Mypy passed for the new package.
The real graphical launcher reached and continuously rendered the South
Approach with the isolated database and corrected music slug; it was then
stopped manually. This is launch evidence, not a complete playthrough claim.

## Milestone 3 — content completion

Twelve focused production tests now cover the seven authored combats, both
optional quest completion paths, three secret flags, the three-step puzzle,
paired optional shortcut warps, six-plus resolved village voices, side-quest
independence and static reachability of every mandatory interaction and warp.
The reachability check found blocked interior exit tiles in the first content
build; explicit door openings were authored for both interiors and the test
then passed. The real database overlay and all seven real TMX loads continue
to pass.
