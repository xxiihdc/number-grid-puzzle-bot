# Implementation Plan: Training Watchdog

**Branch**: `007-training-watchdog` | **Date**: 2026-06-03 | **Spec**: [spec.md](spec.md)

**Input**: Feature specification from `/specs/007-training-watchdog/spec.md`

## Summary

Add a configurable training watchdog that evaluates completed GA generation summaries and ends training early when plateau evidence shows the run is no longer effective. The implementation extends training config and CLI flags, adds focused tests, preserves incremental summaries, and documents the new workflow in `WHITEPAPER.md`.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: Standard library, existing `bot.training_runner`, `bot.training_config`, `bot.cli`, and `bot.genetics`

**Storage**: Existing JSON run summaries under `training_runs/`

**Testing**: Existing script-style Python tests in `tests/`

**Target Platform**: Local CLI training on developer machines

**Project Type**: CLI and offline training engine

**Performance Goals**: O(1) watchdog decision per generation; no extra candidate evaluations

**Constraints**: Preserve deterministic GA evaluation, Common Random Numbers, existing replay compatibility, and inference/training separation

**Scale/Scope**: One training run at a time, evaluated once per completed generation

## Constitution Check

- **Mathematical Rigor**: PASS. Stop decisions are based on explicit fitness deltas, plateau streaks, mutation-pulse evidence, and average recovery.
- **Algorithmic Efficiency**: PASS. The watchdog reads already computed metrics and adds no search-loop allocations.
- **Adaptive Phased Strategies**: PASS. No inference strategy changes.
- **Automated Feature Discovery**: PASS. The watchdog controls run duration only and does not manually select features.
- **Genetic Algorithm Optimization**: PASS. The feature uses plateau diagnostics and adaptive mutation timing to avoid premature termination.
- **Separation of Concerns**: PASS. Offline training behavior changes only; runtime inference remains separate.
- **Action Space Reduction**: PASS. Game placement constraints are untouched.
- **Living Operational Documentation**: PASS. `WHITEPAPER.md` will be updated because CLI flags, stop reasons, and workflow guidance change.

## Project Structure

### Documentation (this feature)

```text
specs/007-training-watchdog/
├── spec.md
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
└── tasks.md
```

### Source Code (repository root)

```text
bot/
├── training_config.py
├── training_runner.py
└── cli.py

tests/
├── test_training_cli.py
└── test_training_records.py

WHITEPAPER.md
```

**Structure Decision**: Extend existing training configuration, runner, CLI, and focused training tests. No new package is needed because the watchdog is a small policy layer over generation summaries.

## Complexity Tracking

No constitution violations.
