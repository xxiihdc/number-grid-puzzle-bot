# Tasks: Optimize Training Workflow

**Input**: Design documents from `/specs/004-optimize-training-workflow/`

**Prerequisites**: plan.md, spec.md, research.md, data-model.md, contracts/

**Tests**: Included because the project constitution requires a test-first approach and
the implementation plan defines focused executable test scripts.

**Organization**: Tasks are grouped by user story so each story can be implemented and
validated as an independent increment.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel because it changes a different file and does not depend on
  another incomplete task in the same phase.
- **[Story]**: Maps the task to one user story from spec.md.
- Every task includes the exact file path to change.

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Create the offline-training directories and keep generated experiment files
out of version control.

- [x] T001 Create tracked placeholder files in `training_data/.gitkeep` and `training_runs/.gitkeep`
- [x] T002 Update `.gitignore` to ignore generated `training_data/*.json` datasets and `training_runs/*.json` summaries while preserving `.gitkeep` files
- [x] T003 Create the tracked scripts-directory placeholder in `scripts/.gitkeep`

---

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Add validated shared models and serialization primitives required by every
user story.

**CRITICAL**: No user story work begins until this phase is complete.

### Tests

- [x] T004 [P] Write failing validation tests for numeric ranges, derived elite and injection counts, tournament size, and dataset capacity in `tests/test_training_config.py`
- [x] T005 [P] Write failing schema-validation tests for valid and malformed seed datasets in `tests/test_training_data.py`

### Implementation

- [x] T006 Implement the `TrainingConfig` dataclass, legacy-compatible defaults, derived counts, and field-level validation errors in `bot/training_config.py`
- [x] T007 Implement `GameplayScenario` and `SeedDataset` dataclasses, canonical checksum helpers, JSON loading, and structural validation in `bot/training_data.py`
- [x] T008 Extend `tests/test_training_config.py` to verify dataset-aware validation through the public `TrainingConfig` validation API
- [x] T009 Run `python3 tests/test_training_config.py` and `python3 tests/test_training_data.py` to verify the foundational model checks pass

**Checkpoint**: Configuration and persisted scenario files can be validated before any
training workload starts.

---

## Phase 3: User Story 1 - Evaluate Training Candidates Efficiently and Fairly (Priority: P1) MVP

**Goal**: Replace placeholder fitness with deterministic completed-game simulation and
evaluate genomes across a configurable number of local process workers.

**Independent Test**: Evaluate the same bounded population and scenarios once with one
worker and once with multiple workers; verify completed 27-turn scores, identical fitness
values and ranking, and one returned result per genome.

### Tests for User Story 1

- [x] T010 [P] [US1] Write failing tests for deterministic 27-turn simulation, stable tie-breaking, trimmed-mean fitness, variance penalty, and absence of synthetic noise in `tests/test_training_runner.py`
- [x] T011 [P] [US1] Write failing tests that compare single-worker and multi-worker candidate fitness values and ranking in `tests/test_training_parallel.py`
- [x] T012 [P] [US1] Write the bounded one-worker versus multi-worker benchmark and 30% acceptance report in `tests/benchmarks/test_training_performance.py`

### Implementation for User Story 1

- [x] T013 [US1] Add chromosome payload serialization and reconstruction helpers for process-boundary evaluation in `bot/genetics.py`
- [x] T014 [US1] Implement deterministic one-ply slot ranking and completed 27-turn scenario simulation using `GameState`, `FeaturePool`, and stable aligned-slot order in `bot/training_runner.py`
- [x] T015 [US1] Implement `CandidateEvaluation` calculation with scenario scores, fixed 10% tail trimming, population standard deviation, and configured variance penalty in `bot/training_runner.py`
- [x] T016 [US1] Implement worker initialization that loads the immutable scenario subset once per process and evaluates one serialized genome per task in `bot/training_runner.py`
- [x] T017 [US1] Implement generation evaluation with configurable worker count, a direct single-worker baseline path, complete-result validation, and explicit worker-failure propagation in `bot/training_runner.py`
- [x] T018 [US1] Replace placeholder seed loops and Gaussian-noise fitness in `bot/genetics.py` with the generation evaluator from `bot/training_runner.py`
- [x] T019 [US1] Run `python3 tests/test_training_runner.py`, `python3 tests/test_training_parallel.py`, and `python3 tests/benchmarks/test_training_performance.py` to verify deterministic equivalence and measure local multi-worker speedup

**Checkpoint**: User Story 1 is independently functional. Training fitness now reflects
completed games and can use multiple CPU workers without changing results.

---

## Phase 4: User Story 2 - Generate Reproducible Seed Datasets (Priority: P2)

**Goal**: Generate named, reusable CRN datasets from a master seed and detect accidental
overlap between training and validation scenarios.

**Independent Test**: Generate two datasets from identical inputs, compare their scenario
content and checksums, load them for evaluation, and verify overlap reporting against a
separate validation dataset.

