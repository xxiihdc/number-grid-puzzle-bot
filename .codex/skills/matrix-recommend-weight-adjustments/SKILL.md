---
name: matrix-recommend-weight-adjustments
description: Analyze Number Grid Puzzle GA training-run chromosome weight and mask changes, correlate them with training/validation outcomes, persist a read-only recommendation artifact, and recommend directional heuristic weight adjustments for the next experiment. Use when asked how to adjust weights, inspect weight-change history, explain which feature weights should increase/decrease/stabilize, or derive next weight tuning decisions from training logs.
---

# Recommend Weight Adjustments

Produce an evidence-based, read-only recommendation for how heuristic weights should
change in the next training experiment. This skill does not choose an old chromosome as
the winner; it studies how weights and masks moved across saved best chromosomes and
connects those movements to observed outcomes.

By default the recommender searches recursively under `training_runs/`, so experiment
subdirectories such as `training_runs/experiment-*/train-*.json` are eligible.

## Workflow

1. Run the bundled analyzer from the repository root:

   ```sh
   python3 .codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py \
     --json
   ```

2. The recommender first checks whether the newest selected training summary already
   has a latest-run analysis handoff:

   ```text
   training_runs/analysis-<train-summary-stem>.json
   ```

   If that file is missing, it invokes the `matrix-analyze-latest-training-run`
   analyzer as a sub-skill step before building the weight recommendation. The
   resulting recommendation includes a `latest_training_analysis` status of
   `already_available`, `created`, `failed`, or `unavailable`.

3. The analyzer persists a versioned JSON report under:

   ```text
   <selected-run-directory>/weight-adjustment-recommendation-<timestamp>.json
   ```

   The ready-to-run candidate experiment is also created under the selected run's
   directory so follow-up runs continue from the local `active_chromosome.json`.

4. The recommender also persists a canonical best-known CLI profile artifact under:

   ```text
   training_runs/best_known_training_profile.json
   ```

   This artifact captures the strongest known training configuration from the analyzed
   runs, keyed primarily by validation fitness, and is intended to preserve operating
   knowledge alongside chromosome/weight artifacts.

5. Use the persisted report for the user-facing answer. Preserve the distinction between
   measured facts, directional recommendations, and caveats.

6. Summarize:
   - number of runs analyzed
   - latest training analysis status and path
   - evidence scope
   - validation coverage and dataset comparability warnings
   - best-known training profile artifact and source run
   - ready-to-run candidate active model path and training command when available
   - highest-confidence phase/feature recommendations
   - mask recommendations
   - recommended next action

7. If the report says validation coverage is weak, recommend validation replay or a
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

When a selected run includes a `config` block, reuse that run's CLI parameters and
dataset paths when constructing the next training command instead of falling back to a
hardcoded baseline.

## Safety Rules

- Do not edit `training_runs/active_chromosome.json`.
- Do not promote weights.
- Do not start training automatically.
- Do not rewrite training summaries.
- Do not compare validation fitness across different validation dataset checksums
  without warning.
- Do not infer superiority from training fitness alone when validation is missing.

## Optional Inputs

Analyze all summaries recursively:

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
- `latest_training_analysis`
- `datasets`
- `global_assessment`
- `candidate_experiment`
- `phase_recommendations`
- `mask_recommendations`
- `recommended_next_action`
- `analysis_path`
