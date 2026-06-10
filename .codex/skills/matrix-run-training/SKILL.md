---
name: matrix-run-training
description: Start a Number Grid Puzzle GA training run quickly when the user asks to run training, train, trainning, or start/continue an offline optimizer run. Use this skill to avoid broad repo exploration before launching the standard training command.
---

# Run Training

Start training with minimal preflight. Do not inspect unrelated specs, code, or old logs
unless the command fails or the user asks for custom parameters.

## Fast Path

1. From the repository root, verify the standard CRN datasets exist:

   ```sh
   ls training_data/train-10m.json training_data/validation-10m.json
   ```

2. If the user did not provide parameters, run this default continuation profile:

   ```sh
   python3 run_bot.py train \
     --non-interactive \
     --population-size 40 \
     --generations 40 \
     --games-per-genome 20 \
     --mutation-rate 0.05 \
     --elite-ratio 0.10 \
     --tournament-size 5 \
     --inject-ratio 0.10 \
     --variance-penalty 0.15 \
     --workers 8 \
     --seed 20260530 \
     --watchdog-patience 12 \
     --watchdog-min-generations 10 \
     --watchdog-min-delta 0.0 \
     --watchdog-average-recovery 0.0 \
     --training-dataset training_data/train-10m.json \
     --validation-dataset training_data/validation-10m.json
   ```

3. Run training in a PTY when possible so progress can be monitored. Give the user the
   summary path printed by the command.

4. If training completes, do not promote weights automatically. Recommend analysis with
   `$matrix-analyze-latest-training-run` before promotion.

## If Inputs Are Missing

- If either standard dataset is missing, generate only the missing dataset before
  training:

  ```sh
  python3 scripts/generate_training_seeds.py \
    --dataset-id train-10m \
    --purpose training \
    --master-seed 20260530 \
    --scenarios 100 \
    --output training_data/train-10m.json

  python3 scripts/generate_training_seeds.py \
    --dataset-id validation-10m \
    --purpose validation \
    --master-seed 20260531 \
    --scenarios 100 \
    --output training_data/validation-10m.json
  ```

- If the user provides any GA flag, preserve it exactly and fill only missing required
  non-interactive fields: `--non-interactive`, `--training-dataset`, and optionally
  `--validation-dataset`.

## Reporting

Keep the first response short: state that training is starting and show the command
profile only if it differs from the default. During long runs, report generation
progress, best fitness, average fitness, diversity, validation fitness when present,
and watchdog stop reason if triggered.

## Safety

- Do not run `scripts/sync_latest_weights.py`.
- Do not edit `training_runs/active_chromosome.json`.
- Do not analyze old logs before starting a requested training run.
- If sandboxing blocks multiprocessing, retry the same training command with escalation.
