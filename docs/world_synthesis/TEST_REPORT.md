# Verification Report

Environment: Windows, Python 3.12.10, upstream development commit `59a34164f`.

## Passing checks

- deterministic build: zero blocking validation errors;
- focused world-synthesis tests: 38/38 passed;
- Ruff: passed for `world_synthesis/` and focused tests;
- Mypy: passed for the isolated tooling with imported upstream internals skipped;
- real `TMXMapLoader`: loaded Glasswind and every Deep Forest A/B/C route with collision and events;
- Ashenbell horizon loader: loaded all 12 R0/R1/R2 maps with collision and events;
- Ashenbell database overlay: activated every generated NPC and encounter record with localization validation;
- Ashenbell cross-map checks: paired warps, graph, transition targets, optionality and state names pass for all methods; the new interaction-anchor audit preserves failures in R0/R1 and passes R2 final;
- normal graphical client: launched all three final Deep Forest maps in responsive windows;
- input smoke: arrow-key movement visibly moved the player toward the bridge;
- visual review: all deterministic normal/debug renders and six Deep Forest live frames inspected;
- Ashenbell visual review: 24 final full/debug renders, R2 initial renders, six representative live frames and the corrected R2 hoist approach inspected;
- compiler freezes: Deep Forest preserves historical SHA-256 `a2e28bd4…62088`; Ashenbell re-froze before variant authoring at `4e94b1ae…f156a` after two logged generic primitives.

## Full repository suite

The pre-Ashenbell freeze run completed with **4,261 passed and 1 failed** in
71.15s. The final post-implementation run collected 4,274 tests and completed
with **4,273 passed and 1 failed** in 67.84s.
The sole failure is upstream `tests/tuxemon/test_map_loader.py::test_remove_from_cache`.
It inserts the literal POSIX key `/fake/path`, while production
`remove_from_cache()` resolves the requested path before lookup. On Windows,
that resolves to a drive-qualified path, so the raw test key cannot match.
Neither the test nor `tuxemon/map/loader.py` differs from upstream in this fork;
the failure reproduces in isolation. It was not hidden or patched as part of
the experiment.
