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
