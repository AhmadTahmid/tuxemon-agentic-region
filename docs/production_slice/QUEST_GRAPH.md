# Quest graph

## Persistent episode states

The authoritative phase variable is `low_bell_story` with values `intro`,
`investigation`, `quarry_discovered` and `resolved`. `low_bell_episode_complete`
is set only by the return-to-town ending. All other flags are facts or local
quest progress; none substitutes for a story phase.

```text
fresh start
  -> starter chosen
  -> tutorial encounter cleared
  -> arrive Ashenbell [intro]
  -> accept Mara/Nera investigation [investigation]
  -> defeat Rook + hear pass tone
  -> identify disturbed drainage [quarry_discovered]
  -> solve controls + defeat Jemuar + damp assembly [resolved]
  -> return to Ashenbell + closing conversations
  -> episode complete
```

The boss path requires no side-quest flag. The ordinary South–Village–Pass–
Quarry route remains available after the hoist shortcut opens.

## Main quest: The Low Bell

| Step | Producer | Required facts | Produces |
|---|---|---|---|
| First resonance | South arrival trigger | none | `low_bell_tone_seen` |
| New handler | Nera interaction | tone seen, no starter | `low_bell_starter_chosen` |
| Clear the path | tutorial encounter resolves by win, capture or retreat | starter chosen | `low_bell_tutorial_cleared`, capture kit |
| Hear the accounts | civic plinth scene | tutorial cleared | `low_bell_story:investigation` |
| Warden's test | Rook victory | investigation | `low_bell_rook_defeated` |
| Trace the tone | pass resonance interaction | Rook defeated | `low_bell_pass_trace` |
| Find the disturbance | quarry survey evidence | pass trace | `low_bell_story:quarry_discovered` |
| Stabilize the hoist | three-control puzzle | quarry discovered | `low_bell_puzzle_solved`, `low_bell_shortcut_unlocked` |
| Calm the nest | Jemuar victory | puzzle solved | `low_bell_boss_defeated` |
| Dampen the assembly | post-battle control | boss defeated | `low_bell_story:resolved` |
| Report home | Ashenbell plinth resolution | resolved | main reward, `low_bell_episode_complete` |

The control interaction, not the battle alone, resolves the tone. Losing a
mandatory battle leaves its victory flag unset and allows a retry.

## Side quest: Jori's Squabbit

```text
not discussed -> accepted -> found at quarry rim -> returned
                     \-> may be found before acceptance -> returned later
```

Flags: `low_bell_sq_squabbit_accepted`, `low_bell_sq_squabbit_found`,
`low_bell_sq_squabbit_complete`. The quarry discovery and climax do not read
any of them. Reward: two existing `tuxeball_hearty` items. Jori has distinct
resolved dialogue for complete and incomplete outcomes.

## Side quest: Names of the Silent Shift

Mara requests three records. Each can be recovered before or after accepting:

1. a weathered shift token on the South Approach overlook;
2. a survey rubbing on the optional Highland Pass shelf;
3. a brass name strip in the quarry's collapsed side pocket.

Flags: `low_bell_sq_names_accepted`, `low_bell_name_south`,
`low_bell_name_pass`, `low_bell_name_quarry`, `low_bell_sq_names_complete`.
Completion requires all three and a return to Mara, then changes Mara, Tovin
and the memorial. Reward: one existing `bivouac`. No main-quest condition reads
these flags.

## Puzzle and shortcut

Tovin explains the safe physical order: **divert runoff, brace the cradle,
then release the hoist**. Labels and water/brace/hoist visuals repeat the clue
inside the lower works.

Controls advance `low_bell_puzzle_stage` from absent to `runoff` to `brace`;
the final control sets `low_bell_puzzle_solved`. An out-of-order control makes no state change,
so experimentation cannot lose progress or permanently block the puzzle.
Solving it opens the hoist and sets
`low_bell_shortcut_unlocked`. Bidirectional shortcut events require that flag;
the ordinary quarry entrance never does.
