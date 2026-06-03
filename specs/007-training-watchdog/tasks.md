# Tasks: Training Watchdog

**Input**: Design documents from `/specs/007-training-watchdog/`

## Phase 1: Setup

- [x] T001 Create Speckit feature artifacts in `specs/007-training-watchdog/`

## Phase 2: Foundational

- [x] T002 Add watchdog config fields and validation in `bot/training_config.py`
- [x] T003 Add watchdog decision helper in `bot/training_runner.py`

## Phase 3: User Story 1 - Stop Ineffective Training (P1)

**Goal**: Stop a plateaued run after a completed generation while preserving summary state.

**Independent Test**: Run a deterministic training test that forces a watchdog stop before max generations.

- [x] T004 [US1] Add watchdog plateau summary test in `tests/test_training_records.py`
- [x] T005 [US1] Integrate watchdog decision into `run_training` in `bot/training_runner.py`
- [x] T006 [US1] Run `python3 tests/test_training_records.py`

## Phase 4: User Story 2 - Configure Watchdog Strictness (P2)

**Goal**: Expose watchdog controls through the training CLI.

**Independent Test**: Parse CLI flags and assert config fields.

- [x] T007 [US2] Add CLI parsing assertions in `tests/test_training_cli.py`
- [x] T008 [US2] Add watchdog CLI flags and config mapping in `bot/cli.py`
- [x] T009 [US2] Run `python3 tests/test_training_cli.py`

## Phase 5: User Story 3 - Document Operations (P3)

**Goal**: Keep canonical operations documentation aligned.

**Independent Test**: Inspect whitepaper training parameter and log guidance sections.

- [x] T010 [US3] Update watchdog flags and stop reason guidance in `WHITEPAPER.md`

## Final Phase: Polish

- [x] T011 Run `python3 tests/test_training_config.py`, `python3 tests/test_training_cli.py`, and `python3 tests/test_training_records.py`
- [x] T012 Record final whitepaper impact decision in this task list: `WHITEPAPER.md` was updated because the feature changes CLI flags, stop reasons, and training operations guidance.

## Dependencies

User Story 1 depends on foundational config and decision helper. User Story 2 can proceed after config fields exist. User Story 3 depends on finalized flag names and stop reason.

## Implementation Strategy

Implement config and decision helper first, then make the runner stop intentionally, expose CLI flags, and update the whitepaper.
