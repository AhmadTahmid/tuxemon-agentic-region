# Implementation deviations

## Design lock

No creative-brief deviation has been accepted.

The following implementation choices clarify, rather than alter, the brief:

- The episode uses seven maps: five outdoor/dungeon maps and two interiors.
- The three starter candidates are Anoleaf, Flounce and Rockitten.
- Jemuar is the provisional climax creature.
- The three resonant controls are physically labelled runoff, cradle and
  hoist controls. Tovin's dialogue supplies the same causal order.
- The episode ends in free-roam resolved Ashenbell with an episode-complete
  flag and forward-hook interaction, rather than forcing a credits screen.

Any later departure must record the intended requirement, actual behaviour,
reason, impact and whether it should be revisited.

## Milestone 2 — golden path

The existing monster catalogue supplies Jemuar's battle sprite but no Jemuar
overworld/NPC sheet. The quarry encounter therefore uses the existing
`landrace` overworld sheet and `snugglepot` opponent sheet as a staging proxy;
the combat party contains a real level-11 Jemuar and enters the real combat
system. This is visually imperfect but not a fake boss. Composition review in
Milestone 4 must either retain this documented proxy or select a better
existing legal sheet.

Side quests, the full three-control puzzle, optional trainer beats and the
shortcut are deliberately absent from the Milestone 2 runtime. This follows
the mandated implementation order and is not a scope reduction; they are the
next commit's work.

## Milestone 3 — puzzle error handling

The design lock proposed resetting local puzzle progress after an incorrect
control. With ordinary Tiled button conditions, correct and reset events on
one anchor can both observe the same held input after the correct event mutates
state. To avoid a race and avoid adding an engine action for one puzzle, an
out-of-order control now makes no state change. The visible labels and Tovin's
causal clue still give the order, and the more forgiving behaviour cannot make
the puzzle permanently inaccessible.

Squabbit, the garden Caper and the Rockat gate use the same existing
`landrace` overworld proxy as the Jemuar staging because those monster species
do not provide compatible overworld NPC sheets. Caper and Rockat enter real
combat as NPC parties, so those two authored encounters are trainer-type under
the hood and cannot be captured. The optional South wild zone remains the
episode's real capture opportunity. A reusable distinct-ID scripted-wild
battle would remove this presentation compromise, but adding it was not
necessary for the episode's progression.

## Milestone 4 — existing-art composition

The village civic plinth uses the existing `core_city_and_country` fountain
set because the repository has no confirmed overworld stone-bell memorial
stamp in the reviewed compatible family. Dialogue and interaction identify it
as Ashenbell's memorial/warning focal point; its water imagery also supports
the drainage theme. This is a visual approximation, not a story change.

The quarry reuses cave details embedded in `core_outdoor` instead of mixing a
second incompatible cave atlas into a single generated map. This limits wall
autotiling and machinery variety, but preserves a coherent existing-art
family and keeps the production compiler generic.

## Milestone 5 — validation and launch boundaries

The design audit proposed mission records for journal visibility. The final
episode uses namespaced persistent variables and concise in-world reminders,
but does not add a mission-journal entry. This avoids authoring a parallel
mission database solely for one episode, at the cost of less explicit objective
tracking in menus. Human testing must determine whether dialogue and geography
keep the goal clear enough.

Save persistence was exercised through the engine's actual state models and
variable manager, not through a manual save-menu/reload playthrough. The real
client was launched and the opening event was observed, but a complete human
playthrough has not yet been recorded. Therefore target duration, enjoyment,
all interaction ergonomics and end-to-end difficulty remain unverified.

## First external playtest — tutorial resolution semantics

The frightened Shybulb tutorial is resolved when the scripted wild encounter
ends by victory, capture or retreat. Tuxemon records trainer results for
`battle_outcome`, but does not record `CombatType.MONSTER` encounters there.
The original trainer-history condition therefore caused an infinite retrigger.
The repaired event sets `low_bell_tutorial_cleared` after the asynchronous
encounter returns and grants the capture kit in the same sequence. Allowing a
retreat is consistent with Nera's goal of giving the frightened creature room,
and prevents the tutorial from requiring a specific combat outcome.

## Second external playtest — village arrival dialogue lifecycle

The original Ashenbell entrance chained four automatic `DialogState` actions
and recorded `low_bell_story:investigation` only after every box closed. A
player reached a dialogue box that would not advance, leaving both movement
and progression blocked. The arrival now records the guarded progression state
before opening one concise prompt. Mara, Iven and Nera deliver their distinct
accounts through their existing player-initiated conversations around the
memorial. This preserves the intended conflict while removing the fragile
modal chain and makes an interrupted arrival safe to reload.
