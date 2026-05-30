# Feature Specification: Optimize Training Workflow

**Feature Branch**: `004-optimize-training-workflow`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Tối ưu training: chạy đa nhân, có script tạo bộ seed dùng chung để giảm nhiễu random, và có UI cấu hình các thông số training."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evaluate Training Candidates Efficiently and Fairly (Priority: P1)

A developer runs offline heuristic training and uses the available processing capacity of the machine to evaluate candidate genomes faster. Every candidate in a comparable training run is scored against the same fixed gameplay scenarios so that random block sequences do not distort selection.

**Why this priority**: Candidate evaluation is the dominant training cost. Faster evaluation is only useful when the fitness comparison remains fair and reproducible.

**Independent Test**: Run the same bounded training workload once with one worker and once with multiple workers, then verify that both runs evaluate the same candidates against the same scenarios, produce equivalent fitness results, and that the multi-worker run completes faster on a multi-core target machine.

**Acceptance Scenarios**:

1. **Given** a training run configured with multiple workers and a valid seed dataset, **When** a generation is evaluated, **Then** candidate evaluations are distributed across the configured workers and the generation completes with one fitness result per candidate.
2. **Given** two candidates in the same training run, **When** their fitness is calculated, **Then** both candidates are evaluated against the same gameplay scenarios.
3. **Given** identical training inputs and a fixed seed dataset, **When** candidate evaluation is run with one worker and with multiple workers, **Then** the fitness results are equivalent.
4. **Given** a candidate evaluation, **When** its fitness is calculated, **Then** the score is derived from completed 27-turn game simulations rather than an empty-board or synthetic placeholder value.

---

### User Story 2 - Generate Reproducible Seed Datasets (Priority: P2)

A developer generates and stores a named dataset of random block sequences for training or validation. The same generation inputs always reproduce the same scenarios, allowing experiments to be compared over time.

**Why this priority**: Common Random Numbers reduce random noise and make training improvements measurable. Persisted datasets also allow results to be reproduced after the original run.

**Independent Test**: Generate two datasets using the same master seed and scenario count, verify that every generated block sequence matches, and confirm that the resulting dataset can be selected for a training run.

**Acceptance Scenarios**:

1. **Given** a master seed and requested scenario count, **When** a developer runs the seed dataset generator, **Then** it stores a dataset containing the requested number of scenarios and exactly 27 three-value blocks per scenario.
2. **Given** identical seed generation inputs, **When** datasets are generated independently, **Then** their scenario contents are identical.
3. **Given** a stored seed dataset, **When** a developer selects it for training, **Then** the training run records the dataset identity and uses its scenarios for every candidate.
4. **Given** separate training and validation datasets, **When** a run is configured, **Then** the system reports whether scenarios overlap so accidental validation leakage is visible.

---

### User Story 3 - Configure Training Through an Interactive Interface (Priority: P3)

A developer opens a training configuration interface, reviews the available settings, changes the desired values, selects seed datasets, and starts a run without editing source code. The configurable values include the genetic algorithm controls needed for repeated experiments, such as population size, generation count, games evaluated per candidate, mutation rate, elite ratio, tournament size, random injection ratio, variance penalty, and worker count.

**Why this priority**: Training experiments require frequent tuning. A configuration interface reduces setup errors and makes the offline optimizer usable without code changes.

**Independent Test**: Open the interface, configure a short training run with selected datasets and worker count, start it, and verify that the recorded run configuration matches the chosen values.

**Acceptance Scenarios**:

1. **Given** the training configuration interface is opened, **When** it loads, **Then** it displays current values and clear descriptions for the supported training settings, including the genetic algorithm controls.
2. **Given** a developer changes valid settings and starts training, **When** the run begins, **Then** the selected settings are applied and recorded with the run.
3. **Given** a developer enters an invalid value, **When** the configuration is submitted, **Then** the interface identifies the invalid field and does not start training until the value is corrected.
4. **Given** stored datasets are available, **When** a developer configures a run, **Then** the interface allows selection of training and validation datasets and displays their key metadata.

---

### User Story 4 - Inspect and Reproduce Training Runs (Priority: P4)

A developer can inspect the progress and outcome of a training run, identify the exact configuration and seed datasets used, and rerun the experiment later.

**Why this priority**: Optimization results are not trustworthy unless the experiment can be audited and reproduced.

**Independent Test**: Complete a short training run, inspect its recorded summary, rerun it with the recorded inputs, and verify that the same evaluation workload and fitness values are reproduced.

**Acceptance Scenarios**:

1. **Given** a training run is active, **When** a generation completes, **Then** the system reports generation progress, elapsed time, and fitness summary.
2. **Given** a training run finishes or is stopped, **When** its summary is inspected, **Then** the configuration, dataset identities, reproducibility seed, and best candidate are available.
3. **Given** a completed run summary, **When** a developer reruns the same evaluation workload, **Then** the recorded inputs are sufficient to reproduce its fitness results.

### Edge Cases

