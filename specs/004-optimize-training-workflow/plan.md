# Implementation Plan: Optimize Training Workflow

**Branch**: `004-optimize-training-workflow` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/004-optimize-training-workflow/spec.md`

## Summary

Replace the placeholder genetic-optimizer fitness with deterministic 27-turn game
simulation, evaluate genomes in parallel across local CPU workers, and persist reusable
Common Random Numbers datasets. Add a local terminal configuration interface with CLI
overrides for the advanced GA controls, validate all settings before work starts, and
write JSON run summaries that preserve enough information to reproduce an experiment.

## Technical Context

**Language/Version**: Python 3.9+

**Primary Dependencies**: NumPy; Python standard library (`argparse`,
`concurrent.futures`, `dataclasses`, `hashlib`, `json`, `pathlib`, `random`,
`statistics`, `time`)

**Storage**: Versioned JSON files for seed datasets and training-run summaries

**Testing**: Executable Python test scripts following the repository pattern
(`test_training_config.py`, `test_training_data.py`, `test_training_overlap.py`,
`test_training_runner.py`, `test_training_parallel.py`, `test_training_ui.py`,
`test_training_cli.py`, `test_training_records.py`, `test_training_replay.py`,
`test_training_performance.py`)

**Target Platform**: Local macOS or Linux development machine with one or more CPU
cores; offline operation

**Project Type**: Local CLI game bot with an interactive terminal training interface

**Performance Goals**: A fixed multi-genome evaluation workload completes at least 30%
faster with two or more workers than with one worker on a multi-core target machine

**Constraints**: Fitness must use deterministic completed 27-turn games; every genome
in a comparable run must receive the same scenarios; single-worker and multi-worker
fitness values and ranking must match; normal game mode must not initialize training
components

**Scale/Scope**: Default `50` genomes for up to `100` generations, `40` training games
per genome per generation, 27 blocks per game, configurable local worker count, one
training dataset and one validation dataset per run

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### I. Mathematical Rigor
- **Status**: PASS
- **Explanation**: Common Random Numbers compare genomes against identical deterministic
  scenarios. Fitness uses completed games and explicitly records a variance penalty.

### II. Algorithmic Efficiency
- **Status**: PASS
- **Explanation**: Independent genome evaluations are distributed across process
  workers. Each worker loads the selected scenarios once and reuses existing compact
  game state and local placement scoring.

### III. Adaptive Phased Strategies
- **Status**: PASS
- **Explanation**: Existing phase-based chromosomes remain the heuristic representation.
  Runtime game mode retains its phase-specific search depths. Offline fitness uses a
  deterministic one-ply policy so fitness does not depend on wall-clock timing.

### IV. Automated Feature Discovery
- **Status**: PASS
- **Explanation**: Existing phase-based feature masks and evolved weights remain part of
  each chromosome and are exercised by every simulated game.

### V. Genetic Algorithm Optimization
- **Status**: PASS
- **Explanation**: The design exposes population size, generations, games per genome,
  mutation rate, elite ratio, tournament size, injection ratio, variance penalty, and
  reproducibility seed. Common Random Numbers and validation datasets reduce noise and
  expose overfitting.

### VI. Separation of Concerns
- **Status**: PASS
- **Explanation**: Dataset generation, training UI, worker evaluation, and run records
  remain offline modules. Game mode imports none of them unless training is requested.

### VII. Action Space Reduction
- **Status**: PASS
- **Explanation**: Every simulated turn evaluates only currently unused aligned slots
  where `x in 0..8` and `y in {0, 3, 6}`.

### Post-Design Re-check

All gates remain PASS. The file contracts, data model, and CLI design keep training
offline, preserve deterministic CRN comparisons, and avoid changes to runtime puzzle
rules.

## Project Structure

### Documentation (this feature)

```text
specs/004-optimize-training-workflow/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── contracts/
│   ├── training-cli.md
│   └── training-files.md
├── spec.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
bot/
├── main.py                  # Dispatch play mode and training mode
├── cli.py                   # Parse training commands and CLI overrides
├── genetics.py              # Chromosomes and GA evolution
├── training_config.py       # Validated GA configuration
├── training_data.py         # Seed dataset generation, loading, validation
├── training_runner.py       # Full-game fitness, process workers, run records
├── training_ui.py           # Interactive terminal configuration interface
├── expectimax.py
├── features.py
└── game_state.py

scripts/
└── generate_training_seeds.py

training_data/
└── .gitkeep

training_runs/
└── .gitkeep

run_bot.py
test_training_config.py
test_training_data.py
test_training_overlap.py
test_training_runner.py
test_training_parallel.py
test_training_ui.py
test_training_cli.py
test_training_records.py
test_training_replay.py
test_training_performance.py
```

**Structure Decision**: Extend the existing single-project Python CLI. Keep GA evolution
in `bot/genetics.py`, but move configuration, persisted datasets, orchestration, and
interactive input into focused offline modules. Generated JSON files live under
`training_data/` and `training_runs/`; repository placeholders may be tracked while
experiment output is ignored.

## Complexity Tracking

No constitution violations require justification.
