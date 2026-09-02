# Decisions

## D001 — Preserve Tuxemon as upstream

The new repository retains full upstream history. `upstream` points to `Tuxemon/Tuxemon`; experimental content is isolated in `mods/world_synthesis/` and tooling in `world_synthesis/`.

## D002 — WorldSpec before TMX

High-level intent is YAML validated by Pydantic. TMX tile arrays are compiled output. This keeps agent reasoning proportional to landmarks, paths, zones, and pacing rather than tile count.

## D003 — Reviewed fixed palette

The first route uses one coherent existing tileset family and a small reviewed tile vocabulary. Automatic filename classification remains advisory.

## D004 — Explicit collision

The compiler emits merged collision rectangles from semantic blocked cells. Visual tiles and atlas transparency never determine walkability.

## D005 — Static critic first

The initial critic is a reproducible rubric fed by map metrics and authored evidence. It does not pretend to be a perceptual model. Visual screenshots remain required for human/agent revision.

## D006 — Freeze compiler behavior during A/B/C authoring

Glasswind-specific defaults were first converted into narrow reusable outdoor
primitives: typed boundary/base terrain, forest and safe zones, explicit props
and fence entrances, encounter tables, starter metadata, and generic database
exports. After this preparation commit, all Deep Forest variants must be made
through content. Any later compiler change invalidates the code-free claim and
must be recorded in `artifacts/world_synthesis/generalization_log.json`.

## D007 — Separate structural heuristics from human evaluation

The deterministic critic reports a `structural_design_score`; it is neither a
visual-quality rating nor evidence that a map is enjoyable. Blind human
playtest answers are stored separately and are never averaged into that score.

## D008 — Equivalent allowance, not identical geometry

Deep Forest A/B/C share dimensions, seed, engine, asset vocabulary, NPC/trainer
counts, encounter zones, dominant-landmark allowance, optional content and
reward budget. Their geometry and authorship effort differ because generation
method is the independent variable. A is competent rather than intentionally
weak; B receives only parse/load repairs (none were needed); C retains its full
revision history.

## D009 — Blind assignment, revealed post-test

The play launcher exposes only “Mossveil Passage” and a random session ID. It
logs the hidden method before launch and stores the questionnaire separately.
The gallery reveals method identity only for post-test analysis. Automated
structural scores never enter human response files.

## D010 — Re-freeze before the Ashenbell horizon variants

The pre-authoring audit found two shared missing primitives: conditional story
events and a small building composition using existing atlas tiles. Both were
implemented generically before R0/R1/R2 authoring and the compiler was
re-frozen at SHA-256
`4e94b1ae4e531dd70da33b162b8329a0d0d2cc5a71190633e4a560b1ff7f156a`.
No variant-specific compiler change is allowed after that point.

## D011 — Cross-map facts are reviewed, not scored

Ashenbell mechanically verifies topology, paired warps, transition targets,
optional bypasses, state producers/consumers and stable reachable anchors for
player-facing interactions. Geography, NPC facts, ecology, identity and
repetition receive evidence-linked categorical review. No aggregate
world-quality score is produced, and human responses remain in the separate
human-evaluation directory.

## D012 — Preserve invalid one-shot design evidence

R1 receives compatibility-only repairs for YAML quoting, the event-condition
operator and an invalid documented sprite reference. Its three path/collision
errors and seven unstable player-facing interaction anchors are not redesigned
after inspection. The maps remain loader-valid, but R1 is explicitly not
reported as passing authored-path or cross-map progression acceptance.

## D013 — A reachable event cell is not necessarily interactable

Tuxemon's `char_facing_tile` condition requires the player to stand on a
cardinal neighbor while facing the event. A traversable target cell can absorb
directional movement instead. The horizon audit therefore requires a player-
facing event to overlap collision or a spawned NPC and to have a reachable
cardinal neighbor. This generic validator exposed R0/R1 failures and informed
the permitted R2 content revision; it did not change the frozen compiler.
