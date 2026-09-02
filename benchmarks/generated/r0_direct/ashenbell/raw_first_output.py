"""Verbatim direct low-level response for the Ashenbell R0 condition."""

from __future__ import annotations

import xml.etree.ElementTree as ET
from pathlib import Path

import yaml

HERE = Path(__file__).resolve().parent
OUT = HERE / "raw_output"
TILE = 16
TILESET = "../../../../../../mods/tuxemon/gfx/tilesets/prototyping_outdoor.tsx"
HOUSE = (
    (850, 851, 852, 853),
    (882, 883, 884, 885),
    (914, 915, 916, 917),
    (946, 947, 948, 949),
    (978, 979, 980, 981),
)


def blank(width: int, height: int, tile: int = 0) -> list[list[int]]:
    return [[tile for _ in range(width)] for _ in range(height)]


def line(a: tuple[int, int], b: tuple[int, int]):
    x0, y0 = a
    x1, y1 = b
    dx, sx = abs(x1 - x0), 1 if x0 < x1 else -1
    dy, sy = -abs(y1 - y0), 1 if y0 < y1 else -1
    error = dx + dy
    while True:
        yield x0, y0
        if (x0, y0) == (x1, y1):
            return
        twice = 2 * error
        if twice >= dy:
            error += dy
            x0 += sx
        if twice <= dx:
            error += dx
            y0 += sy


def paint_path(
    data: dict, points: list[tuple[int, int]], width: int = 3
) -> None:
    radius = 1 if width == 3 else 0
    for start, end in zip(points, points[1:]):
        for cx, cy in line(start, end):
            for oy in range(-radius, radius + 1):
                for ox in range(-radius, radius + 1):
                    x, y = cx + ox, cy + oy
                    if 0 <= x < data["width"] and 0 <= y < data["height"]:
                        data["layers"]["Terrain"][y][x] = 193
                        data["blocked"].discard((x, y))


def tree(data: dict, x: int, y: int) -> None:
    if y < 1 or data["layers"]["Terrain"][y][x] == 193:
        return
    data["layers"]["Objects"][y][x] = 47
    data["layers"]["Above Player"][y - 1][x] = 15
    data["blocked"].add((x, y))


def prop(data: dict, x: int, y: int, tile: int, block: bool = True) -> None:
    data["layers"]["Objects"][y][x] = tile
    if block:
        data["blocked"].add((x, y))


def sign(data: dict, x: int, y: int) -> None:
    data["layers"]["Above Player"][y - 2][x] = 306
    data["layers"]["Above Player"][y - 1][x] = 338
    prop(data, x, y, 370)


def house(data: dict, x: int, y: int) -> None:
    for oy, row in enumerate(HOUSE):
        for ox, tile in enumerate(row):
            target_y = y - 4 + oy
            layer = "Above Player" if oy < 4 else "Objects"
            data["layers"][layer][target_y][x + ox] = tile
            data["blocked"].add((x + ox, target_y))


def event(
    name: str,
    x: int,
    y: int,
    properties: list[tuple[str, str]],
    width: int = 1,
    height: int = 1,
) -> dict:
    return {
        "name": name,
        "x": x,
        "y": y,
        "width": width,
        "height": height,
        "properties": properties,
    }


def warp(
    name: str, x: int, y: int, facing: str, target_map: str, tx: int, ty: int
) -> dict:
    return event(
        name,
        x,
        y,
        [
            (
                "act10",
                f"transition_teleport player,{target_map}.tmx,{tx},{ty},0.3",
            ),
            ("act20", f"char_face player,{facing}"),
            ("cond10", "is char_at player"),
            ("cond20", f"is char_facing player,{facing}"),
        ],
    )


def interaction(
    name: str,
    x: int,
    y: int,
    actions: list[str],
    conditions: list[str] | None = None,
) -> dict:
    props = [(f"act{index}", value) for index, value in enumerate(actions, 1)]
    props.extend(
        (f"cond{index + 20}", value)
        for index, value in enumerate(conditions or [], 1)
    )
    props.extend(
        [
            ("cond10", "is char_facing_tile player"),
            ("cond20", "is button_pressed INTERACT"),
        ]
    )
    return event(name, x, y, props)


def npc_events(slug: str, x: int, y: int) -> list[dict]:
    return [
        event(
            f"Create {slug}",
            x,
            y,
            [
                ("act1", f"create_npc {slug},{x},{y}"),
                ("cond1", f"not char_exists {slug}"),
            ],
        ),
        event(
            f"Talk {slug}",
            x,
            y,
            [
                ("act1", f"char_talk {slug},pre_battle"),
                ("behav1", f"talk {slug}"),
            ],
        ),
    ]


