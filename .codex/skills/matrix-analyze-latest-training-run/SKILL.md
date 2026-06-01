---
name: matrix-analyze-latest-training-run
description: Analyze the newest Number Grid Puzzle GA training summary and diagnose convergence, plateau, validation, and active-weight status. Use when the user asks to analyze the latest training run, inspect the last train log, explain whether training plateaued, compare a recent candidate with the active chromosome, or recommend the next training experiment.
---

# Analyze Latest Training Run

Produce an evidence-based report for the newest persisted GA run. Keep analysis
read-only unless the user explicitly asks to promote weights or start another run.

## Workflow

1. Run the bundled analyzer from the repository root:

   ```sh
   python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py
   ```

2. Report the selected summary path, status, configuration, best and validation fitness,
   best generation, recent fitness movement, plateau diagnostics, active-model relation,
   and the script recommendation.

3. Distinguish measured facts from inference. Treat a high diversity ratio as evidence
   that chromosomes differ, not proof that the search explores useful regions.

4. If the newest candidate has a validation dataset but no recorded validation fitness,
   offer to run:

   ```sh
   python3 run_bot.py replay <summary-path> --dataset validation
   ```

5. If the user requests a comparison with the active chromosome, compare candidates on
   the same validation dataset. Do not infer superiority from training fitness alone.

6. Recommend one concrete next action. Prefer a validation replay before changing GA
   parameters when validation evidence is missing.

## Selection Rules

- Select the newest parseable `training_runs/train-*.json` by `updated_at`, falling back
  to filename order only when timestamps are missing or invalid.
- Include `completed`, `interrupted`, `failed`, and `running` summaries.
- Handle older summaries without `plateau_diagnostics`; state that metrics are
  unavailable instead of treating them as zero.
- Read `training_runs/active_chromosome.json` only for status context.

## Safety Rules

- Do not call `scripts/sync_latest_weights.py` during analysis.
- Do not edit `training_runs/active_chromosome.json`.
- Do not start training automatically.
- Promote weights only after an explicit user request.

## Optional Inputs

Analyze a specific summary or emit machine-readable JSON:

```sh
python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
  --summary training_runs/train-<timestamp>.json

python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
  --json
```
