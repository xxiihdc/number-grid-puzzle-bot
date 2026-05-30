# Quick Start: Optimize Training Workflow

## Overview

Offline training evaluates phase-based heuristic chromosomes against reusable fixed
block sequences. Every candidate receives the same scenarios, completed-game evaluation
is deterministic, and independent genomes can run across local CPU workers.

## Generate Training and Validation Datasets

```bash
python3 scripts/generate_training_seeds.py \
  --dataset-id train-default \
  --purpose training \
  --master-seed 20260530 \
  --scenarios 100 \
  --output training_data/train-default.json

python3 scripts/generate_training_seeds.py \
  --dataset-id validation-default \
  --purpose validation \
  --master-seed 20260531 \
  --scenarios 40 \
  --output training_data/validation-default.json
```

Generation prints the persisted dataset identity, scenario count, and checksum.

## Configure Training Interactively

```bash
python3 run_bot.py train
```

The local terminal interface shows available datasets and the defaults:

| Setting | Default |
|---------|---------|
| Population size | `50` |
| Generations | `100` |
| Games evaluated per genome | `40` |
| Mutation rate | `0.20` |
| Elite ratio | `0.10` |
| Tournament size | `5` |
| Random injection ratio | `0.10` |
| Variance penalty | `0.15` |
| Worker count | Local CPU-aware default |

The interface validates settings, displays derived elite and injection counts, and asks
for confirmation before starting.

## Run a Scripted Experiment

```bash
python3 run_bot.py train \
  --non-interactive \
  --population-size 50 \
  --generations 100 \
  --games-per-genome 40 \
  --mutation-rate 0.20 \
  --elite-ratio 0.10 \
  --tournament-size 5 \
  --inject-ratio 0.10 \
  --variance-penalty 0.15 \
  --workers 4 \
  --seed 20260530 \
  --training-dataset training_data/train-default.json \
  --validation-dataset training_data/validation-default.json
```

Run summaries are written under `training_runs/` and updated after every completed
generation.

## Run Focused Checks

```bash
python3 test_training_config.py
python3 test_training_data.py
python3 test_training_overlap.py
python3 test_training_runner.py
python3 test_training_parallel.py
python3 test_training_ui.py
python3 test_training_cli.py
python3 test_training_records.py
python3 test_training_replay.py
python3 test_training_performance.py
```

The performance check compares a bounded workload with one worker and multiple workers.
Acceptance requires equivalent fitness values and ranking, plus at least 30% lower
elapsed time with multiple workers on a multi-core target machine.

Initial implementation benchmark on the target development machine:

```text
single=0.935s parallel=0.543s workers=2 speedup=41.9% target=30.0%
```

## Normal Game Mode

```bash
python3 run_bot.py
```

Normal game mode remains separate and does not initialize datasets, process workers, or
training records.
