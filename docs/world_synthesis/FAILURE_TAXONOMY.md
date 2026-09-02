# World-Synthesis Failure Taxonomy

Failures are recorded even when maps validate. `severity` should distinguish a
blocking gameplay defect from a design weakness, visual-vocabulary limitation
or uncertain observation.

| Code | Failure | Observable evidence |
|---|---|---|
| REPETITIVE_GEOMETRY | Repeated rectangles, straight corridors or regular grids | Render and path/zone geometry |
| MEANINGLESS_DEAD_END | Branch has no reward, story beat, view or route function | Reachability graph plus content review |
| POOR_SIGHTLINE | Landmark/choice is hidden or clutter obscures navigation | Screenshot/playtest |
| WEAK_LANDMARK | Landmark does not dominate composition or memory | Blind evaluation response |
| INCOHERENT_ASSET_USE | Semantically incompatible current assets are combined | Asset IDs plus render review |
| OVER_DECORATION | Clutter impairs route reading or movement | Density metrics and playtest |
| UNDER_DECORATION | Large areas lack visual or gameplay purpose | Density metrics and render |
| POOR_ROUTE_RHYTHM | Compression/release/choice/rest beats are absent or mistimed | Path structure and playtest |
| BAD_NPC_PLACEMENT | NPC blocks flow, feels random or lacks local purpose | Coordinates, role and playtest |
| NARRATIVE_MAP_MISMATCH | Geometry does not support the brief/story role | Brief-to-spec comparison |
| INVALID_PROGRESSION | Mandatory goal/exit cannot be reached or quest reference is invalid | Blocking validator |
| COLLISION_MISTAKE | Visual and semantic obstruction disagree | Debug render and in-game collision test |
| ASSET_SEMANTIC_MISMATCH | Registered tile/prop does not read as intended | Render review with asset catalogue |
| WEAK_REGIONAL_IDENTITY | Map could be relabelled without meaningful change | Blind comparison/human comments |
| COMPILER_LIMITATION | Desired reusable operation cannot be represented mechanically | Generalization log |
| WORLDSPEC_LIMITATION | Planner intent cannot be expressed in typed content | Schema failure/generalization log |
| LLM_SPATIAL_REASONING_FAILURE | One-shot or structured placement produces incoherent space | Spec/render comparison |
| LLM_LONG_HORIZON_FAILURE | Distant map decisions contradict progression or earlier intent | Multi-map graph/content review |
| CRITIC_BLIND_SPOT | Structural score is high despite an obvious human-visible defect | Score versus blind evaluation |
| BASELINE_UNFAIRNESS | A/B/C differ in scope, assets, allowances or repairs | Comparability audit |
| R0_LOW_LEVEL_REPRESENTATION_FAILURE | Direct TMX/event output loses intent, duplicates low-level bookkeeping, or becomes difficult to audit/maintain | Raw source, repair log, low-level diff |
| R1_ONE_SHOT_LONG_HORIZON_CONTRADICTION | One-shot WorldSpec conflicts across maps despite local validity | Cross-map consistency report and semantic review |
| R2_PLANNING_REVISION_FAILURE | Staged planning or its allowed revision fails to remove an evidenced defect | Initial/final validation, critic and revision diff |
| GEOGRAPHIC_CONTRADICTION | A road, ridge, watercourse, boundary or adjacency cannot continue as claimed | Region graph, map edges, renders and dialogue |
| NPC_CONTRADICTION | NPCs disagree about an immutable fact rather than offering compatible perspectives | Dialogue fact table and semantic review |
| ECOLOGICAL_INCONSISTENCY | Encounter composition does not follow the declared habitat gradient | Encounter tables, zones and ecology declaration |
| COPY_PASTED_MAP_STRUCTURE | Maps with different roles reuse circulation/composition without a regional reason | Cross-map path/zone comparison |
| OPTIONAL_CONTENT_MANDATORY | Main progression requires entering a declared optional area | Progression graph with optional nodes removed |
| STATE_EVENT_INCONSISTENCY | A persistent variable lacks a producer/consumer, uses mismatched names, or can strand traversal | Parsed action/condition graph |

## Fixture 0 observations

- Glasswind's first render exposed `ASSET_SEMANTIC_MISMATCH`: the initially
  selected water and grass variation tiles contained edge pixels despite
  passing semantic validation.
- The baseline compiler contains `COMPILER_LIMITATION` for non-horizontal
  water and non-vertical crossings.
- The structural critic is a known `CRITIC_BLIND_SPOT` risk. Its score is not a
  quality score and must not be merged with human results.

## Deep Forest observations

