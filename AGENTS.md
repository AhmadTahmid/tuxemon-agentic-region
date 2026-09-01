# Agent Guide: Tuxemon World Synthesis

This repository preserves upstream Tuxemon and adds an isolated world-design
experiment. Read `docs/world_synthesis/README.md` and
`docs/world_synthesis/DECISIONS.md` before changing experiment files.

## Source and generated boundaries

- `content/world_synthesis/` is canonical authored intent.
- `benchmarks/briefs/` and `benchmarks/generated/` hold benchmark requirements,
  method-specific WorldSpecs, revision evidence and deterministic renders.
- `world_synthesis/` is deterministic compiler, validation, rendering and critic code.
- `mods/world_synthesis/mod.yaml` is hand-authored campaign metadata.
- `mods/world_synthesis/maps/`, `mods/world_synthesis/db/` and its locale catalogue are compiler output.
- `artifacts/` and `docs/world_synthesis/ASSET_CATALOG.json` are reproducible evidence.
- `mods/tuxemon/` and `tuxemon/` are upstream. Avoid changing them unless an upstream engine defect makes isolation impossible.

## Commands

```powershell
.\.venv\Scripts\python.exe -m world_synthesis build
.\.venv\Scripts\python.exe -m world_synthesis.benchmark build
.\.venv\Scripts\python.exe -m world_synthesis.benchmark play deep_forest
.\.venv\Scripts\python.exe -m pytest tests\world_synthesis -q --no-cov
.\.venv\Scripts\ruff.exe check world_synthesis tests\world_synthesis
.\.venv\Scripts\mypy.exe --follow-imports=skip world_synthesis
.\.venv\Scripts\python.exe -m world_synthesis.play
```

## Determinism and safe content work

Do not put timestamps, process IDs or unordered-set iteration into compiled
maps. Seed every mechanical placement rule from the world seed, map ID, rule
ID and revision. Do not hand-edit generated TMX; change the YAML or compiler.
Do not silently repair authored intent. Blocking topology failures must stop
the build. Reuse assets through semantic catalogue evidence, and record
uncertainty when visual meaning is not established.

For the Deep Forest A/B/C benchmark, `world_synthesis/compiler.py` is frozen at
commit `1ded0461f` and SHA-256
`a2e28bd42e4810faef84bbe508594aa6f3e231b81e8d1f5d92b6562689962088`.
Changing it invalidates the code-free comparison unless the missing primitive
and rerun are recorded in `artifacts/world_synthesis/generalization_log.json`.

## Definition of done

A world-synthesis change is done when schemas validate, repeated builds have
identical hashes, independent reachability/collision/reference checks pass,
the real Tuxemon TMX loader accepts the maps, static renders were inspected,
and any visible/gameplay change was exercised in the client.
