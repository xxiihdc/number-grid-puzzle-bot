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
   python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
     --json
   ```

2. Treat the versioned JSON as the reusable agent handoff. Use the measured fields,
   `assessment`, and `recommended_next_action`; do not replace them with conclusions
   inferred from training fitness alone.

3. For a user-facing response, summarize the selected summary path, status,
   configuration, best and validation fitness, best generation, recent fitness
   movement, plateau diagnostics, active-model relation, assessment, and recommended
   next action.

4. Preserve the distinction between measured facts and inference. Treat a high
   diversity ratio as evidence that chromosomes differ, not proof that the search
   explores useful regions.

5. If the newest candidate has a validation dataset but no recorded validation fitness,
   offer to run:

   ```sh
   python3 run_bot.py replay <summary-path> --dataset validation
   ```

6. If the user requests a comparison with the active chromosome, compare candidates on
   the same validation dataset. Do not infer superiority from training fitness alone.

7. Recommend one concrete next action. Prefer a validation replay before changing GA
   parameters when validation evidence is missing.

## Agent Handoff Contract

- Use `--json` when the output will be passed to another agent.
- Require `schema_version == 1` and
  `report_type == "matrix_training_run_analysis"` before consuming the payload.
- `analysis_mode` is `read_only`.
- Top-level measured fields remain stable for simple consumers.
- `datasets`, `plateau_diagnostics`, and `active_model` provide evidence context.
- `assessment` separates status labels, facts, inferences, and caveats.
- `recommended_next_action` contains an action code, rationale, optional command, and
  whether execution requires an explicit user request.

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

Analyze a specific summary, render a human-readable report, or emit agent-handoff JSON:

```sh
python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
  --summary training_runs/train-<timestamp>.json

python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
  --json
```
