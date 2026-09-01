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
