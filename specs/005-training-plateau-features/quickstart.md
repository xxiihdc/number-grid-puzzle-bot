# Quickstart: Improve Training Plateau Signals

Run focused checks:

```sh
python3 tests/test_training_features.py
python3 tests/test_training_weights.py
python3 tests/test_training_records.py
python3 tests/test_training_parallel.py
python3 tests/test_training_plot.py
python3 tests/benchmarks/test_training_feature_performance.py
```

Inspect the recorded plateau:

```sh
python3 scripts/plot_training_log.py \
  training_runs/train-20260530T083521.294234Z.json \
  --no-ui
```

The inspected baseline reached its final global best at generation 13 of 80. A future
training run can be compared by checking whether new diagnostics show diversity collapse
and whether best fitness improves beyond the baseline under the same CRN dataset.

## Baseline Plateau

The inspected run `train-20260530T083521.294234Z` improved from `340.506362` at
generation 1 to `472.644385` at generation 13, then remained flat through generation 80.
Its validation fitness was `409.070609`. Before this feature, summaries did not preserve
population diversity or mutation-surge history, so the log could confirm the plateau but
could not distinguish feature exhaustion from premature convergence.

## Extraction Benchmark

On the local development machine, `python3 tests/benchmarks/test_training_feature_performance.py`
processed 1,000 representative midgame feature extractions in `0.3852s`, or
`0.3852 ms/state`. The bounded offline-training threshold is `5.0 ms/state`.

The multi-worker training benchmark remained healthy after expansion:
`python3 tests/benchmarks/test_training_performance.py` completed in `2.355s` with one worker and
`1.244s` with two workers, a `47.2%` speedup against the `30.0%` target.

## Validate An Interrupted Best

Replay the best chromosome from the interrupted `578.6131` run against its full
validation dataset:

```sh
python3 run_bot.py replay \
  training_runs/train-20260530T131529.939217Z.json \
  --dataset validation
```

Adaptive mutation now runs as a one-generation pulse at no-improvement streaks
`3, 7, 11, ...`. Normal mutation resumes between pulses so the population can exploit
useful descendants instead of remaining under continuous surge mutation.

The interrupted best scored `443.6211` on the full validation dataset, compared with
`409.0706` for the previous completed baseline.
