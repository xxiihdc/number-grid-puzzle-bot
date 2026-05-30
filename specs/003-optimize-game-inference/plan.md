# Implementation Plan: Optimize Game Inference Performance

**Branch**: `003-optimize-game-inference` | **Date**: 2026-05-30 | **Spec**: [spec.md](./spec.md)

**Input**: Feature specification from `/specs/003-optimize-game-inference/spec.md`

## Summary

Replace the unbounded full-expansion runtime search with budgeted Expectimax. Game mode
spawns the current block before search, computes a fast valid fallback, and uses the
remaining 180-millisecond internal budget for deterministic sampled lookahead with
phase-specific target depths.

## Technical Context

**Language/Version**: Python 3.9.6

**Primary Dependencies**: NumPy; Python standard library

**Storage**: N/A; runtime state and bounded transposition table remain in memory

**Testing**: Executable Python test scripts (`test_bot.py`, `test_performance.py`)

**Target Platform**: Current development machine: macOS arm64

**Project Type**: Local CLI game bot with optional post-game visualization

**Performance Goals**: Every game-mode move selection completes within 200 milliseconds

**Constraints**: Use a 180-millisecond internal search deadline; preserve valid aligned
placements; keep training out of game-mode move selection; keep local scoring semantics
unchanged in this feature

**Scale/Scope**: 27 turns per game, at most 27 aligned slots, 10 deterministic benchmark
games covering 270 measured moves

## Constitution Check

*GATE: Must pass before Phase 0 research. Re-checked after Phase 1 design.*

### I. Mathematical Rigor
- **Status**: PASS
- **Explanation**: Search preserves the 27-slot action model and explicitly separates
  exact current-block evaluation from sampled future uncertainty.

### II. Algorithmic Efficiency
- **Status**: PASS
- **Explanation**: The design adds a deadline, bounded beam expansion, deterministic
  chance sampling, apply/undo simulation, and a bounded transposition table.

### III. Adaptive Phased Strategies
- **Status**: PASS
- **Explanation**: Opening, middlegame, and endgame retain target depths 2, 3, and 5.
  The runtime budget determines whether deeper iterations are feasible.

### IV. Automated Feature Discovery
- **Status**: PASS
- **Explanation**: Existing feature extraction and feature masking remain available.

### V. Genetic Algorithm Optimization
- **Status**: PASS
- **Explanation**: Offline training behavior is preserved and explicitly excluded from
  runtime move selection.

### VI. Separation of Concerns
- **Status**: PASS
- **Explanation**: Game mode constructs only the runtime search engine. The optimizer is
  created only when training is requested.

### VII. Action Space Reduction
- **Status**: PASS
- **Explanation**: Search considers only unused aligned slots `(x, y)` where
  `x in 0..8` and `y in {0, 3, 6}`.

## Project Structure

### Documentation (this feature)

```text
specs/003-optimize-game-inference/
├── plan.md
├── research.md
├── data-model.md
├── quickstart.md
├── spec.md
└── checklists/
    └── requirements.md
```

### Source Code (repository root)

```text
bot/
├── main.py
├── game_state.py
├── expectimax.py
├── features.py
└── genetics.py

test_bot.py
test_performance.py
```

**Structure Decision**: Extend the existing single-project bot modules. No external
contract directory is needed because this feature does not expose a network, file, or
third-party integration interface.

## Complexity Tracking

No constitution violations require justification.
