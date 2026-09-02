# Engine capability audit

Audit scope: upstream Tuxemon in this repository at design lock. A capability
is marked **source-confirmed** when its production code and an existing usage
were inspected. It remains **client-unverified** until exercised in the real
Low Bell build.

| Need | Existing mechanism | Audit result | Production decision |
|---|---|---|---|
| Three-way starter choice | `choice_monster` stores a selected monster slug; `add_monster` can resolve a slug from that variable | Source-confirmed; existing `manhattan_beach.tmx` demonstrates three choices | Use Anoleaf, Flounce and Rockitten at level 5 |
| Tutorial/trainer battle | `start_battle player,<npc>` queues the real combat state and records outcome | Source-confirmed | Use a trainer NPC for Rook and real scripted battles elsewhere |
| Scripted catchable wild battle | `wild_encounter` creates `CombatType.MONSTER`; ordinary `tuxeball` has the capture effect | Source-confirmed | Give capture devices after the tutorial, then expose an optional catchable pocket |
| Quest state | Persistent game variables, mission models, `set_mission`, `check_mission` | Source-confirmed | Use mission records for journal visibility and variables as event-level facts |
| Conditional dialogue | Event conditions `variable_set`, `variable_is`, battle outcome and mission checks | Source-confirmed | Compile mutually exclusive talk events at stable NPC anchors |
| Item rewards | `add_item` with existing item database records | Source-confirmed | Use potions, Tuxeballs and one Bivouac; validate every slug |
| NPC state changes | `create_npc`, `remove_npc`, conditional events and state-aware NPC profiles | Source-confirmed | Reposition/replace logical NPC profiles only where staging requires it |
| Persistent variables | NPC save state serializes and restores `game_variables` | Source-confirmed | Namespace every flag `low_bell_*` |
| Battle persistence | NPC save state serializes battle history; `battle_outcome` queries it | Source-confirmed | Victory flags are explicit; battle history provides secondary validation |
| Optional shortcut | Conditional `transition_teleport` and persistent variables | Source-confirmed | Unlock a bidirectional hoist link while retaining the ordinary path |
| Puzzle switches | Conditional interactions plus `set_variable`/`clear_variable` | Source-confirmed | Three observed-order controls; wrong order resets only puzzle progress |
| Save/reload | `SaveManager`; NPC save contains variables, battles, missions, party and inventory | Source-confirmed | Add round-trip state tests and exercise a real save in Milestone 5 |
| Music/SFX | `play_music` and `play_sound`; existing wind, stone, metal and bell audio | Source-confirmed | Select existing tracks/SFX after in-client volume review |
| Ending transition | Dialogue, state mutation, reward, save, teleport and `quit_world` all exist | Source-confirmed | End in resolved Ashenbell with `low_bell_episode_complete`; do not force `quit_world` before post-story exploration |

## Starter selection

The selection is cleanly data-driven and does not require engine work.

| Monster | Existing type and early kit | Early role | Fit |
|---|---|---|---|
| Anoleaf | Wood; Leaf Stab, Feint, Assault | Quick utility/pressure | Naturalist-friendly sheltered-route choice |
| Flounce | Fire; Fire Claw, Wall Fire, Canine | Direct offense with protection | Strong contrast against damp terrain |
| Rockitten | Earth; Ram, Boulder, Mudslide | Sturdy control | Upland/quarry thematic choice |

All are basic-stage creatures with catch rate 100 and complete battle sprites,
data and sounds. Choice consequence is mechanical role and flavour dialogue;
the critical path cannot depend on a particular type.

## Climax creature

**Jemuar** is selected provisionally and locked unless real-client battle
testing exposes a mechanical problem. It is an existing stage-two Earth/Cosmic
mountain creature, 160 cm and 150 kg, with rock/gemstone tags and a roar. Its
large feline silhouette can plausibly nest in a dry quarry chamber; its mass
and movement can load the fractured resonant assembly. It reads as territorial
rather than malicious. The encounter uses a real battle and is not catchable
if threat-battle support is used; exact level and moves are tuned only through
playtesting. Its visual design was inspected from the repository sprite sheet.

## Planned ecology

The episode draws from 10 existing species/families, with starters excluded
from random encounter counts when needed to preserve choice identity:

- sheltered South Approach: Shybulb, Budaye, Elofly, Caper;
- cultivated edge: Caper, Squabbit and occasional Budaye;
- exposed pass: Rockitten, Flacono, Baddrscratch, Corvix;
- quarry: Slichen, Rockat and the unique Jemuar climax.

Final encounter weights and levels will be recorded in content and validated
against terrain, type, stage and sprite availability.

## Generic gaps identified at design lock

The existing benchmark compiler does not yet model production missions,
state-dependent dialogue matrices, scripted battle sequences, area-specific
multi-tileset palettes or production acceptance graphs. These are
**WorldSpec/compiler authoring gaps**, not missing Tuxemon runtime mechanics.
Milestone 2 may add the smallest reusable production schema/compiler layer.
It must describe arbitrary episodes and may not branch on Low Bell map IDs.

No upstream engine change is authorized by this audit. Every capability still
requires real-client exercise before the final report can call it working.

