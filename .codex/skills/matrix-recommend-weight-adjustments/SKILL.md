---
name: matrix-recommend-weight-adjustments
description: Analyze Number Grid Puzzle GA training-run chromosome weight and mask changes, correlate them with training/validation outcomes, persist a read-only recommendation artifact, and recommend directional heuristic weight adjustments for the next experiment. Use when asked how to adjust weights, inspect weight-change history, explain which feature weights should increase/decrease/stabilize, or derive next weight tuning decisions from training logs.
---

# Recommend Weight Adjustments

Produce an evidence-based, read-only recommendation for how heuristic weights should
change in the next training experiment. This skill does not choose an old chromosome as
the winner; it studies how weights and masks moved across saved best chromosomes and
connects those movements to observed outcomes.

## Workflow

1. Run the bundled analyzer from the repository root:

   ```sh
   python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py \
     --json
   ```

2. The analyzer persists a versioned JSON report under:

   ```text
   training_runs/weight-adjustment-recommendation-<timestamp>.json
   ```

3. Use the persisted report for the user-facing answer. Preserve the distinction between
   measured facts, directional recommendations, and caveats.

4. Summarize:
   - number of runs analyzed
   - evidence scope
   - validation coverage and dataset comparability warnings
   - highest-confidence phase/feature recommendations
   - mask recommendations
   - recommended next action

5. If the report says validation coverage is weak, recommend validation replay or a
   controlled experiment before making aggressive manual weight changes.

## Evidence Scope

Analysis uses population telemetry when it is available in newer training summaries:

- `generation_summaries[*].population_telemetry.ranked_candidates`
- `generation_summaries[*].population_telemetry.gene_statistics`

For older summaries, fall back to:

- `generation_summaries[*].best_chromosome`
- `generation_summaries[*].best_fitness`
- final `best_chromosome`
- `best_fitness`
- `validation_fitness`
- `stop_reason`
- `watchdog_decision`
- `plateau_diagnostics`
- `training_dataset` and `validation_dataset`

Treat recommendations as directional, not causal proof. If only older summaries are
available, report that evidence scope is limited to generation-best chromosomes.

## Safety Rules

- Do not edit `training_runs/active_chromosome.json`.
- Do not promote weights.
- Do not start training automatically.
- Do not rewrite training summaries.
- Do not compare validation fitness across different validation dataset checksums
  without warning.
- Do not infer superiority from training fitness alone when validation is missing.

## Optional Inputs

Analyze all summaries:

```sh
python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py
```

Analyze one summary:

```sh
python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py \
  --summary training_runs/train-<timestamp>.json
```

Emit JSON for agent handoff:

```sh
python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py \
  --json
```

## Output Contract

Require these top-level fields before consuming the payload:

- `schema_version == 1`
- `report_type == "matrix_weight_adjustment_recommendation"`
- `analysis_mode == "read_only"`

Main report sections:

- `runs_analyzed`
- `datasets`
- `global_assessment`
- `phase_recommendations`
- `mask_recommendations`
- `recommended_next_action`
- `analysis_path`