def base_map(map_id: str, width: int, height: int, ground: int) -> dict:
    layers = {
        "Ground": blank(width, height, ground),
        "Terrain": blank(width, height),
        "Objects": blank(width, height),
        "Above Player": blank(width, height),
    }
    return {
        "id": map_id,
        "width": width,
        "height": height,
        "layers": layers,
        "blocked": set(),
        "events": [],
    }


def forest_boundary(data: dict, depth: int) -> None:
    for y in range(1, data["height"]):
        for x in range(data["width"]):
            edge = min(x, y, data["width"] - 1 - x, data["height"] - 1 - y)
            if edge < depth and (x * 7 + y * 11) % 5 != 0:
                tree(data, x, y)


def south_route() -> dict:
    data = base_map("r0_south_route", 36, 34, 36)
    forest_boundary(data, 4)
    paint_path(
        data,
        [
            (18, 33),
            (16, 29),
            (20, 25),
            (17, 21),
            (18, 16),
            (13, 11),
            (17, 6),
            (18, 0),
        ],
    )
    paint_path(data, [(20, 25), (28, 26), (30, 21), (24, 19)], 1)
    for y in range(15, 18):
        for x in range(36):
            data["layers"]["Terrain"][y][x] = 45
            data["blocked"].add((x, y))
    for x in range(16, 21):
        for y, tile in ((15, 562), (16, 594), (17, 626)):
            data["layers"]["Terrain"][y][x] = tile
            data["blocked"].discard((x, y))
    for y in range(20, 28):
        for x in range(26, 34):
            if (x + y) % 3:
                data["layers"]["Ground"][y][x] = 36 if (x + y) % 5 else 34
    prop(data, 12, 7, 50)
    prop(data, 23, 7, 50)
    sign(data, 25, 29)
    data["events"].append(
        warp("r0_south_to_village", 18, 0, "up", "r0_ashenbell", 17, 28)
    )
    data["events"].extend(npc_events("r0_south_shepherd", 18, 27))
    data["events"].append(
        event(
            "r0_south_encounters",
            26,
            20,
            [("act1", "random_encounter r0_south_ecology,9")],
            8,
            8,
        )
    )
    data["events"].append(
        interaction(
            "r0_read_south_marker",
            25,
            29,
            [
                "translated_dialog The marker shows Split Crown above a bell, then ASHENBELL.",
                "set_variable r0_south_marker:read",
            ],
            ["not variable_set r0_south_marker:read"],
        )
    )
    data["events"].append(
        event(
            "Give R0 starter",
            0,
            0,
            [
                ("act1", "add_monster cardiling,7"),
                ("act2", "set_variable ashenbell_r0_starter:yes"),
                ("cond1", "not variable_set ashenbell_r0_starter:yes"),
            ],
        )
    )
    return data


def village() -> dict:
    data = base_map("r0_ashenbell", 34, 30, 33)
    forest_boundary(data, 2)
    paint_path(
        data,
        [(17, 29), (17, 25), (13, 21), (16, 16), (20, 12), (23, 7), (22, 0)],
    )
    paint_path(data, [(16, 16), (11, 17), (7, 20), (7, 26)], 1)
    paint_path(data, [(20, 12), (26, 11), (32, 10)], 1)
    for x in range(3, 13):
        for y in (20, 27):
            if x != 7:
                prop(data, x, y, 210)
    for y in range(21, 27):
        for x in (3, 12):
            if not (x == 12 and y == 23):
                prop(data, x, y, 242)
    for y in range(21, 27):
        for x in range(4, 12):
            if (x * 2 + y) % 3:
                data["layers"]["Ground"][y][x] = 36
    house(data, 4, 13)
    house(data, 9, 13)
    house(data, 25, 18)
    house(data, 26, 27)
    prop(data, 14, 14, 50)
    prop(data, 19, 14, 50)
    sign(data, 20, 16)
    data["events"].extend(
        [
            warp(
                "r0_village_to_south", 17, 29, "down", "r0_south_route", 18, 1
            ),
            warp(
                "r0_village_to_pass", 22, 0, "up", "r0_highland_pass", 14, 34
            ),
        ]
    )
    data["events"].extend(npc_events("r0_bell_keeper", 18, 18))
    data["events"].extend(npc_events("r0_gardener", 8, 24))
    data["events"].append(
        event(
            "r0_village_encounters",
            4,
            21,
            [("act1", "random_encounter r0_village_ecology,6")],
            8,
            6,
        )
    )
    data["events"].append(
        interaction(
            "r0_read_bell_plinth",
            20,
            16,
            [
                "translated_dialog Three warning dates end with THE QUARRY SLIDE; CHAIN RETIRED.",
                "set_variable r0_bell_history:read",
            ],
            ["not variable_set r0_bell_history:read"],
        )
    )
    data["events"].append(
        interaction(
            "r0_village_shortcut_locked",
            32,
            10,
            [
                "translated_dialog The ridge stair counterweight is down; its cable climbs toward the quarry."
            ],
            ["not variable_set r0_shortcut:open"],
        )
    )
    data["events"].append(
        interaction(
            "r0_village_shortcut_open",
            32,
            10,
            [
                "translated_dialog The raised weight opens the ridge stair.",
                "transition_teleport player,r0_highland_pass.tmx,5,30,0.3",
                "char_face player,right",
            ],
            ["variable_set r0_shortcut:open"],
        )
    )
    return data


