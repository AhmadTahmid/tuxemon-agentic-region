# Ashenbell: The Low Bell — production feasibility report

> **External-playtest status:** failed. The current build is not verified as
> beginning-to-end playable. A real player remains unable to move after the
> South Approach-to-Ashenbell transition (`LB-004`), despite passing automated
> validation. Claims below about implemented content describe authored and
> loadable coverage, not successfully traversed content.

## 1. Could the locked creative brief be implemented faithfully?

Not yet at the required production-feasibility level. Substantially at the
authored and mechanically validated level, the isolated
episode implements the opening resonance, three-way starter choice, tutorial,
capture opportunity, organized village, recurring cast, investigation,
Highland Pass, two side quests, three-control puzzle, shortcut, real Jemuar
battle, separate physical dampening action, return resolution, changed
dialogue and ending hook. The grounded explanation and character conflicts are
preserved.

The fidelity limits are explicit: several creatures use an existing overworld
proxy; the memorial is represented by a compatible existing fountain/plinth;
objective state is not exposed through a mission journal; and no completed
human playthrough yet establishes the intended 60–90-minute duration. These do
not change the central story, but they weaken presentation and usability.
More importantly, the unresolved Ashenbell transition blocker prevents a
beginning-to-end playthrough and therefore prevents claiming faithful playable
implementation.

## 2. Which intended experiences survived implementation?

The causal mystery survived: runoff, fresh survey disturbance, resonant stone,
metal fittings and Jemuar's frightened movement are revealed across different
places and characters rather than in one speech. Player responsibility also
survived because winning the boss battle does not solve the disturbance; the
player must stabilize the mechanism and dampen the assembly.

The episode contains substantial authored structure: 7 maps, 17 logical NPCs,
71 events, 7 authored combat beats, 7 wild encounter zones, 2 completable side
quests, 3 secrets, 1 observed-order puzzle, 1 persistent bidirectional shortcut
and 9 characters with resolved-state dialogue. The real client renders the
opening and the real loader accepts every authored event.

## 3. Which intended experiences were weakened or lost?

Creature staging is the clearest loss: Squabbit, Caper, Rockat and Jemuar lack
compatible overworld sheets and therefore share an existing proxy outside
battle. The quarry and settlement are compositionally distinct but remain
limited by reusable tile stamping rather than hand-authored autotile detail.
The absence of a journal may weaken goal clarity on a long first playthrough.

No human evidence yet proves pacing, character memorability, emotional
investment, optional-content value, balance, or that resolved Ashenbell feels
meaningfully changed. Static coverage and valid state transitions cannot prove
those experiences, so the project does not claim that they survived.

## 4. How much generic engine/compiler work was required?

No upstream Tuxemon engine file and no frozen benchmark compiler file was
modified. Existing actions supplied starter choice, battles, capture, items,
variables, conditions, audio, NPC staging and warps.

A separate reusable production layer was required: a strict EpisodeSpec,
deterministic multi-map compiler, database/locale overlay writer, static
full/debug renderer, declarative acceptance contract, cross-map/state/reference
validator, isolated launcher and human playtest wrapper. None branches on an
Ashenbell map ID, though the acceptance YAML appropriately declares this
episode's required sequence.

## 5. How much manual or agent revision was required?

Implementation proceeded through the five required commits rather than one
repair pass. Validation caused four material revisions: opening interior doors
after collision reachability failed; separating an accidental double-building
atlas stamp; replacing a repeated cave-detail tile used as terrain; and quoting
comma-containing YAML conditions after the real loader rejected two NPC spawn
events. The puzzle's incorrect-order behaviour was simplified to a safe no-op
to avoid a held-input race.

The first external playtest added a fifth material repair: a tutorial wild
battle incorrectly relied on trainer-only battle history and retriggered on
the bridge. It was replaced by an explicit persistent completion flag in the
same ordered encounter event, and the validator now rejects that unsupported
condition pattern.

The second external playtest added a sixth material repair: Ashenbell's entry
touch event chained four modal dialogue states and delayed its state producer
until the end. The repaired arrival records progression first, uses one concise
prompt, and distributes the disagreement across the characters' existing
player-initiated conversations. Tests and validation now reject chained modal
dialogue on touch events.

Follow-up playtesting showed that even the replacement single entrance prompt
could remain modal. The arrival now contains no automatic dialogue: it records
investigation state and returns control immediately, while Mara, Iven and Nera
carry the scene through nearby player-initiated conversations. This was a
second revision of the same sixth repair, not a new content feature.

The next playtest entered Ashenbell without a prompt but still could not move.
The destination and neighboring cells are statically walkable and the arrival
event is synchronous, leaving runtime transition/control release as the leading
unverified cause. This open blocker demonstrates that the preceding repair was
symptom-driven and that automated acceptance lacked a real-client control-state
oracle.

All content and repair decisions were agent-authored in this run. No human map
or dialogue polish pass and no completed human playtest response has yet been
applied, so production autonomy beyond mechanical completion is unproven.

## 6. Did the result contain substantial playable content rather than empty maps?

The source contains substantial inspectable content, but the build does not yet
meet the requirement for substantial *playable* content because a real player
is blocked at the second major area. Every
major outdoor map has several authored battles, revelations, quest updates,
decisions, rewards or state changes in addition to random encounters. Every
declared detour pays off with evidence, an item, a battle, a side-quest subject
or the shortcut. The density report exposes those beats map by map and avoids
an aggregate quality score.

Most downstream content has therefore not been reached in external testing.
The 60–90-minute target is a design target, not a measured result, and current
evidence cannot distinguish its pacing quality from inaccessible authored data.

## 7. What must be solved before attempting a 3–5-hour alpha?

The next experiment should isolate human-perceived pacing and production
fidelity, not add another region. Run several fresh Low Bell playtests and
compare observed completion time, goal-loss points, empty stretches, battle
cadence, character recall and optional-quest uptake against the beat ledger.
Use those observations to determine whether the bottleneck is objective UX,
spatial composition, encounter balance, dialogue, or missing creature/world
presentation.

Before any longer alpha, resolve and trace the map-transition movement lock,
add a real-client golden-path harness or required observed checkpoint protocol,
and make runtime control-state assertions part of acceptance. The pipeline also
needs full manual save-menu/reload
exercise, automated event-script parsing as a standard compiler gate, better
generic multi-tile/autotile composition, and a legal strategy for distinct
overworld creature representation. Expanding playtime before those questions
are answered would multiply uncertainty rather than test production scale.
