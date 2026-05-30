# Contract: Training CLI and Interactive UI

## Entry Points

### Interactive Training Configuration

```bash
python3 run_bot.py train
```

**Behavior**:
- Opens a local terminal configuration interface.
- Shows defaults, available seed datasets, and descriptions.
- Validates all values before training begins.
- Prints derived elite and injection counts.
- Requires explicit confirmation before starting the workload.

### Scripted Training

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

**Required behavior**:
- `--non-interactive` requires all settings needed to start without prompts.
- CLI values override defaults.
- Invalid settings produce actionable field-level errors and a non-zero exit status.
- Normal play remains available through `python3 run_bot.py`.

## Seed Dataset Generator

```bash
python3 scripts/generate_training_seeds.py \
  --dataset-id train-default \
  --purpose training \
  --master-seed 20260530 \
  --scenarios 100 \
  --output training_data/train-default.json
```

**Required flags**:
- `--dataset-id`
- `--purpose` with value `training` or `validation`
- `--master-seed`
- `--scenarios`
- `--output`

**Required behavior**:
- Refuses to overwrite an existing file unless an explicit overwrite flag is supplied.
- Validates the generated dataset before writing it.
- Prints dataset identity, scenario count, and checksum.