def highland_pass() -> dict:
    data = base_map("r0_highland_pass", 36, 36, 33)
    paint_path(
        data,
        [
            (14, 35),
            (12, 31),
            (17, 28),
            (15, 23),
            (22, 20),
            (19, 14),
            (24, 9),
            (18, 0),
        ],
    )
    paint_path(data, [(15, 23), (24, 24), (30, 20), (35, 22)], 1)
    paint_path(data, [(12, 31), (8, 32), (4, 30)], 1)
    for x, y, tile in [
        (4, 7, 50),
        (9, 10, 54),
        (14, 12, 50),
        (16, 15, 50),
        (23, 14, 50),
        (27, 11, 54),
        (30, 6, 50),
        (29, 28, 54),
        (25, 31, 50),
        (7, 34, 54),
        (5, 20, 50),
        (31, 17, 50),
        (10, 25, 54),
        (21, 26, 54),
    ]:
        prop(data, x, y, tile)
    prop(data, 16, 14, 50)
    prop(data, 23, 14, 50)
    sign(data, 29, 19)
    for bounds in [(19, 26, 10, 7), (10, 3, 14, 8)]:
        x0, y0, width, height = bounds
        for y in range(y0, y0 + height):
            for x in range(x0, x0 + width):
                if (x + 2 * y) % 5 == 0:
                    data["layers"]["Ground"][y][x] = 36
    data["events"].extend(
        [
            warp("r0_pass_to_village", 14, 35, "down", "r0_ashenbell", 22, 1),
            warp(
                "r0_pass_to_quarry",
                35,
                22,
                "right",
                "r0_old_bell_quarry",
                1,
                14,
            ),
        ]
    )
    data["events"].extend(npc_events("r0_pass_surveyor", 24, 21))
    data["events"].append(
        event(
            "r0_pass_south_encounters",
            19,
            26,
            [("act1", "random_encounter r0_pass_ecology,8")],
            10,
            7,
        )
    )
    data["events"].append(
        event(
            "r0_pass_north_encounters",
            10,
            3,
            [("act1", "random_encounter r0_pass_ecology,8")],
            14,
            8,
        )
    )
    data["events"].append(
        interaction(
            "r0_pass_echo",
            19,
            14,
            [
                "translated_dialog The three warning cuts match Ashenbell's plinth; the west stone carries a lower answering tone."
            ],
            ["variable_set r0_bell_history:read"],
        )
    )
    data["events"].append(
        interaction(
            "r0_pass_shortcut_locked",
            4,
            30,
            [
                "translated_dialog A lowered counterweight blocks the old ridge stair."
            ],
            ["not variable_set r0_shortcut:open"],
        )
    )
    data["events"].append(
        interaction(
            "r0_pass_shortcut_open",
            4,
            30,
            [
                "translated_dialog The quarry hoist holds the stair open.",
                "transition_teleport player,r0_ashenbell.tmx,31,10,0.3",
                "char_face player,left",
            ],
            ["variable_set r0_shortcut:open"],
        )
    )
    return data


