# Locked creative brief

Status: authoritative production lock. Local changes are allowed only when a
real Tuxemon capability requires an adaptation, and every such change must be
recorded in `IMPLEMENTATION_DEVIATIONS.md`.

## Product target

Build one original, beginning-to-end playable Tuxemon episode titled
**Ashenbell: The Low Bell**, targeting 60–90 minutes on a first playthrough.
It must provide an opening hook, starter onboarding, exploration, capture,
wild and trainer battles, a believable settlement, recurring characters, an
escalating grounded mystery, two optional side quests, one observed-clue
environmental puzzle, an optional discovery area, a persistent shortcut, a
boss-like climax, a return-to-town resolution, changed post-climax dialogue,
and a modest forward hook.

This is not another R0/R1/R2 comparison. Existing benchmark evidence remains
available but its geometry and frozen palette do not constrain this episode.

## Theme and setting

Ashenbell is an upland village founded around an old warning network. Resonant
stone bells with metal tongues once warned three valleys about storms and
landslides. A quarry collapse killed workers and ended production decades
ago. The warning system was retired, and each year the village now holds a
silent memorial rather than ringing the bells.

A lower, unfamiliar bell-like tone has recently sounded at night, coinciding
with heavy rain and west winds. Creatures are abandoning their usual habitats
and entering paths, gardens and buildings.

The explanation is grounded:

- rainwater has returned to cracks in the abandoned quarry;
- buried fittings and fractured resonant stone are vibrating;
- a large creature nesting near the buried assembly amplifies the vibration;
- Iven's unofficial survey disturbed drainage around the quarry.

The story concerns responsibility, preservation, and the difference between
honouring the past and mechanically recreating it. Memory can protect a
community, but can also trap it. Modest ambiguity about the exact sound may
remain, but the four physical facts above must be evidenced.

## Player role and cast

The player is a junior field courier and new monster handler travelling with
field naturalist Nera. The first low tone drives frightened creatures onto the
South Approach. Nera is practical, observant and compassionate; she supplies
the starter and tutorial, but does not solve the mystery for the player.

Mara is Ashenbell's precise, guarded bellkeeper and historian. She preserves
the names and facts of the collapse, rejects superstition, and fears that the
new tone will provoke panic or romanticize a lethal system.

Tovin is a retired quarry worker who understands the old hoist and drainage.
He carries guilt for approving a final shift and initially refuses to enter
the quarry. His knowledge and emotional change must emerge gradually.

Jori is a village child whose companion Squabbit followed the tone and went
missing. Finding Squabbit is optional and personal, not a mandatory
world-saving task.

Iven is a trader who believes reopening the quarry could keep Ashenbell alive.
He commissioned a limited unofficial survey and cleared an old drainage
channel. He concealed this involvement, but is not an evil antagonist and
must ultimately accept responsibility.

Sela is an evidence-driven, cautious upland surveyor. She observed the
wind/runoff correlation and knows the terrain, but cannot enter the quarry
alone because of creature activity.

Rook is the route warden and trainer at Highland Pass. He tests whether the
new handler can proceed safely and conveys practical local knowledge.

## Locked story structure

### Act 1 — The sound

Open on the South Approach. Within two minutes the low tone affects nearby
creatures, Nera offers a meaningful choice of three existing starters, and a
real tutorial battle occurs. Before Ashenbell, offer a catchable encounter,
an environmental interaction, a small detour reward and evidence of unusual
creature movement.

### Act 2 — Ashenbell

The organized village has a productive southern edge, compact homes, a civic
memorial/warning plinth, a northern road and at least two enterable interiors.
Mara argues for facts and calm; Iven argues that infrastructure could revive
the village; Nera focuses on displaced creatures; Tovin evades the quarry;
Jori raises the missing Squabbit; Sela reports the weather correlation. The
main investigation begins here. At least six village NPCs change dialogue
across INTRO, INVESTIGATION, QUARRY_DISCOVERED and RESOLVED states. Exposition
must be divided among short conversations, map evidence, interactions and
optional discovery.

### Act 3 — Highland Pass

The pass is exposed, rocky and constrained rather than a padded corridor. It
contains Rook's trainer battle, Split Crown Ridge, a stronger low-tone event,
evidence that terrain transmits the sound, a clear quarry branch, an optional
reward, and a distinct highland ecology.

### Act 4 — Old Bell Quarry

The quarry works as a small dungeon across an exterior and lower works. It
shows the collapse, old fittings, runoff through fractured stone, Iven's
survey disturbance, Tovin's useful knowledge, Squabbit in or near the quarry,
an existing-item reward, a hoist, and a stateful shortcut.

Three labelled resonant controls form a modest environmental puzzle. Its
causal sequence must be observable and reinforced by earlier dialogue; an
incorrect interaction cannot permanently block progress.

An unusually strong existing creature is frightened and territorial near the
buried assembly. Its movement amplifies the tone. A real battle is followed by
an environmental action that reduces vibration and resolves the
drainage/hoist problem.

### Act 5 — Return

The episode returns the player to Ashenbell rather than ending at the boss.
Jori reacts to Squabbit's outcome, Iven acknowledges the survey, Tovin faces
part of his guilt, Mara updates the memorial's meaning, Nera notes creatures
returning, the shortcut stays open, a main reward is given, and at least six
NPCs have changed dialogue. End on a small courier/naturalist hook, not a new
region implementation.

## Optional quests

**Jori's Squabbit:** begins in Ashenbell; clues lead toward the tone and
quarry; Squabbit is present in gameplay; returning it changes dialogue and
gives a modest reward. It can never gate the main story.

**Names of the Silent Shift:** Mara asks for three weathered records across
existing areas, including one optional path. Completion deepens Tovin and the
memorial and grants an existing useful item. It can never gate the main story.

## Production budget and constraints

- 6–8 playable maps including interiors.
- 14–18 functional NPCs; no generic filler dialogue.
- 5–7 trainer or scripted combats, plus random wild encounters and one climax.
- 8–12 ecologically placed existing monsters.
- Two side quests, one puzzle, three curiosity rewards and one shortcut.
- At least five recurring/key NPCs change across story states.
- Every outdoor map contains multiple meaningful beats.
- Every optional branch pays off in reward, evidence, interaction, shortcut,
  landmark, view or rare encounter.
- Dialogue is concise, character-specific and respects knowledge boundaries.
- Use only reviewed existing legal Tuxemon art, audio, monsters and items.
- Use WorldSpec and deterministic compilation where practical. Reusable
  production primitives are allowed; map-ID branches and generated-TMX edits
  are not.
- Automated validation proves mechanics, never fun. Human responses remain
  separate and are not collapsed into a synthetic score.

Stop after the complete episode, evidence, playtest launcher and production
feasibility report. Do not expand into a full game.

