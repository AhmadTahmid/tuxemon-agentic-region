# External playtest bugs

This log records observed real-client failures separately from automated
acceptance. A passing schema, loader, reachability or state-graph check does
not close an entry. Only a repeat playthrough through the affected scene can
verify a runtime repair.

## LB-001 — tutorial wild encounter retrigger

- Severity: critical-path blocker
- Observation: the frightened Shybulb battle retriggered on the bridge after
  either winning or running.
- Cause: the event queried `battle_outcome` for a `wild_encounter`, but Tuxemon
  records that history for trainer battles rather than ordinary wild combat.
- Repair: use an explicit persistent `low_bell_tutorial_cleared` producer after
  the asynchronous battle returns.
- Commit: `e5b12f6d2`
- Status: repaired and regression-tested; subsequent external play reached
  Ashenbell, confirming this blocker no longer prevented that session.

## LB-002 — chained village-arrival dialogue lock

- Severity: critical-path blocker
- Observation: entering Ashenbell opened several story text boxes and
  eventually left the player stuck in a bottom-screen dialog.
- Cause established in authored content: the touch event chained four modal
  `translated_dialog` actions and produced investigation state only after all
  four returned.
- First repair: produce state first, replace the chain with one concise prompt,
  and distribute character information to player-initiated conversations.
- Commit: `29ed01edb`
- Status: superseded; external play showed that the remaining prompt also
  blocked.

## LB-003 — single village-arrival prompt lock

- Severity: critical-path blocker
- Observation: the replacement “Ashenbell's memorial square is tense…” prompt
  appeared but could not be dismissed.
- Mitigation: remove all automatic dialogue from the village arrival event.
- Commit: `d858da15c`
- Status: the modal symptom was removed, but the next playtest exposed LB-004.
  The underlying runtime control problem was not proved fixed.

## LB-004 — movement remains locked after Ashenbell transition

- Severity: critical-path blocker
- Observation: after automatic arrival dialogue was removed, the player entered
  Ashenbell with no text box but still could not move.
- Current status: **OPEN / UNRESOLVED**.
- Static evidence: the incoming destination is `(22, 38)`; it and the adjacent
  arrival cells are not collision-blocked. The guarded arrival event contains
  only synchronous `set_variable` and `set_teleport_faint` actions.
- Current inference: runtime movement controls may not be released after the
  `transition_teleport` lifecycle. This is not yet proved with runtime tracing.
- Required diagnosis: instrument transition start, teleport completion,
  `WorldTransition.fade_in` cleanup and `MovementManager.unlock_controls`; then
  exercise South Approach to Ashenbell in the real client.

## What automated testing missed

All production acceptance checks and 57 world-synthesis tests passed while the
real critical path remained blocked. Those checks established useful but
narrower facts:

- TMX files parse and load, but loader acceptance does not simulate input.
- Static flood-fill proves the destination is geometrically walkable, but does
  not prove `MovementManager` permits movement.
- State producer/consumer checks prove declared ordering, but not asynchronous
  action completion or state-stack behavior.
- Dialogue-reference checks prove locale keys exist, but not that a real player
  can dismiss every modal state.
- The graphical test was an opening-map smoke launch, not a golden-path run.
- Save-state model round trips do not exercise the real save UI or restore an
  interrupted event lifecycle.

The production slice is therefore **not currently beginning-to-end playable**.
Automated acceptance is necessary evidence, not a substitute for critical-path
client playthroughs.
