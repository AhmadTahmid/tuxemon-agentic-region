# Event Grammar

Tuxemon events are ordered commands attached to Tiled objects. Numeric suffixes control order, so generators use zero-padded keys such as `cond010`, `act010`, and `act020`.

## Core patterns

### Map exit

```text
cond010 = is char_at player
cond020 = is char_facing player,up
act010  = transition_teleport player,next_map.tmx,12,28,0.3
act020  = char_face player,up
```

The destination map and coordinates must exist and must not be blocked. A paired return warp is required for milestone maps.

### Passive NPC

```text
init:  act010 = create_npc ws_route_botanist,10,14
event: cond010 = is char_at player
       behav010 = talk ws_route_botanist
       act010 = char_talk ws_route_botanist,greeting
```

The NPC slug must resolve in `db/npc`, its sprite and combat sheet must exist, and its tile must be reachable.

### Trainer

```text
act010 = char_talk ws_route_scout,pre_battle
act020 = start_battle player,ws_route_scout
act030 = char_talk ws_route_scout,post_battle_lose
cond010 = not battle_outcome player,won,ws_route_scout
behav010 = talk ws_route_scout
```

The custom NPC record owns its party. Once `battle_outcome ... won` becomes true, a separate post-battle talk event can provide persistent dialogue.

### Wild encounter area

```text
cond010 = is char_at player
cond020 = is char_moved player
act010 = random_encounter ws_glasswind_meadow,12
act020 = play_map_animation grass,0.1,noloop,player
```

The object may cover several tiles. `12` scales the table probability; it is not a monster level.

### Secret reward

```text
cond010 = is char_at player
cond020 = is button_pressed K_RETURN
cond030 = not variable_set ws_route_cache_found:yes
act010 = translated_dialog You found a weathered field kit.
act020 = add_item potion,2
act030 = set_variable ws_route_cache_found:yes
```

The reward flag prevents duplication. A second event conditioned on the flag can provide an empty-cache response.

### Quest/flag progression

`set_variable key:value` records state. Common checks are `variable_set key:value`, `variable_is`, `has_item`, `battle_outcome`, `char_exists`, and `char_defeated`. Validators should model mutually exclusive flag states and verify that every required transition has at least one reachable triggering event.

## Observed conventions

Across 263 maps, the most frequent actions are character facing, dialogue, NPC creation, monster addition, teleportation, and control locking. The dominant conditions are player location, facing, NPC existence, battle outcome, movement, and button input. This supports a compact authoring grammar rather than exposing every engine action in the first WorldSpec.

## Generator restrictions

- Never emit an unknown action/condition or unresolved slug.
- Event boxes must be positive, grid-aligned, and within map bounds.
- Interaction events need a reachable adjacent player cell.
- Reward events need a persistence flag.
- Trainer events need both pre- and post-battle behavior.
- Cinematic control locks must always have a later unlock.
- Automatic repair is reported; it is never silent.
