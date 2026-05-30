# Implementation Plan: Improve Training Plateau Signals

**Branch**: `005-training-plateau-features` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)

## Summary

Expand the heuristic pool with four generalized three-cell line-window features, preserve
older promoted chromosomes by appending disabled neutral genes, and persist generation-
level plateau diagnostics. Keep fitness deterministic and measure feature-extraction cost
with a bounded benchmark.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: NumPy; Python standard library (`dataclasses`, `json`, `time`)

**Storage**: Existing JSON training summaries and active chromosome files

**Testing**: Existing executable Python checks plus `test_training_features.py` and
`test_training_feature_performance.py`

**Target Platform**: Local offline training on macOS or Linux

**Project Type**: Python CLI game bot with offline GA training

**Performance Goals**: Added extraction remains bounded for offline one-ply training;
single-worker and multi-worker evaluation stay equivalent

**Constraints**: Preserve phase masks, deterministic CRN evaluation, existing summary
readability, and inference behavior for migrated chromosomes until new genes evolve

## Constitution Check

- **Mathematical Rigor**: PASS. Added signals count exact length-three scoring windows.
- **Algorithmic Efficiency**: PASS. One shared bounded board scan derives all four signals.
- **Adaptive Phased Strategies**: PASS. New genes use existing per-phase masks and weights.
- **Automated Feature Discovery**: PASS. New genes start disabled and GA mutation selects them.
- **Genetic Algorithm Optimization**: PASS. Diversity and surge metrics expose convergence.
- **Separation of Concerns**: PASS. Training diagnostics do not alter runtime learning.
- **Action Space Reduction**: PASS. Placement action space is unchanged.

## Project Structure

```text
bot/features.py                       # line-window feature extraction
bot/genetics.py                       # chromosome normalization and diagnostics
bot/training_runner.py                # persisted generation diagnostics
scripts/plot_training_log.py          # optional diagnostics loading
test_training_features.py             # controlled-board checks
test_training_feature_performance.py  # bounded extraction benchmark
test_training_records.py              # summary diagnostics checks
test_training_weights.py              # older chromosome migration checks
```

## Complexity Tracking

No constitution violations require justification.