| Map/method | Failure | Evidence | Classification | Disposition |
|---|---|---|---|---|
| Deep Forest C initial | A sign and ward stone blocked authored paths; the secret became unreachable. | `benchmarks/generated/c_agentic/deep_forest/initial_validation/validation.txt` | collision mistake / LLM spatial-reasoning failure | Corrected through revision content; compiler remained frozen. |
| Deep Forest C initial | Structural heuristic scored 7.5 while the map had two blocking errors. | `initial_structural_critic.json` beside the validation report | critic blind spot | Retained as evidence; validation and human results stay independent. |
| Deep Forest A/B/C | Repeated pine silhouettes dominate dense areas and make sub-areas less visually distinct. | Static and live gallery renders | frozen asset-vocabulary limitation / repetition | Not repaired in this art-frozen milestone. |
| Deep Forest A/B/C | Dominant landmarks are readable clearings but boulder clusters have modest visual identity. | Landmark captures in `benchmark_gallery.md` | asset-semantic mismatch / weak landmark | Human tester should compare memorability; no new art permitted. |
| Deep Forest B/C | Both capable LLM-authored paths converge on broadly similar S-curves and west-side loops. | Full-map renders | LLM spatial-reasoning homogeneity | Blind playtesting must determine whether local rhythm still differs perceptibly. |
| Capture tooling | Accelerated Pygame surfaces rendered black through Win32 `PrintWindow`. | Rejected first capture batch | tooling limitation, not map quality | Capture helper now foregrounds the client and uses screen pixels. |

## Ashenbell horizon observations

| Map/method | Failure | Evidence | Classification | Disposition |
|---|---|---|---|---|
| Shared pre-authoring audit | WorldSpec story events exposed actions but not existing Tuxemon state conditions. | `horizon_generalization_log.json` | WorldSpec limitation | Added one generic `conditions` list, re-froze before all variants. |
| Shared pre-authoring audit | The compiler could label a settlement but could not compose a house from the existing reviewed atlas. | Atlas audit and `horizon_generalization_log.json` | compiler limitation | Added one generic fixed building stamp from existing tiles, re-froze before all variants. |
| R0 raw | Tileset path was relative to the evidence folder, positive state conditions omitted the `is` operator, and `botanist` did not resolve. | R0 `mechanical_repairs.json` and first client launch | low-level representation / asset-reference failure | Loader/grammar/reference repairs only; no design changes. |
| R0 final | Nine player-facing story/state events, including the hoist producer and shortcut consumers, occupy traversable cells without stable anchors. The files load and the graph/state names pass, but the interactions are not reliable in the client. | R0 consistency report plus in-client hoist exercise | R0 low-level representation failure / state-event inconsistency | Retained without redesign; no WorldSpec was retrofitted. |
| R1 raw/compilable | Two comma-delimited actions required YAML quoting; positive conditions and one invalid sprite reference required compatibility repairs. | R1 raw output and `mechanical_repairs.json` | schema-format / event-grammar / asset-reference failure | Mechanical repair only. |
| R1 final | Props, a river edge and settlement/quarry composition overlap authored paths on three maps. | R1 `validation/validation.json` and debug overview | LLM spatial-reasoning failure / collision mistake | Preserved unrevised as the one-shot result. All critical entities remain reachable. |
| R1 final | Geography, facts, ecology, optionality and state names are consistent, but seven player-facing interactions lack stable anchors. The hoist can produce state while both shortcut consumers remain unreliable. | R1 `consistency_report.json` | one-shot long-horizon progression failure / state-event inconsistency | Preserved unrevised; demonstrates that declarative state names alone do not prove usable progression. |
| R1 final | South/pass circulation uses similar long central polylines. | R1 overview and consistency critic | repeated path geometry / copy-pasted structure risk | Preserved; blind playtest must judge perceptual impact. |
| R2 initial | River edge, garden fence/plinth and ridge-stair rock overlap authored paths. | R2 `initial_validation/validation.json` | planning/spatial-reasoning failure | Corrected in the single recorded content revision. |
| R2 initial | Hoist produced `r2_hoist:raised` while village/pass consumers required `r2_shortcut:open`; several interaction cells also lacked collision/NPC anchors. | R2 `initial_consistency_report.json` and in-client hoist exercise | state/event inconsistency / long-horizon failure / critic blind spot | Corrected in the recorded content revision without compiler changes. |
| R2 final | All ordinary and cross-map mechanical checks, including stable reachable interaction anchors, pass; the pass remains sparse. | R2 final validation, consistency report and renders | revision success plus frozen-vocabulary limitation | Sparse warning retained instead of optimizing a heuristic. |
| Validation stack | Reachability and state producer/consumer checks initially treated a traversable event cell as usable, overlooking `char_facing_tile` semantics. | Failed first hoist interaction exercise | critic/validation blind spot | Added a generic stable-anchor and reachable-adjacent-cell audit for all three methods; improved secret validation to accept legitimate adjacent interaction. |
| Validation stack | TMX loader passed before the real database overlay rejected a documented but nonexistent `botanist` slug. | First graphical launch and final database-activation check | critic/validation blind spot | Build now activates and validates the full NPC/encounter overlay. |
