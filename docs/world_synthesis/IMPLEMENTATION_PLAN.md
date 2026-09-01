# First Milestone Implementation Plan

Status: Phase 0/1 and the first polished-route milestone are complete.

1. Verify upstream launch and freeze the inspected development commit.
2. Catalogue TMX, tilesets, sprites, NPCs, monsters, items, encounters, and event vocabulary.
3. Define Pydantic WorldSpec/MapSpec contracts and a reviewed semantic tile palette.
4. Compile a single authored route to readable TMX plus custom NPC/encounter YAML.
5. Validate schema, IDs, bounds, collision, warps, reachability, events, trainers, secret, and encounter zones.
6. Render a deterministic full-map PNG and write a structured critic report.
7. Revise at least once from recorded critique and retain revision history.
8. Load the generated TMX through Tuxemon and launch the isolated mod.
9. Add focused tests, document exact commands, commit logical milestones, and push.

Acceptance: the route is traversable between two conceptual settlements, includes a landmark, optional loop, secret, encounters, and meaningful NPC/trainer locations, and passes both the independent validator and Tuxemon's real TMX loader.

Result: accepted. Revision 2 passes with zero blocking validator errors; all
focused tests pass; the real loader reports a 40x48 map with collision and
events; and the isolated campaign was launched and moved through in the normal
Tuxemon client. Full-region expansion remains intentionally pending.
