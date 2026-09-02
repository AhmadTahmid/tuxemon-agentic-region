# Ashenbell: The Low Bell production slice

This directory records the design, implementation, validation and playtest
evidence for a single 60–90-minute Tuxemon vertical slice. It is a production
feasibility test, not a representation benchmark. The Deep Forest and
Ashenbell horizon fixtures remain unchanged under their existing paths.

Canonical authored intent lives in `content/production_slice/low_bell/`.
Runtime output will live in `mods/low_bell/`. Reproducible evidence will live
in `artifacts/production_slice/low_bell/`.

The implementation is deliberately limited to this episode. It adds no new
region, monster, visual asset, image model or engine port.

Development commands:

```powershell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice build low_bell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice render low_bell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice validate low_bell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice play low_bell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice playtest low_bell
```