- The configured worker count is one, exceeds the available processing capacity, or is not a positive integer.
- A worker fails while evaluating a candidate or does not return a result.
- The selected dataset is missing, unreadable, empty, malformed, or contains values outside `{7, 8, 9, 10}`.
- A scenario contains fewer or more than 27 blocks, or a block contains fewer or more than three values.
- Training and validation datasets overlap partially or completely.
- The requested seed dataset name already exists.
- A training run is interrupted before all candidates in the current generation are evaluated.
- A configuration uses a population size too small for the selected elite ratio, tournament size, or random injection ratio.
- A rate or ratio setting is outside its allowed range, or the number of games evaluated per candidate is greater than the available training scenarios.
- The same experiment is rerun with a different worker count.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST support offline evaluation of training candidates using a configurable number of workers.
- **FR-002**: The system MUST evaluate every candidate in a comparable run against the same fixed set of training scenarios.
- **FR-003**: The system MUST calculate candidate fitness from completed 27-turn game simulations using the candidate's heuristic behavior.
- **FR-004**: The system MUST preserve equivalent fitness results when the same candidates, configuration, and scenarios are evaluated with different valid worker counts.
- **FR-005**: The system MUST keep offline training isolated from normal game-mode move selection.
- **FR-006**: The system MUST provide a developer-invoked seed dataset generator.
- **FR-007**: The seed dataset generator MUST accept a dataset identity, a master seed, and a scenario count.
- **FR-008**: Each generated scenario MUST contain exactly 27 blocks, and each block MUST contain exactly three values drawn from `{7, 8, 9, 10}`.
- **FR-009**: Seed dataset generation MUST be reproducible: identical generation inputs MUST produce identical scenario contents.
- **FR-010**: The system MUST store generated seed datasets for reuse in later training and validation runs.
- **FR-011**: Stored seed datasets MUST include enough metadata to identify their purpose, generation inputs, scenario count, and creation time.
- **FR-012**: The system MUST validate a selected dataset before training begins and report invalid or malformed content without starting the run.
- **FR-013**: The system MUST support separate training and validation datasets and report detected overlap between them.
- **FR-014**: The system MUST provide an interactive training configuration interface that allows a developer to review, edit, validate, and apply supported training settings without modifying source code.
- **FR-015**: The configuration interface MUST support at least: population size, generation count, games evaluated per candidate, mutation rate, elite ratio, tournament size, random injection ratio, variance penalty, training dataset, validation dataset, worker count, and reproducibility seed.
- **FR-016**: The system MUST reject invalid configurations before training begins and identify each field that requires correction.
- **FR-017**: The system MUST record the applied configuration, selected dataset identities, reproducibility seed, and progress metrics for each training run.
- **FR-018**: After each completed generation, the system MUST report elapsed time and a fitness summary containing the best and average fitness values.
- **FR-019**: When a run finishes or is interrupted, the system MUST preserve a summary containing the best available candidate and the inputs required to reproduce the evaluated workload.
- **FR-020**: The system MUST report worker failures clearly and MUST NOT silently accept an incomplete generation as a valid completed generation.
- **FR-021**: Population size, generation count, games evaluated per candidate, tournament size, and worker count MUST be configurable as positive whole numbers.
- **FR-022**: Mutation rate, elite ratio, and random injection ratio MUST be configurable as values from `0` through `1`, and variance penalty MUST be configurable as a non-negative value.
- **FR-023**: The system MUST reject a tournament size greater than the configured population size.
- **FR-024**: The system MUST reject a games-evaluated-per-candidate value greater than the number of scenarios available in the selected training dataset.
- **FR-025**: For each generation, the system MUST derive the number of preserved elite candidates and randomly injected candidates from the configured population size and their respective ratios, and MUST report the derived counts before training begins.

### Key Entities

- **Seed Dataset**: A named, reusable collection of gameplay scenarios with purpose, master seed, scenario count, creation time, and content identity.
- **Gameplay Scenario**: A deterministic sequence of exactly 27 blocks used to evaluate one complete game.
- **Training Configuration**: The validated settings applied to an offline optimization run, including population size, generation count, games evaluated per candidate, mutation rate, elite ratio, tournament size, random injection ratio, variance penalty, scenario selection, worker count, and reproducibility seed.
- **Training Run**: One recorded optimization experiment with configuration, selected datasets, generation progress, outcome, and reproducibility information.
- **Candidate Evaluation**: The fitness result for one candidate across the fixed scenarios assigned to a comparable run.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: For a bounded evaluation workload on a multi-core target machine, using at least two workers reduces candidate evaluation elapsed time by at least 30% compared with one worker.
- **SC-002**: For identical candidates, configuration, and seed datasets, single-worker and multi-worker evaluation runs produce equivalent candidate fitness values and ranking.
- **SC-003**: 100% of generated scenarios contain exactly 27 blocks, and 100% of generated blocks contain exactly three allowed values.
- **SC-004**: Generating datasets twice with the same dataset parameters produces identical scenario contents in 100% of compared cases.
- **SC-005**: A developer can configure and start a valid short training run through the interactive interface in under 3 minutes without editing source code.
- **SC-006**: 100% of invalid configurations and malformed selected datasets are rejected before candidate evaluation begins with an actionable error message.
- **SC-007**: Every completed or interrupted training run records the applied settings, dataset identities, reproducibility seed, progress metrics, and best available candidate.
- **SC-008**: A developer can rerun a recorded evaluation workload and reproduce its candidate fitness results using only the preserved run summary and referenced datasets.

## Assumptions

- The feature targets local offline experimentation by developers, not remote multi-machine distributed training.
- The configuration interface is a local interactive interface; a browser-based interface is not required for the first version.
- A worker count of one remains supported as a reproducibility baseline and fallback.
- The default training dataset and validation dataset are distinct persisted datasets.
- Fitness comparisons within one experiment use Common Random Numbers: every candidate receives the same scenarios.
- Validation evaluation is used to measure generalization and is not used to evolve the population.
- Existing puzzle rules remain unchanged: 9x9 grid, 27 turns, aligned vertical three-cell blocks, and values from `{7, 8, 9, 10}`.
- Advanced training behavior already required by the project constitution, including adaptive mutation, phase-based genomes, and feature masking, remains in scope for configuration and reporting where applicable.
- The initial configuration interface may use the current advanced trainer defaults as starting values: population size `50`, generations `100`, games evaluated per candidate `40`, mutation rate `0.20`, elite ratio `0.10`, tournament size `5`, random injection ratio `0.10`, and variance penalty `0.15`.
