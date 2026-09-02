# Ashenbell representation + horizon report

## 1. Did direct low-level generation work?

Partly. R0 produced four traversable TMX maps plus NPC, encounter and localization records without WorldSpec or compiler imports. The files pass parsing, reachability, transition-target, paired-warp, optionality, state-name, real TMX-loader and full database-activation checks. Both village and quarry were exercised in the graphical client.

It was not repair-free. The raw response needed three compatibility-only repairs: rebase the tileset path when installing from the evidence directory, add Tuxemon's explicit `is` operator to positive `variable_set` conditions, and replace the documented but nonexistent `botanist` reference with the existing `scientist` reference. No tile, coordinate, collision, topology, ecology, dialogue meaning or reward was redesigned.

It did not produce a fully functional slice. Nine player-facing story/state events, including the quarry hoist and both shortcut consumers, were placed on traversable cells without a blocking prop or NPC anchor. Directional input therefore moves onto those cells instead of reliably leaving the player beside and facing them. The new generic audit preserves this failure rather than redesigning R0. Direct generation worked better than a claim such as “LLMs cannot author TMX” would predict, but low-level validity hid a functional event-placement error and semantic intent remains difficult to audit.

## 2. What failures disappeared when WorldSpec was introduced?

WorldSpec removed manual XML/object/database serialization and made geography, map roles, landmarks, ecology, NPC roles, optional paths and pacing explicitly inspectable. The frozen compiler deterministically handled tile layers, collision rectangles, database records, localization and manifests. That made cross-map review and content diffs materially easier than inspecting R0's direct grid/event writer. R1 also correctly co-located the quarry hoist producer with a blocking sign, eliminating R0's failure at that specific high-value interaction.

WorldSpec did not automatically eliminate the whole interaction-anchor class: authors must still align semantic events with collision-bearing props. The strongest representation result is therefore improved auditability and reduced low-level bookkeeping, plus one observed correct event/prop coupling—not immunity from spatial mistakes.

## 3. What failures remained in one-shot WorldSpec?

R1 preserved three `path_blocked` errors: the South Route clips a sign/river edge, the village paths overlap fence/plinth/building collision, and the quarry path overlaps a worked stone/hoist sign. It also left seven player-facing interactions without stable collision/NPC anchors. The hoist producer itself is correctly anchored, but the village and pass shortcut consumers are not, so the persistent state can be produced without making the intended traversal benefit reliably usable. The real client and files load, but the result fails collision/path-clearance and cross-map progression acceptance. R1 also retains similar long central polyline grammar across maps and one sparse-pass warning.

The one-shot did *not* exhibit an NPC, geographic, ecological, optionality or state-*naming* contradiction. Shared facts, encounter gradient and paired topology remain consistent. Its long-horizon failure is spatial/mechanical coupling across the producer and consumers, not contradictory lore.

## 4. Did staged agentic planning materially help multi-map consistency?

Yes, for the final accepted result, but the evidence attributes the advantage mainly to explicit validation, in-client checking and revision rather than flawless up-front planning. R2 initial contained three local path/collision defects, one genuine state mismatch (`r2_hoist:raised` versus consumers of `r2_shortcut:open`), and the same unanchored-interaction blind spot. The recorded critic-linked revision fixed the state name, path defects and every interaction anchor. R2 final has zero blocking validation errors and zero mechanical consistency failures.

The coordinate-free region model also yielded more varied circulation and a clearer fact/knowledge allocation than R1's repeated path grammar. Static evidence cannot establish whether players perceive that difference as materially better. The defensible result is: staged validation+revision added clear value at this horizon; the independent value of pre-planning remains confounded with the revision loop.

## 5. Did any method require compiler modification?

The benchmark required two generic pre-authoring primitives, not a method-specific rescue. WorldSpec needed generic story-event conditions to expose Tuxemon's existing state checks, and the compiler needed one generic four-by-five building stamp using existing frozen atlas tiles so “settlement” could contain actual houses. Both limitations were logged before variant generation, implemented once, tested, and re-frozen at compiler SHA-256 `4e94b1ae4e531dd70da33b162b8329a0d0d2cc5a71190633e4a560b1ff7f156a` for R0/R1/R2.

No compiler behavior changed during variant authoring, R2 criticism or revision. No Ashenbell map ID, coordinate, story fact or method-specific rule entered the compiler.

## 6. Which conclusions require human playtesting?

Human playtesting is required for traversal time, navigation clarity, perceived regional coherence, settlement believability, environmental variety, dialogue naturalness, landmark memory, desire to explore, quarry optionality, whether the quarry changes the player's interpretation, perceived repetition, intentional authorship and enjoyment. It is also required to determine whether R1's reachable path collisions are noticeable in practice and whether R2's more differentiated circulation matters perceptually.

Automated evidence can establish references, graph/state consistency, interaction anchoring, collision reachability and loader/database acceptance. It cannot establish fun or a winner. Human results remain separate and pending.

## 7. What should the next experiment isolate?

Isolate pre-planning from feedback. Compare one-shot WorldSpec **plus the same cross-map validator and one revision opportunity** against region-model-first WorldSpec **plus the identical validator and one revision opportunity**. Hold model, prompt information, revision budget, dimensions and vocabulary fixed. This would test whether the coordinate-free region model adds value beyond the already-demonstrated value of validation and revision.
