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

## Reviewed area palettes

Every runtime tile comes from an existing repository tileset. No artwork was
created or imported. The semantic palettes deliberately reuse compatible
families while assigning different material vocabularies:

- South Approach uses `core_outdoor`: damp green ground, water, tall conifers,
  flowers, shrubs and narrow earth paths.
- Ashenbell uses `core_city_and_country`: bright maintained grass, timber
  houses, service paths, garden planting and the existing fountain/plinth set
  as its civic focal point.
- Highland Pass uses a second semantic view of `core_outdoor`: sparse green
  margins, a broad exposed-earth shelf and repeated pale ridge stones.
- Both quarry maps use a quarry-specific semantic view of `core_outdoor`:
  worked timber track, runoff channels, rock boundaries, metal fittings and a
  darker resonant chamber floor.
- Mara's Archive and Tovin's Workshop use `core_set pieces`: wood floor,
  masonry walls and distinct record/hoist props.

The labelled atlas windows used to inspect legal candidates are preserved in
`artifacts/production_slice/low_bell/asset_review/`. Full and debug renders of
all seven maps are preserved in the sibling `renders/` directory. These are
review artifacts generated from the source atlases, not replacement assets.

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

## Milestone 4 coverage

All seven maps now compile with reviewed, existing art rather than the
benchmark prototype palette. Ashenbell has four compact buildings, an actual
civic focal point, an orthogonal road hierarchy and planted productive edge.
The South Approach is framed by layered woodland and water; the Pass opens
into exposed earth and ridge stones; and the quarry changes to worked timber,
runoff, rubble, fittings and a dark resonant bay. Static full/debug rendering
is a reusable deterministic command: `python -m
world_synthesis.production_slice render low_bell`.
