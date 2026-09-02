# Content coverage

This is the design-lock inventory. Final status and evidence links will be
updated as implementation lands.

## Planned maps (7)

| Map | Approximate size | Function | Visual family |
|---|---:|---|---|
| South Approach | 34×46 | Opening, tutorial, capture, wooded ascent | Core outdoor/nature/water: damp green shelter |
| Ashenbell | 44×40 | Organized village hub and four story phases | Core outdoor/city/buildings/set pieces: paths, gardens, civic plinth |
| Mara's Archive | 16×12 | Bell records and names quest | Core indoor floors/walls/furniture |
| Tovin's Workshop | 16×12 | Hoist/drainage clues and character progression | Core indoor plus existing industrial/furniture set pieces |
| Highland Pass | 36×48 | Exposed route, trainers, ridge and quarry fork | Core outdoor/nature: sparse rock and cliff geometry |
| Old Bell Quarry Exterior | 34×36 | Survey evidence, Squabbit and optional pocket | Core outdoor/cave/set pieces: worked damaged stone |
| Quarry Lower Works | 38×40 | Small dungeon, puzzle, hoist, boss and resolution | Existing cave/factory/core set pieces in one reviewed family |

## Implemented logical NPCs (17)

| NPC | Declared function(s) |
|---|---|
| Nera | tutorial, main progression, ecology, ending consequence |
| Mara | main progression, historian conflict, names quest, reward |
| Tovin | character development, puzzle clue, resolution |
| Jori | side quest, personal stake, changed consequence |
| Iven | central conflict, concealed evidence, responsibility arc |
| Sela | geography, evidence, gameplay direction |
| Rook | trainer gate, route safety, local knowledge |
| Alda | productive-world texture, ecology evidence, post-state |
| Bren | material evidence, local texture, post-state |
| Caro | rumour contrast, inhabited-world texture, post-state |
| Pell | courier identity, outside-world ending hook |
| Ren | optional South battle, tutorial reinforcement, reward |
| Kesh | optional Pass battle, survey context, reward |
| Quarry Squabbit | represented side-quest subject and interaction |
| Garden Caper | represented displaced-creature encounter at productive edge |
| Rockat guard | represented territorial encounter at lower-works gate |
| Jemuar | represented climax creature in a real battle |

Repeated appearances of a logical character do not inflate this count.

## Planned combat and ecology

Seven authored combat beats: frightened Shybulb tutorial, Ren, displaced garden
encounter, Rook, Kesh, territorial Rockat, and the Jemuar climax. This is seven
including all optional/scripted beats, within the locked budget. Random wild
encounters are additional. Ten non-boss ecology candidates are reviewed in
the capability audit; final tables must remain area-specific.

## Area palettes

Palette review is constrained to existing repository assets:

- South Approach: `core_outdoor`, `core_outdoor_nature`,
  `core_outdoor_water`; dense canopy margins, wet ground and narrow openings.
- Ashenbell: the same core family plus `core_city_and_country`,
  `core_buildings` and `core_set pieces`; orthogonal service paths, clustered
  homes, garden rows and a central plinth.
- Highland Pass: `core_outdoor` and compatible nature/terrain rock forms;
  sparse planting, cliff bands, wind gaps and long sightlines.
- Quarry: compatible cave/worked-stone tiles with `factory` or core set pieces
  only after rendered review; machinery traces are accents, not a mismatched
  industrial map.
- Interiors: `core_indoor_floors`, `core_indoor_walls`, furniture and small
  function-specific set pieces.

Exact tile IDs will be recorded by the compiler palette catalogue and checked
through deterministic full-map renders before client launch.

## Milestone 2 coverage

The first playable golden path now compiles all seven declared maps. It
includes starter selection, a scripted tutorial encounter, capture devices and
wild zones, Ashenbell's introduction, state-dependent village dialogue,
Rook's real trainer party, Split Crown resonance, Iven's survey evidence, a
required return for Tovin's knowledge, the lower works, a real Jemuar battle,
a separate post-battle physical resolution, return-to-town closure, rewards
and an episode-complete ending hook.

## Milestone 3 coverage

Content completion is implemented. Jori's Squabbit can be found before or
after accepting the quest and never gates the main story. Names of the Silent
Shift has three independently collectable records and changes Mara and Tovin.
South, Pass and Quarry dead ends each combine evidence or encounter context
with a useful existing item. Ren, the garden Caper, Kesh and the Rockat gate
bring the authored combat total to seven. The labelled runoff–cradle–hoist
sequence unlocks a persistent bidirectional shortcut while leaving the
ordinary route open. Nine logical village/key characters have resolved-state
dialogue branches, including complete/incomplete side-quest reactions.
