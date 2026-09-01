# Verification Report

Environment: Windows, Python 3.12.10, upstream development commit `59a34164f`.

## Passing checks

- deterministic build: zero blocking validation errors;
- focused world-synthesis tests: 26/26 passed;
- Ruff: passed for `world_synthesis/` and focused tests;
- Mypy: passed for the isolated tooling with imported upstream internals skipped;
- real `TMXMapLoader`: loaded Glasswind and every Deep Forest A/B/C route with collision and events;
- normal graphical client: launched all three final Deep Forest maps in responsive windows;
- input smoke: arrow-key movement visibly moved the player toward the bridge;
- visual review: all deterministic normal/debug renders and six Deep Forest live frames inspected;
- compiler freeze: `compiler.py` remained byte-identical after commit `1ded0461f`.

## Full repository suite

`pytest -q --no-cov` completed with **4,261 passed and 1 failed** in 61.26s.
The sole failure is upstream `tests/tuxemon/test_map_loader.py::test_remove_from_cache`.
It inserts the literal POSIX key `/fake/path`, while production
`remove_from_cache()` resolves the requested path before lookup. On Windows,
that resolves to a drive-qualified path, so the raw test key cannot match.
Neither the test nor `tuxemon/map/loader.py` differs from upstream in this fork;
the failure reproduces in isolation. It was not hidden or patched as part of
the experiment.
