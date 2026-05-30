# Tasks: Improve Training Plateau Signals

**Input**: Design documents from `/specs/005-training-plateau-features/`

**Tests**: Included because the constitution requires test-first algorithm changes.

## Phase 1: User Story 1 - Evolve Useful Line Opportunity Features (Priority: P1)

**Independent Test**: Controlled boards report exact generalized line-window metrics.

- [x] T001 [P] [US1] Add controlled-board line-window feature tests in `test_training_features.py`
- [x] T002 [US1] Implement shared four-direction line-window extraction and four new pool features in `bot/features.py`
- [x] T003 [US1] Run `python3 test_training_features.py` and `python3 test_bot.py`

## Phase 2: User Story 3 - Continue From Older Chromosomes (Priority: P3)

**Independent Test**: A legacy 15-feature chromosome loads into the expanded pool with
neutral appended genes and evaluates without index errors.

- [x] T004 [P] [US3] Add legacy chromosome expansion and oversized rejection tests in `test_training_weights.py`
- [x] T005 [US3] Add chromosome feature-count normalization and integrate it with loading and optimizer startup in `bot/genetics.py`, `bot/training_weights.py`, and `bot/training_runner.py`
- [x] T006 [US3] Run `python3 test_training_weights.py` and `python3 test_training_replay.py`

## Phase 3: User Story 2 - Inspect Plateau Diagnostics (Priority: P2)

**Independent Test**: Every completed generation summary reports population diversity,
active-gene statistics, no-improvement streak, and surge state.

- [x] T007 [P] [US2] Add generation diagnostics persistence tests in `test_training_records.py`
- [x] T008 [P] [US2] Extend backward-compatible chart-series tests in `test_training_plot.py`
- [x] T009 [US2] Implement population diagnostics and persist them per generation in `bot/genetics.py` and `bot/training_runner.py`
- [x] T010 [US2] Load optional plateau diagnostics in `scripts/plot_training_log.py`
- [x] T011 [US2] Run `python3 test_training_records.py` and `python3 test_training_plot.py`

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T012 [P] Add bounded extraction benchmark in `test_training_feature_performance.py`
- [x] T013 Update heuristic feature documentation in `README.md`
- [x] T014 Run focused regression checks: `python3 test_training_features.py`, `python3 test_training_weights.py`, `python3 test_training_records.py`, `python3 test_training_replay.py`, `python3 test_training_parallel.py`, `python3 test_training_plot.py`, `python3 test_bot.py`, and `python3 test_training_feature_performance.py`
- [x] T015 Record benchmark result and plateau explanation in `specs/005-training-plateau-features/quickstart.md`
- [x] T016 Add validation-dataset replay support for interrupted best chromosomes in `bot/cli.py`, `bot/training_runner.py`, `test_training_cli.py`, and `test_training_replay.py`
- [x] T017 Replace continuous adaptive mutation surge with cooldown pulses in `bot/genetics.py` and add policy checks in `test_training_mutation.py`
- [x] T018 Replay the interrupted `578.6131` best against its full validation dataset and record the result in `specs/005-training-plateau-features/quickstart.md`

## Dependencies & Execution Order

- User Story 1 adds the pool features before migration checks can validate the expanded size.
- User Story 3 normalization must complete before warm-start training uses the new pool.
- User Story 2 diagnostics can be implemented after chromosome structure is stable.
- Benchmark and regression checks run after all implementation tasks.

## Parallel Opportunities

- T001, T004, T007, and T008 affect separate test files.
- T012 and T013 affect separate files after implementation is stable.

## Implementation Strategy

Deliver P1 first so GA chromosomes gain stronger opportunity signals. Add migration next
to protect the existing promoted model, then add diagnostics so future plateau analysis
is evidence-based.
