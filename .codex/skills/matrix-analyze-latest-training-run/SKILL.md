---
name: matrix-analyze-latest-training-run
description: Analyze the newest Number Grid Puzzle GA training summary and diagnose convergence, plateau, validation, and active-weight status. Use when the user asks to analyze the latest training run, inspect the last train log, explain whether training plateaued, compare a recent candidate with the active chromosome, or recommend the next training experiment.
---

# Analyze Latest Training Run

Produce an evidence-based report for the newest persisted GA run. Persist only the
handoff artifact; keep training summaries and active weights read-only unless the user
explicitly asks to promote weights or start another run.

By default the analyzer searches recursively under `training_runs/`, so experiment
subdirectories such as `training_runs/experiment-*/train-*.json` are eligible and are
ordered by `updated_at`.

## Workflow

1. Run the bundled analyzer from the repository root:

   ```sh
   python3 .codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py \
     --json
   ```

2. The analyzer always persists the versioned JSON handoff beside the selected summary
   as `training_runs/analysis-<train-summary-stem>.json`. Treat that file as the
   reusable input for the next skill. Use the measured fields, `assessment`, and
   `recommended_next_action`; do not replace them with conclusions inferred from
   training fitness alone.

3. If the analyzer warns that an analysis already exists for an old log and exits with
   status `2`, report the warning and stop. Do not overwrite the artifact or continue
   with a repeated analysis.

4. For a user-facing response, summarize the selected summary path, persisted analysis
   path, status,
   configuration, best and validation fitness, best generation, recent fitness
   movement, plateau diagnostics, active-model relation, assessment, and recommended
   next action.

5. Preserve the distinction between measured facts and inference. Treat a high
   diversity ratio as evidence that chromosomes differ, not proof that the search
   explores useful regions.

6. If the newest candidate has a validation dataset but no recorded validation fitness,
   offer to run:

   ```sh
   python3 run_bot.py replay <summary-path> --dataset validation
   ```

7. If the user requests a comparison with the active chromosome, compare candidates on
   the same validation dataset. Do not infer superiority from training fitness alone.

8. Recommend one concrete next action. Prefer a validation replay before changing GA
   parameters when validation evidence is missing.

## Agent Handoff Contract

- Use `--json` when the output will be passed to another agent.
- The analyzer always writes `analysis-<train-summary-stem>.json` beside the selected
  summary, even when stdout is rendered as Markdown.
- Never overwrite an existing analysis artifact. Treat its presence as evidence that
  the selected log is old or has already been analyzed, warn the user, and stop.
- Require `schema_version == 1` and
  `report_type == "matrix_training_run_analysis"` before consuming the payload.
- `analysis_mode` is `read_only`.
- Top-level measured fields remain stable for simple consumers.
- `datasets`, `plateau_diagnostics`, and `active_model` provide evidence context.
- `assessment` separates status labels, facts, inferences, and caveats.
- `recommended_next_action` contains an action code, rationale, optional command, and
  whether execution requires an explicit user request.

## Selection Rules

- Select the newest parseable `train-*.json` recursively under `training_runs/` by
  `updated_at`, falling back to filename order only when timestamps are missing or invalid.
- Include `completed`, `interrupted`, `failed`, and `running` summaries.
- Handle older summaries without `plateau_diagnostics`; state that metrics are
  unavailable instead of treating them as zero.
- Read `training_runs/active_chromosome.json` only for status context. When the summary is
  inside an experiment subdirectory and the default active-model path is used, prefer the
  sibling `active_chromosome.json` beside that summary directory for local context.

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