### Tests for User Story 2

- [x] T020 [P] [US2] Write failing tests for deterministic generation, schema metadata, checksums, allowed block values, and overwrite protection in `tests/test_training_data.py`
- [x] T021 [P] [US2] Write failing tests for partial and complete training-validation scenario overlap reports in `tests/test_training_overlap.py`

### Implementation for User Story 2

- [x] T022 [US2] Implement local-RNG scenario generation, dataset metadata creation, checksum persistence, overwrite protection, and JSON saving in `bot/training_data.py`
- [x] T023 [US2] Implement scenario-checksum overlap detection between training and validation datasets in `bot/training_data.py`
- [x] T024 [US2] Implement the documented `--dataset-id`, `--purpose`, `--master-seed`, `--scenarios`, `--output`, and explicit overwrite flags in `scripts/generate_training_seeds.py`
- [x] T025 [US2] Run `python3 tests/test_training_data.py`, `python3 tests/test_training_overlap.py`, and generate temporary training and validation datasets with `scripts/generate_training_seeds.py`

**Checkpoint**: User Story 2 is independently functional. Developers can persist,
validate, reuse, and compare deterministic scenario datasets.

---

## Phase 5: User Story 3 - Configure Training Through an Interactive Interface (Priority: P3)

**Goal**: Let developers configure and start training locally without editing source
code, using terminal prompts or scriptable CLI flags.

**Independent Test**: Configure a short run through the terminal interface and through
non-interactive flags; verify both paths produce the same validated configuration and
invalid inputs do not start training.

### Tests for User Story 3

- [x] T026 [P] [US3] Write failing tests for prompt defaults, corrected invalid values, dataset selection, confirmation, and cancellation in `tests/test_training_ui.py`
- [x] T027 [P] [US3] Write failing CLI parsing tests for interactive mode, `--non-interactive`, all documented GA flags, missing required values, and normal play dispatch in `tests/test_training_cli.py`

### Implementation for User Story 3

- [x] T028 [US3] Implement terminal prompts, available-dataset display, field descriptions, validation feedback, derived-count preview, and explicit confirmation in `bot/training_ui.py`
- [x] T029 [US3] Replace the incomplete training argument forwarding with the documented train-mode flags and a shared `TrainingConfig` construction path in `bot/cli.py`
- [x] T030 [US3] Update `run_bot.py` and `bot/main.py` so play mode remains isolated while train mode opens the UI or accepts non-interactive configuration and invokes the offline runner
- [x] T031 [US3] Run `python3 tests/test_training_ui.py`, `python3 tests/test_training_cli.py`, and `python3 tests/test_bot.py` to verify configuration workflows and play-mode isolation

**Checkpoint**: User Story 3 is independently functional. Training experiments can be
configured interactively or scripted without source edits.

---

## Phase 6: User Story 4 - Inspect and Reproduce Training Runs (Priority: P4)

**Goal**: Persist progress and best candidates so completed, failed, and interrupted
training workloads can be audited and reproduced.

**Independent Test**: Run a short experiment, inspect its JSON summary, rerun evaluation
from the recorded inputs, and verify matching candidate fitness results. Interrupt
another short run and verify its best available candidate remains recorded.

### Tests for User Story 4

- [x] T032 [P] [US4] Write failing tests for initial, per-generation, completed, failed, and interrupted JSON summary states in `tests/test_training_records.py`
- [x] T033 [P] [US4] Write failing replay tests that reconstruct evaluation inputs from a saved run summary and reproduce candidate fitness values in `tests/test_training_replay.py`

### Implementation for User Story 4

- [x] T034 [US4] Implement versioned `TrainingRun` JSON summary creation, atomic updates, generation append, terminal states, dataset references, and best-chromosome persistence in `bot/training_runner.py`
- [x] T035 [US4] Add generation elapsed time, best, average, and minimum fitness reporting plus final validation-dataset evaluation in `bot/training_runner.py`
- [x] T036 [US4] Add run-summary replay loading and deterministic candidate reevaluation in `bot/training_runner.py`
- [x] T037 [US4] Update `bot/main.py` to preserve an interrupted run summary on `KeyboardInterrupt` and print the summary path
- [x] T038 [US4] Run `python3 tests/test_training_records.py`, `python3 tests/test_training_replay.py`, and execute one short non-interactive training run to verify summary persistence and replay

**Checkpoint**: User Story 4 is independently functional. Each experiment leaves an
auditable summary and can be reevaluated from preserved inputs.

---

## Phase 7: Polish & Cross-Cutting Concerns

**Purpose**: Validate the complete workflow, document usage, and measure the requested
performance effect.

