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

## Milestone 4 — composition and presentation

The static review renderer emits full and collision/event/encounter debug
views for all seven maps. Review exposed two real presentation defects before
commit: a stamp that combined two neighbouring building atlas entries and a
cave-rock detail repeated as a terrain fill. Both were corrected in the
canonical semantic palettes, without map-ID-specific compiler code.

Fourteen focused tests now also require every runtime map to avoid the old
prototype palette, verify each selected source tileset exists, and compare
hashes across two independent render passes. The asset-review atlas windows,
seven full renders and seven debug renders are preserved as reproducible
evidence.

## Milestone 5 — validation and playtest build

The final focused production suite contains 17 tests and passes. The complete
world-synthesis suite passes: **55 passed**. The complete repository suite ran
all 4,291 tests: **4,290 passed, 1 failed** in 104.96 seconds. The remaining
failure is the pre-existing Windows-specific assertion in
`tests/tuxemon/test_map_loader.py::test_remove_from_cache`, where removing the
synthetic path `/fake/path` returns false. No production-slice test failed.

`python -m world_synthesis.production_slice validate low_bell` passes ten
transparent acceptance groups:

- strict schema and reference validation;
- seven-map connectivity;
- the 18-event mandatory sequence and required final state;
- two independently completable, non-blocking side quests;
- usable interaction anchors and collision-aware critical reachability;
- existing asset, monster, item and dialogue references;
- paired persistent shortcut plus independent ordinary route;
- resolved dialogue for nine declared characters;
- key-variable save/model round trip;
- real TMX loading and NPC/encounter overlay activation.

The real client launched the isolated Low Bell mod and rendered the opening
South Approach event. `graphical_launch_game.png` and its SHA-256 are preserved with
an empty stderr log. The process was stopped after evidence capture. This is a
graphical smoke test, not a completed human playthrough.

The playtest launcher and questionnaire are tested without producing a fake
aggregate score. No completed human response is bundled, so duration, fun,
balance, emotional effect and ending ergonomics are still pending human
acceptance.

## First external playtest repair — tutorial encounter loop

The first player session exposed a critical bridge loop: the tutorial used
`battle_outcome player,won,wild_encounter`, but Tuxemon does not record
`CombatType.MONSTER` results in trainer battle history. The condition could
therefore never become true, so the touch event immediately retriggered after
winning or running.

The tutorial now follows the existing upstream scripted-wild pattern: dialogue,
the asynchronous wild encounter, reward/heal, and an explicit persistent
`low_bell_tutorial_cleared` flag execute in one ordered event. Win, capture or
retreat all resolve the frightened-creature obstruction and cannot retrigger
it. A regression test forbids battle-history conditions against
`wild_encounter`, verifies action ordering, and the generic acceptance
validator now reports that unsupported condition as a missing reference.

After rebuilding, all 17 focused production tests pass and the complete
acceptance validator passes.

## Second external playtest repair — village arrival dialogue lock

The next player session exposed a critical modal lock on first entering
Ashenbell. The touch event opened four independent translated-dialog actions
before producing its progression state, so an interrupted or stalled dialog
left the player immobile and the arrival unresolved.

The entrance now sets `low_bell_story:investigation` first and opens one short
arrival prompt. The three character perspectives remain available as separate
player-initiated conversations at the memorial. Regression coverage asserts
the state-first ordering, exactly one dialog on this arrival, and no chained
adjacent modal dialogs on any touch event. The generic validator rejects future
unsafe touch-dialog chains while allowing dialogue separated by gameplay, such
as the tutorial's pre- and post-battle lines.

After rebuilding, all **19 focused production tests** and all **57 complete
world-synthesis tests** pass. The production acceptance validator passes.

### Follow-up: remove the modal entrance prompt

The player confirmed that the replacement single prompt could still trap the
client. It was not an ending or an intentional gate. Because the arrival's
only required mechanical work is producing investigation state and a faint
return point, automatic dialogue has now been removed from that event. The
arrival regression requires zero translated-dialog actions; character-specific
scene content remains in the three nearby talk events.

### Follow-up result: movement remains locked

The next external run entered Ashenbell without the prompt but still could not
move. This proves that prompt removal did not repair the underlying
critical-path failure. Static compilation confirms that the incoming
destination and its neighbors are not collision-blocked, while the arrival
event now contains only synchronous state assignments. Runtime
transition/control release is the leading unverified failure area.

This bug remains open as `LB-004` in `EXTERNAL_PLAYTEST_BUGS.md`. The previously
reported 19 focused tests, 57 world-synthesis tests and passing acceptance
validator did **not** establish end-to-end playability. Their scope does not
simulate transition cleanup, input delivery or movement-control state in a
real critical-path playthrough.
