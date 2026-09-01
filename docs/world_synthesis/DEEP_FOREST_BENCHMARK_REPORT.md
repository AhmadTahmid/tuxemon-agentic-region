# Deep Forest A/B/C benchmark report

## What was attempted

One fixed 40×44 Deep Forest brief was implemented three ways while retaining
the same Tuxemon engine, outdoor atlas, compiler freeze, monsters, items, and
functional allowance:

- A: deterministic single-pass procedural rules;
- B: one saved one-shot prompt and its unrevised valid WorldSpec;
- C: explicit design reasoning, initial WorldSpec, render/validation/structural
  critique, and one recorded content revision.

Each final map has three NPCs (two trainers), two encounter zones, one dominant
landmark, one optional loop, and one potion secret. All use the visible name
“Mossveil Passage.”

## Results

| Method | Validation | Structural design score | Compiler changed during map creation |
|---|---:|---:|---:|
| A | 0 errors, 0 warnings | 7.2 | No |
| B | 0 errors, 0 warnings; no repair | 7.4 | No |
| C final | 0 errors, 0 warnings | 7.5 | No |

These scores are deterministic structural heuristics, not ratings of visual
quality or fun. Their small spread cannot establish a winner.

C initial is important negative evidence: it scored 7.5 while a sign and stone
blocked its paths and made the secret unreachable. Validation caught both. The
recorded revision moved those two props without changing scope, assets, or
compiler code, after which all critical content became reachable.

## Compiler generalization required

Before authoring any Deep Forest variant, Glasswind fixture 0 required typed
base terrain/boundaries, forest and safe zones, explicit props and fence
entrances, typed encounter tables, and generic outputs. That work was frozen at
commit `1ded0461f`. The compiler file remained byte-identical while A, B, and C
were created. No missing primitive was discovered by this family.

## Comparability assessment

A/B/C are genuinely comparable in engine, dimensions, vocabulary, seed,
functional counts, encounter/reward allowances, and validator. They are not
identical in authorship effort: that difference is the independent variable.
A is a fair competent baseline rather than noise; B received no visual revision;
C retains its failed initial state and exact revision diff.

The fixed visual vocabulary constrains all three. Dense pine repetition and
modest boulder landmarks may compress perceptual differences between methods.
This is a benchmark finding, not a reason to change art mid-experiment.

## Verification and evidence

- all three final specs compile and pass graph/collision validation;
- all three load through Tuxemon's real `TMXMapLoader`;
- all three stayed alive through normal headless startup with no load errors;
- two graphical in-game captures were produced for each map;
- deterministic normal/debug renders and critic reports are indexed in
  `artifacts/world_synthesis/benchmark_gallery.md`.

## What the human should test next

Run `python -m world_synthesis.benchmark play deep_forest` for multiple blind
sessions. Compare navigation clarity, exploration desire, landmark memory,
intentionality, artificial repetition, and overall enjoyment. Do not inspect
the method-revealing gallery until after submitting the questionnaire. Human
results are pending, so this report does not conclude that C wins.
