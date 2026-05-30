# Feature Specification: Improve Training Plateau Signals

**Feature Branch**: `005-training-plateau-features`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Tại sao training lại đi ngang, dùng speckit để thêm thêm feature tối ưu việc training."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Evolve Useful Line Opportunity Features (Priority: P1)

A developer trains heuristic chromosomes against deterministic scenarios and expects the
feature pool to distinguish board states that offer materially different scoring
opportunities. The pool includes generalized three-cell line-window signals for
horizontal, vertical, and both diagonal directions so the optimizer can discover useful
weights without manually forcing a strategy.

**Why this priority**: The inspected run reached its best recorded fitness at generation
13 of 80 and did not improve afterward. Existing features contain several placement-
invariant signals and incomplete directional opportunity signals, limiting the search
surface available to the optimizer.

**Independent Test**: Build controlled boards with one-match, two-match, blocked, and
multi-line completion windows in each direction; verify that the extracted values change
only when the corresponding opportunities change and remain available to chromosomes.

**Acceptance Scenarios**:

1. **Given** a board with a three-cell line window containing one placed value and two
   empty cells, **When** features are extracted, **Then** the open one-match window is
   counted.
2. **Given** a board with a three-cell line window containing two equal placed values and
   one empty cell, **When** features are extracted, **Then** the open two-match window is
   counted.
3. **Given** a board with a three-cell line window containing conflicting placed values,
   **When** features are extracted, **Then** the blocked window is counted.
4. **Given** an empty cell that would complete more than one three-cell line, **When**
   features are extracted, **Then** the multi-line completion cell is counted once.

---

### User Story 2 - Inspect Plateau Diagnostics (Priority: P2)

A developer inspects a training summary and can determine whether a flat best-fitness
curve coincided with population convergence and repeated adaptive mutation surges.

**Why this priority**: Best, average, and minimum fitness alone do not reveal whether a
plateau is caused by an exhausted feature representation or insufficient population
diversity.

**Independent Test**: Run a short deterministic training workload and verify that every
generation summary records chromosome diversity, active-feature statistics, the
no-improvement streak, and whether adaptive mutation surge is active.

**Acceptance Scenarios**:

1. **Given** a completed generation, **When** its summary is inspected, **Then** it
   includes the number of unique chromosomes and active-feature statistics.
2. **Given** at least three generations without a new global best, **When** the next
   population is evolved, **Then** the summary exposes that adaptive mutation surge is
   active for that evolution step.

---

### User Story 3 - Continue From Older Chromosomes (Priority: P3)

A developer can continue training or play using a previously promoted chromosome after
the feature pool expands. Existing genes retain their values and newly introduced
features start disabled with neutral weights until evolution selects them.

**Why this priority**: The repository already stores promoted chromosomes with the
previous feature count. Expanding the pool without migration would make warm-start
training and inference fail or silently misalign genes.

**Independent Test**: Load a serialized older chromosome into the expanded feature pool,
verify preserved legacy genes and disabled neutral appended genes, then evaluate a game
state without an index error.

**Acceptance Scenarios**:

1. **Given** a chromosome with fewer features than the current pool, **When** it is
   normalized for use, **Then** missing genes are appended as disabled neutral genes.
2. **Given** a chromosome with more features than the current pool, **When** it is
   normalized for use, **Then** the system rejects it rather than discarding data.

### Edge Cases

- Empty boards contain many open windows but no two-match completion windows.
- Completed lines are not counted as open opportunities.
- One empty cell may complete multiple windows and must only increment the multi-line
  completion-cell feature once.
- Older chromosomes may be loaded from an active model, a run summary, or a replay.
- Population diversity may be one when every chromosome is identical.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The feature pool MUST report open three-cell windows with exactly one
  placed value and two empty cells across horizontal, vertical, and both diagonal
  directions.
- **FR-002**: The feature pool MUST report open three-cell windows with exactly two equal
  placed values and one empty cell across all four scoring directions.
- **FR-003**: The feature pool MUST report three-cell windows blocked by conflicting
  placed values.
- **FR-004**: The feature pool MUST report empty cells that complete two or more scoring
  lines.
- **FR-005**: New signals MUST participate in existing phase-based feature masking and
  weight evolution.
- **FR-006**: Every generation summary MUST record unique chromosome count, chromosome
  diversity ratio, active-feature statistics, no-improvement streak, and adaptive-surge
  state.
- **FR-007**: The system MUST preserve deterministic generation evaluation across valid
  worker counts.
- **FR-008**: The system MUST normalize older chromosomes by appending disabled,
  zero-weight genes for newly added features.
- **FR-009**: The system MUST reject chromosomes with more features than the current
  feature pool.
- **FR-010**: Existing run summaries without plateau diagnostics MUST remain readable by
  the chart loader.
- **FR-011**: The implementation MUST include focused correctness tests and a bounded
  performance benchmark for feature extraction.

### Key Entities

- **Line Window**: A contiguous three-cell segment in one scoring direction with counts
  of empty cells and distinct placed values.
- **Plateau Diagnostics**: Per-generation metrics describing population diversity,
  active-feature selection, improvement streak, and mutation-surge state.
- **Normalized Chromosome**: A serialized or in-memory chromosome whose phase gene lists
  match the current feature pool size.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: Controlled-board checks cover all four scoring directions and pass for
  every added opportunity signal.
- **SC-002**: A short training run writes plateau diagnostics for 100% of completed
  generations.
- **SC-003**: A chromosome created before the pool expansion can be loaded and evaluated
  without losing its existing gene values.
- **SC-004**: Deterministic single-worker and multi-worker candidate fitness remains
  equivalent after the feature expansion.
- **SC-005**: The focused feature-extraction benchmark reports elapsed time after the
  change and the expanded extraction remains suitable for offline training.

## Assumptions

- The added signals enrich the optimizer search space; one bounded training run is not
  sufficient to prove a universal score improvement.
- Existing deterministic Common Random Numbers datasets remain the comparison basis.
- New genes start disabled and neutral to preserve previous inference behavior until
  offline evolution selects them.
- Plateau diagnostics are additive fields in run summaries and do not change fitness.
