# Quick Start: Optimize Game Inference Performance

## Overview

Game mode now selects each move with a budgeted Expectimax search. The current block is
spawned before search, each move has a fast valid fallback, and deeper phase-specific
lookahead runs only while the internal 180-millisecond budget remains.

## Run a Game

```bash
python3 run_bot.py
```

Each turn prints the spawned block, selected slot, elapsed move-selection time, completed
depth, target depth, node count, cache size, timeout state, fallback state, and fallback
reason.

When fallback occurs, the search engine also appends a structured event to
`inference_performance.log`. Override the location with `BOT_INFERENCE_LOG_PATH` when
running experiments:

```bash
BOT_INFERENCE_LOG_PATH=/private/tmp/inference.log python3 run_bot.py
```

## Run Functional Checks

```bash
python3 test_bot.py
```

This validates state mutation, deterministic block placement, valid timeout fallback,
non-mutating search, and complete 27-turn packing.

## Run the Performance Gate

```bash
python3 test_performance.py
```

The benchmark runs ten fixed-seed games and measures only `search()` calls. It prints
per-move durations, the slowest move, and a final pass/fail summary. Acceptance requires
all 270 moves to be valid and each search call to finish within 200 milliseconds on the
target machine.

## Known Follow-Up

Runtime local placement scoring and final board scoring use different scales. This
feature intentionally leaves that behavior unchanged so performance work can be
measured independently from strategic scoring changes.
