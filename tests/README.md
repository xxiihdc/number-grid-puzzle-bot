# Test Layout

The repository keeps executable regression checks under `tests/`. Run them directly
from the repository root, for example:

```sh
python3 tests/test_bot.py
python3 tests/test_training_runner.py
```

The `tests/benchmarks/` directory contains bounded performance gates and local timing
reports. These are intentionally separate because they are slower and more sensitive
to host load:

```sh
python3 tests/benchmarks/test_performance.py
python3 tests/benchmarks/test_training_feature_performance.py
python3 tests/benchmarks/test_training_performance.py
```

Manual diagnostics that do not assert application behavior live under
`scripts/diagnostics/`.
