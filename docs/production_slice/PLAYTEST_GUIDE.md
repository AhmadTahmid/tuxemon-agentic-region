# Playtest guide

## Fresh-session launcher

From the repository root in PowerShell:

```powershell
.\.venv\Scripts\python.exe -m world_synthesis.production_slice playtest low_bell
```

This builds the current canonical episode, creates a new session record, and
starts Tuxemon with `load_slot=None`; it does not load or overwrite an existing
save slot. The launcher shows only **Ashenbell: The Low Bell**. Close the game
after reaching the ending hook in resolved Ashenbell. The launcher then asks
for completion confirmation and presents the questionnaire. If the episode
was not completed, it records an incomplete session without presenting the
completion questionnaire.

Human responses live only under
`artifacts/production_slice/low_bell/human_evaluation/`. They are never merged
with `automated_acceptance.json`, and the response schema contains no aggregate
score. Do not read automated reports before a human session if that knowledge
could bias the playthrough.

## Questionnaire

Ratings use 1–10; yes/no and free responses are stored separately. The
launcher asks every required question:

Required questions:

1. Was the current goal usually clear?
2. Was there any stretch that felt empty or pointless?
3. Which three characters do you remember?
4. Did the village feel inhabited?
5. Did the village feel changed after the climax?
6. Did the quarry reveal change your understanding of the low tone?
7. Did optional content feel worth exploring?
8. Did battles and exploration feel well paced?
9. Did any dialogue feel like filler or exposition?
10. Did any map feel randomly generated?
11. What was the most memorable moment?
12. Did you feel any emotional investment?
13. Would you continue playing another episode?
14. Did this feel like a competent early chapter of a classic
    monster-catching RPG?