- [x] T039 [P] Update `README.md` with seed generation, interactive training, scripted training, run-summary replay, and focused test commands
- [x] T040 [P] Update `.gitignore` if implementation introduces additional generated training artifacts beyond the JSON files covered by T002
- [x] T041 Run `python3 tests/test_bot.py`, `python3 tests/test_display.py`, `python3 scripts/diagnostics/class_vars.py`, `python3 tests/test_training_config.py`, `python3 tests/test_training_data.py`, `python3 tests/test_training_overlap.py`, `python3 tests/test_training_runner.py`, `python3 tests/test_training_parallel.py`, `python3 tests/test_training_ui.py`, `python3 tests/test_training_cli.py`, `python3 tests/test_training_records.py`, and `python3 tests/test_training_replay.py`
- [x] T042 Run `python3 tests/benchmarks/test_training_performance.py`, record the one-worker and multi-worker elapsed times in `specs/004-optimize-training-workflow/quickstart.md`, and report whether the 30% speedup criterion passes on the target machine
- [x] T043 Validate every command in `specs/004-optimize-training-workflow/quickstart.md` against the implemented CLI and correct any stale examples

---

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies.
- **Foundational (Phase 2)**: Depends on Setup and blocks all user stories.
- **User Story 1 (Phase 3)**: Depends on Foundational and delivers the MVP.
- **User Story 2 (Phase 4)**: Depends on Foundational. It can be implemented alongside
  US1 after the shared loader exists.
- **User Story 3 (Phase 5)**: Depends on Foundational and uses US2 dataset discovery plus
  the US1 offline runner when starting a real workload.
- **User Story 4 (Phase 6)**: Depends on the US1 runner and US2 persisted dataset
  references. It can begin before US3 is complete.
- **Polish (Phase 7)**: Depends on all selected user stories.

### User Story Dependencies

- **User Story 1 (P1)**: Starts after Foundational. No other user story dependency.
- **User Story 2 (P2)**: Starts after Foundational. No other user story dependency.
- **User Story 3 (P3)**: Integrates US1 and US2 but its prompt and parser tests can begin
  after Foundational.
- **User Story 4 (P4)**: Integrates US1 and US2 but does not depend on US3.

### Within Each User Story

- Write tests first and confirm they fail for the expected missing behavior.
- Implement models and pure helpers before orchestration.
- Complete-result validation precedes integration with GA evolution.
- Run the focused story tests at each checkpoint.

### Parallel Opportunities

- T004 and T005 can run in parallel.
- T010, T011, and T012 can run in parallel.
- T020 and T021 can run in parallel.
- T026 and T027 can run in parallel.
- T032 and T033 can run in parallel.
- After Foundational completes, US1 and US2 can proceed in parallel.
- US3 prompt and parser tests can begin while US1 and US2 implementations finish.
- US4 can proceed while US3 integration is in progress.

---

## Parallel Example: User Story 1

```text
Task T010: Write deterministic simulation and fitness tests in tests/test_training_runner.py
Task T011: Write worker-count equivalence tests in tests/test_training_parallel.py
Task T012: Write bounded speedup benchmark in tests/benchmarks/test_training_performance.py
```

## Parallel Example: User Story 2

```text
Task T020: Write deterministic dataset generation tests in tests/test_training_data.py
Task T021: Write overlap-report tests in tests/test_training_overlap.py
```

## Parallel Example: User Story 3

```text
Task T026: Write terminal prompt tests in tests/test_training_ui.py
Task T027: Write train-mode CLI parsing tests in tests/test_training_cli.py
```

## Parallel Example: User Story 4

```text
Task T032: Write run-summary state tests in tests/test_training_records.py
Task T033: Write run-summary replay tests in tests/test_training_replay.py
```

---

## Implementation Strategy

### MVP First

1. Complete Phase 1: Setup.
2. Complete Phase 2: Foundational shared models.
3. Complete Phase 3: User Story 1.
4. Run deterministic and worker-count equivalence checks.
5. Measure the local speedup before expanding the workflow.

### Incremental Delivery

1. Setup + Foundational: validated config and dataset loader.
2. User Story 1: meaningful deterministic full-game fitness with local multi-core
   evaluation.
3. User Story 2: persisted reproducible datasets and overlap reporting.
4. User Story 3: interactive and scripted configuration.
5. User Story 4: incremental run records and replay.
6. Polish: full regression suite, docs, quickstart verification, and benchmark report.

### Parallel Team Strategy

1. Complete Setup and Foundational together.
2. Implement US1 runner and US2 dataset generator in parallel.
3. Start US3 UI/parser tests while runner and generator integration finishes.
4. Implement US4 run records alongside US3 integration.
5. Finish with the full regression and benchmark pass.

---

## Notes

- `[P]` tasks modify different files or can be developed independently.
- `[US1]` through `[US4]` map directly to prioritized user stories in `spec.md`.
- Generated datasets and run summaries are local experiment artifacts, not committed
  fixtures unless a later task explicitly adds a small test fixture.
- Full-game training fitness must remain deterministic across worker counts.
- Commit after each task or coherent task group.
