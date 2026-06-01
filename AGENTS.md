# Codex Development Guide

## Scope
These instructions apply to the entire repository.

## Project Overview
This repository implements an AI bot for the Number Grid Puzzle game. The game uses a 9x9 grid and runs for exactly 27 turns. Each turn places one 3x1 vertical block containing random numbers from `{7, 8, 9, 10}`. The goal is to maximize score by forming continuous horizontal, vertical, or diagonal lines of 3 or more identical numbers.

## Game Rules and Constraints
- Grid coordinates range from `(0, 0)` to `(8, 8)`.
- The game has exactly 27 turns, filling all 81 cells with 27 vertical 3-cell blocks.
- Blocks are fixed-orientation 3x1 vertical pieces.
- Valid aligned slots use any column `x` from `0..8` and row `y` from `{0, 3, 6}`.
- The effective action space is exactly 27 slots per move.
- Avoid placements that create isolated 1-2 cell gaps; they violate the perfect-packing constraint.
- Scored cells remain on the board and can participate in later scores.

## Architecture
- `bot/game_state.py`: state representation and game mechanics.
- `bot/expectimax.py`: real-time move search.
- `bot/features.py`: heuristic feature extraction.
- `bot/genetics.py`: offline heuristic optimization.
- `bot/main.py` and `run_bot.py`: CLI entry points.
- `utils/display.py`: board and score display helpers.
- `ref/`: legacy/reference implementations.
- `specs/`: active feature specs and implementation plans.
- `thiet_ke_thuat_toan_bot_puzzle.md`: original algorithm design document.

## Core Algorithm Requirements
- Use dynamic-depth Expectimax for inference:
  - Opening, turns 1-10: depth 2.
  - Middlegame, turns 11-20: depth 3.
  - Endgame, turns 21-27: depth 4-5 where feasible.
- Represent grids as 1D row-major arrays where `index = y * 9 + x`.
- Use local ray-casting scoring from newly placed cells instead of full-board rescans.
- Use transposition tables for repeated game states.
- Keep inference and training separate. Runtime move selection should use precomputed heuristics, not online learning.

## Heuristics and Training
- Heuristic scores follow `H(state) = sum(weight_i * feature_i(state))`.
- Preserve phase-specific heuristic behavior for opening, midgame, and endgame.
- Genetic algorithm experiments should use:
  - Common Random Numbers for fair comparisons.
  - Adaptive mutation when fitness plateaus.
  - Phase-based genomes.
  - Feature masking or automated feature selection where applicable.
- Log seeds and experiment parameters for reproducibility.

## Development Standards
- Prefer Python 3.9+.
- Use NumPy where it improves numerical clarity or performance.
- Use Numba/JIT only for genuinely performance-critical paths.
- Minimize allocations in search loops.
- Profile algorithm changes and report relevant performance effects.
- Keep changes scoped to the requested behavior.
- Do not refactor unrelated files while implementing a feature or fix.

## User Communication
- Address the user as `Đức`.
- In every final response, include a concise `Agents / Skills / Tools` section.
- List every agent, skill, and tool used for the request. Write `none` for any category
  that was not used.

## Living Whitepaper Maintenance
- Treat `WHITEPAPER.md` as the canonical bilingual project overview and operating manual.
- For every feature, fix, or refactor, review whitepaper impact.
- Update `WHITEPAPER.md` when commands, parameters, architecture, generated artifacts,
  log fields, optimization guidance, operational workflows, or user-facing behavior change.
- If no update is needed, record that decision in the feature tasks or review notes.

## Testing
- Run focused tests for the files changed.
- Useful commands:
  - `python tests/test_bot.py`
  - `python tests/test_display.py`
  - `python tests/benchmarks/test_performance.py`
  - `python run_bot.py`
  - `python run_bot.py train`
- For search or heuristic changes, add or update tests with expected move outcomes where practical.
- For display changes, verify both visible output and headless/test behavior.

## Project Principles
Follow the constitution in `.specify/memory/constitution.md`:
- Mathematical rigor.
- Algorithmic efficiency.
- Adaptive phased strategies.
- Automated feature discovery.
- Genetic algorithm optimization.
- Separation of inference and training.
- Action-space reduction.

## Active Spec
The current Speckit active plan referenced by `CLAUDE.md` is:

`specs/006-bilingual-project-whitepaper/plan.md`

Consult the related files under `specs/006-bilingual-project-whitepaper/` when working on
the canonical project manual and its maintenance governance.