def quarry() -> dict:
    data = base_map("r0_old_bell_quarry", 30, 28, 36)
    paint_path(
        data, [(0, 14), (6, 14), (8, 10), (15, 9), (20, 12), (24, 8), (27, 8)]
    )
    paint_path(
        data, [(8, 10), (7, 19), (14, 23), (22, 21), (25, 15), (24, 8)], 1
    )
    rocks = [
        (3, 4),
        (6, 5),
        (10, 4),
        (14, 5),
        (18, 4),
        (22, 4),
        (26, 5),
        (4, 23),
        (8, 24),
        (19, 24),
        (25, 23),
        (28, 19),
        (2, 18),
        (12, 16),
        (17, 7),
        (21, 8),
        (23, 11),
        (19, 15),
        (16, 13),
        (27, 12),
        (11, 21),
    ]
    for index, (x, y) in enumerate(rocks):
        prop(data, x, y, 50 if index % 3 else 54)
    sign(data, 27, 5)
    for y in range(16, 25):
        for x in range(6, 18):
            if (x + y) % 3:
                data["layers"]["Ground"][y][x] = 36 if (x + y) % 4 else 34
    data["events"].append(
        warp("r0_quarry_to_pass", 0, 14, "left", "r0_highland_pass", 34, 22)
    )
    data["events"].extend(npc_events("r0_quarry_prospector", 18, 16))
    data["events"].append(
        event(
            "r0_quarry_damp_encounters",
            6,
            16,
            [("act1", "random_encounter r0_quarry_ecology,8")],
            12,
            9,
        )
    )
    data["events"].append(
        event(
            "r0_quarry_shaft_encounters",
            16,
            3,
            [("act1", "random_encounter r0_quarry_ecology,8")],
            12,
            8,
        )
    )
    data["events"].append(
        interaction(
            "r0_quarry_evidence",
            20,
            12,
            [
                "translated_dialog Runoff pulses through cracked bell-stone while a buried iron strap vibrates against it."
            ],
        )
    )
    data["events"].append(
        interaction(
            "r0_raise_hoist",
            25,
            8,
            [
                "translated_dialog You brace the hoist; the ridge-stair counterweight rises below.",
                "set_variable r0_shortcut:open",
            ],
            ["not variable_set r0_shortcut:open"],
        )
    )
    data["events"].append(
        interaction(
            "r0_hoist_raised",
            25,
            8,
            [
                "translated_dialog The hoist remains braced and the shortcut remains open."
            ],
            ["variable_set r0_shortcut:open"],
        )
    )
    data["events"].append(
        interaction(
            "r0_quarry_cache",
            14,
            23,
            [
                "translated_dialog Survey notes beside a potion connect west wind, runoff, wet stone, and buried iron.",
                "add_item potion",
                "set_variable r0_quarry_cache:found",
            ],
            ["not variable_set r0_quarry_cache:found"],
        )
    )
    return data


def properties(parent: ET.Element, values: list[tuple[str, str]]) -> None:
    node = ET.SubElement(parent, "properties")
    for name, value in values:
        ET.SubElement(node, "property", {"name": name, "value": value})


def write_tmx(data: dict) -> None:
    root = ET.Element(
        "map",
        {
            "version": "1.10",
            "tiledversion": "1.10.2",
            "orientation": "orthogonal",
            "renderorder": "right-down",
            "width": str(data["width"]),
            "height": str(data["height"]),
            "tilewidth": "16",
            "tileheight": "16",
            "infinite": "0",
            "nextlayerid": "7",
            "nextobjectid": "5000",
        },
    )
    ET.SubElement(root, "tileset", {"firstgid": "1", "source": TILESET})
    for layer_id, (name, grid) in enumerate(data["layers"].items(), 1):
        layer = ET.SubElement(
            root,
            "layer",
            {
                "id": str(layer_id),
                "name": name,
                "width": str(data["width"]),
                "height": str(data["height"]),
            },
        )
        encoded = ",\n".join(
            ",".join(str(tile + 1 if tile else 0) for tile in row)
            for row in grid
        )
        ET.SubElement(layer, "data", {"encoding": "csv"}).text = (
            "\n" + encoded + "\n"
        )
    collisions = ET.SubElement(
        root,
        "objectgroup",
        {"id": "5", "name": "Collisions", "color": "#ff0000"},
    )
    next_id = 1
    for x, y in sorted(data["blocked"], key=lambda cell: (cell[1], cell[0])):
        ET.SubElement(
            collisions,
            "object",
            {
                "id": str(next_id),
                "type": "collision",
                "x": str(x * TILE),
                "y": str(y * TILE),
                "width": str(TILE),
                "height": str(TILE),
            },
        )
        next_id += 1
    events = ET.SubElement(
        root, "objectgroup", {"id": "6", "name": "Events", "color": "#ffff00"}
    )
    for item in data["events"]:
        obj = ET.SubElement(
            events,
            "object",
            {
                "id": str(next_id),
                "name": item["name"],
                "type": "event",
                "x": str(item["x"] * TILE),
                "y": str(item["y"] * TILE),
                "width": str(item["width"] * TILE),
                "height": str(item["height"] * TILE),
            },
        )
        properties(obj, item["properties"])
        next_id += 1
    environment = ET.SubElement(
        events,
        "object",
        {
            "id": str(next_id),
            "name": "Environment",
            "type": "event",
            "x": "0",
            "y": "0",
            "width": "16",
            "height": "16",
        },
    )
    properties(
        environment,
        [
            ("act1", "set_environment grass"),
            ("cond1", "not environment_is grass"),
        ],
    )
    ET.indent(root, space=" ")
    output = OUT / "maps" / f"{data['id']}.tmx"
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(
        '<?xml version="1.0" encoding="UTF-8"?>\n'
        + ET.tostring(root, encoding="unicode")
        + "\n",
        encoding="utf-8",
        newline="\n",
    )


