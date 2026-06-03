# Quickstart: Training Watchdog

Run training with conservative watchdog defaults:

```bash
python3 run_bot.py train \
  --non-interactive \
  --population-size 50 \
  --generations 100 \
  --games-per-genome 40 \
  --training-dataset training_data/train-10m.json \
  --validation-dataset training_data/validation-10m.json
```

Tune the watchdog:

```bash
python3 run_bot.py train \
  --non-interactive \
  --generations 200 \
  --watchdog-patience 12 \
  --watchdog-min-delta 0.01 \
  --watchdog-min-generations 16 \
  --watchdog-average-recovery 1.0 \
  --training-dataset training_data/train-10m.json
```

Disable watchdog for a fixed-length experiment:

```bash
python3 run_bot.py train \
  --non-interactive \
  --disable-watchdog \
  --generations 40 \
  --training-dataset training_data/train-10m.json
```

Focused verification:

```bash
python3 tests/test_training_config.py
python3 tests/test_training_cli.py
python3 tests/test_training_records.py
```
