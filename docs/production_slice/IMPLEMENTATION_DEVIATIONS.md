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
