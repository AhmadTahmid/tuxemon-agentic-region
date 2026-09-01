# Glasswind Generalization Audit

Audit baseline: commit `ac937da97`, before the Deep Forest benchmark. Glasswind
Causeway is fixture 0 and must retain its logical topology. Classification is
about implementation scope, not code quality.

## Compiler behavior inventory

| Behavior | Baseline classification | Evidence and disposition |
|---|---|---|
| Stable seed derived from world seed, map ID and revision | GENERAL_PRIMITIVE | Reusable unchanged. |
| Bresenham polyline rasterization with configurable width | GENERAL_PRIMITIVE | Reusable unchanged. |
| Bounds clipping during rasterization | GENERAL_PRIMITIVE | Reusable unchanged. |
| Semantic protected cells for paths, warps, NPCs and secrets | GENERAL_PRIMITIVE | Retain and extend to authored clearings/props. |
| Exact blocked-cell to rectangle merging | GENERAL_PRIMITIVE | Reusable unchanged. |
| Layered TMX CSV emission | GENERAL_PRIMITIVE | Reusable unchanged. |
| Tuxemon event emission for warps, encounters, NPCs and secrets | GENERAL_PRIMITIVE | Event grammar is general; starter injection is not. |
| Full-map grass base with two fixed variants | ARCHETYPE_PRIMITIVE | Suitable for current outdoor vocabulary, but baseline could not select forest-floor treatment. Add a small semantic base-terrain choice. |
| Forest-like boundary on every map, with fixed depth/probability | GLASSWIND_SPECIFIC | The compiler chose a boundary without MapSpec asking. Replace with explicit, configurable boundary intent. |
| Rectangular semantic zones | GENERAL_PRIMITIVE | Shape is limited but useful. Baseline only rendered meadow/encounter/secret zones. Add reusable forest density and safe-clearing semantics. |
| Tall-grass/flower scatter from tagged zones | ARCHETYPE_PRIMITIVE | Outdoor vegetation grammar; deterministic and content-driven. Retain. |
| Water painted from a rectangular `river` feature | ARCHETYPE_PRIMITIVE | Useful simple water primitive; rectangle-only geometry is a known limitation. |
| Bridge painting by grouping cells by X and choosing top/middle/bottom | GLASSWIND_SPECIFIC | Assumes a vertical crossing over a horizontal river. Deep Forest does not require a crossing, so retain and log rather than broadening this milestone. |
| River stones at global minimum/maximum river Y | GLASSWIND_SPECIFIC | Assumes one horizontal river. Retain for fixture 0 and record as an unsupported geography failure. |
| Fence perimeter generation | ARCHETYPE_PRIMITIVE | Mechanical translation is reusable. |
| Always remove two southwest fence cells | GLASSWIND_SPECIFIC | Planner must provide entrance cells. Generalize to explicit feature entrances. |
| Always place a three-tile sign at a fence's southwest side | GLASSWIND_SPECIFIC | Convert signs to explicit props; preserve Glasswind by authoring its sign. |
| Three fixed grove-tree offsets whenever landmark kind is `grove` | GLASSWIND_SPECIFIC | Compiler is choosing composition. Replace with explicit meaningful props plus semantic forest scatter. |
| Palette tile IDs | ARCHETYPE_PRIMITIVE | Frozen reviewed outdoor vocabulary for this benchmark. No asset work in this milestone. |
| `glasswind_causeway` starter special case | GLASSWIND_SPECIFIC | Replace with typed experiment metadata and generic startup event emission. |
| Fixed `glasswind_meadow` encounter table and monsters | GLASSWIND_SPECIFIC | Replace with typed encounter-table content; reuse only existing monsters. |
| `glasswind_npcs.yaml`, trainer response and translation domain names | GLASSWIND_SPECIFIC | Derive deterministic filenames/keys from experiment and NPC content. |
| Build output fixed to the experimental mod and shared maps directory | ARCHETYPE_PRIMITIVE | Appropriate for the isolated Tuxemon mod; make filenames generic so multiple benchmark specs coexist. |
| CLI manufactures Glasswind revision 1 in Python | GLASSWIND_SPECIFIC | Preserve legacy fixture command, but benchmark revision artifacts must be explicit content files. |
| Structural critic rewards presence/counts | UNKNOWN | Transparent and repeatable but not a visual or enjoyment measure. Rename report fields and keep separate from human evaluation. |

## Minimum pre-benchmark generalization

The compiler may change before Deep Forest variants are authored to add:

1. explicit base terrain and boundary specifications;
2. deterministic forest-zone density and safe clearings;
3. explicit significant prop placements;
4. configurable fence entrances with no implicit sign;
5. typed encounter tables and generic NPC/translation output names;
6. generic starter metadata;
7. compilation of multiple content specs into the same isolated mod.

Once those primitives and their tests pass, `compiler.py` is frozen for all
three Deep Forest variants. If later content exposes a missing primitive, the
run must be logged as requiring a compiler change before any modification.

## Intentionally retained limitations

- rectangular terrain/zone/feature regions;
- vertical-only bridge visual grammar and horizontal-river rock grammar;
- a single frozen provisional outdoor tile vocabulary;
- no polygon fill, cliff/elevation renderer or arbitrary coastline grammar;
- structural critic cannot see screenshots or estimate enjoyment.

These limitations are evidence. They are not silently repaired during the
Deep Forest benchmark.

## Fixture-0 regression findings

Removing the blanket `blocked -= protected` repair exposed two latent content
errors. The alder loop crossed Glasswind's river away from the bridge, and its
grove spur intersected a fence at undeclared cells. The source specification
now keeps the loop south of the river and names all intended fence openings.
No validator or compiler silently converts blocked authored paths into open
terrain. A formerly descriptive full-map `boundary_forest` zone was also
removed because the new typed boundary already expresses that intent.