def write_database() -> None:
    npcs = {
        "r0_south_shepherd": (
            "botanist",
            "The lower night tone follows Split Crown's west face when fog presses low. Grandmother's quarry warnings kept that rhythm, but sounded brighter.",
        ),
        "r0_bell_keeper": (
            "scientist",
            "Quarry-stone bells with iron tongues warned three valleys until the slide. Nobody has operated the chain since, whatever sounds at night.",
        ),
        "r0_gardener": (
            "miner_green",
            "Squabbit take dry seed; Elofly only settle here when the ridge wind drops.",
        ),
        "r0_pass_surveyor": (
            "knight",
            "The old warning stones carried across valleys. West wind and quarry runoff arrive with the new tone; weather may be playing abandoned work.",
        ),
        "r0_quarry_prospector": (
            "miner_green",
            "Wet cracked stone and a buried iron strap answer one another here. That can sound without anybody ringing a bell.",
        ),
    }
    records = []
    for slug, (sprite, _) in npcs.items():
        records.append(
            {
                "slug": slug,
                "speech": {
                    "profile": {
                        "default": {
                            "pre_battle": f"{slug}_dialog",
                            "post_battle_win": None,
                            "post_battle_lose": None,
                            "post_battle_draw": None,
                        }
                    }
                },
                "combat": {},
                "audio": {},
                "template": {
                    "sprite_name": sprite,
                    "combat_sheet": "miner"
                    if sprite.startswith("miner")
                    else sprite,
                    "slug": "miner" if sprite.startswith("miner") else sprite,
                },
            }
        )
    npc_dir = OUT / "db" / "npc"
    npc_dir.mkdir(parents=True, exist_ok=True)
    (npc_dir / "ashenbell_r0_npcs.yaml").write_text(
        yaml.safe_dump(records, sort_keys=False), encoding="utf-8"
    )
    tables = {
        "r0_south_ecology": [
            ("shybulb", 5, 4, 6),
            ("squabbit", 3, 5, 7),
            ("elofly", 1, 5, 6),
        ],
        "r0_village_ecology": [("squabbit", 5, 5, 7), ("elofly", 3, 5, 7)],
        "r0_pass_ecology": [("elofly", 5, 6, 8), ("squabbit", 2, 6, 8)],
        "r0_quarry_ecology": [
            ("elofly", 4, 6, 8),
            ("shybulb", 3, 5, 7),
            ("squabbit", 1, 6, 7),
        ],
    }
    encounter_dir = OUT / "db" / "encounter"
    encounter_dir.mkdir(parents=True, exist_ok=True)
    for slug, entries in tables.items():
        record = {
            "monsters": [
                {
                    "encounter_rate": rate,
                    "exp_req_mod": 3,
                    "held_items": [],
                    "level_range": [low, high],
                    "monster": monster,
                    "variables": [],
                }
                for monster, rate, low, high in entries
            ],
            "slug": slug,
        }
        (encounter_dir / f"{slug}.yaml").write_text(
            yaml.safe_dump(record, sort_keys=False), encoding="utf-8"
        )
    locale = OUT / "l18n" / "en_US" / "LC_MESSAGES"
    locale.mkdir(parents=True, exist_ok=True)
    body = 'msgid ""\nmsgstr ""\n"Language: en_US\\n"\n"Content-Type: text/plain; charset=UTF-8\\n"\n\n'
    for slug, (_, dialogue) in sorted(npcs.items()):
        body += f'msgid "{slug}_dialog"\nmsgstr "{dialogue}"\n\n'
    body += (
        'msgid "world_synthesis_campaign"\nmsgstr "The Ashenbell Highlands"\n'
    )
    (locale / "ashenbell_r0.po").write_text(
        body, encoding="utf-8", newline="\n"
    )


def main() -> None:
    for data in (south_route(), village(), highland_pass(), quarry()):
        write_tmx(data)
    write_database()


if __name__ == "__main__":
    main()
