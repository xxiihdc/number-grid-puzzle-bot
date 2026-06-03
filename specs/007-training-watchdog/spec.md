# Feature Specification: Training Watchdog

**Feature Branch**: `007-training-watchdog`

**Created**: 2026-06-03

**Status**: Draft

**Input**: User description: "hãy dùng speckit, để viết 1 trình dạng watch dog, theo dõi log khi training, khi thấy training không hiệu quả thì dừng"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Stop Ineffective Training (Priority: P1)

A developer starts a long offline GA training run and wants the system to stop automatically when the run is no longer producing meaningful improvement.

**Why this priority**: Long GA runs consume CPU. The project already records plateau diagnostics, so automatic stopping prevents wasting time after the optimizer has stopped improving.

**Independent Test**: Run a deterministic training workload with watchdog thresholds that force a plateau stop and verify the summary ends as completed with an explicit watchdog stop reason.

**Acceptance Scenarios**:

1. **Given** a training run with watchdog enabled, **When** the best fitness has not improved for the configured patience window after at least one mutation pulse, **Then** training stops before max generations.
2. **Given** a training run stops by watchdog, **When** the JSON summary is inspected, **Then** it contains the completed generations, best chromosome, best fitness, and a watchdog stop reason.

---

### User Story 2 - Configure Watchdog Strictness (Priority: P2)

A developer can tune watchdog sensitivity from the CLI without editing source code.

**Why this priority**: Different experiments need different patience and minimum improvement thresholds depending on dataset size and mutation policy.

**Independent Test**: Parse CLI training flags and verify the resulting training config carries the watchdog settings.

**Acceptance Scenarios**:

1. **Given** a scripted training command, **When** watchdog flags are supplied, **Then** the config stores the requested patience, minimum improvement, and average-recovery settings.
2. **Given** watchdog is disabled, **When** training reaches the configured generation limit, **Then** the stop reason remains max generations.

---

### User Story 3 - Document Operations (Priority: P3)

A developer can read the canonical whitepaper to understand how the watchdog decides to stop training and which fields appear in logs.

**Why this priority**: The whitepaper is the canonical project manual and must stay aligned with new commands, parameters, and log behavior.

**Independent Test**: Inspect `WHITEPAPER.md` and verify the new CLI flags, stop reason, and recommended usage are documented bilingually.

**Acceptance Scenarios**:

1. **Given** the watchdog feature is implemented, **When** the whitepaper is reviewed, **Then** it documents all new training flags and the watchdog stop reason.

### Edge Cases

- The first generations should not stop before enough history exists to compare improvement and average recovery.
- A run that improves by exactly the configured minimum improvement should reset the no-improvement streak.
- The watchdog should not trigger solely because a generation has low diversity if there is still recent meaningful improvement.
- Interrupted and failed runs should preserve their existing statuses and not be relabeled as watchdog stops.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The system MUST provide a training watchdog that evaluates completed generation summaries during a run.
- **FR-002**: The watchdog MUST be configurable with enablement, patience, minimum improvement, minimum generations, and average-recovery threshold.
- **FR-003**: The watchdog MUST stop only after a completed generation has been written to the run summary.
- **FR-004**: A watchdog stop MUST preserve the best chromosome and best fitness found so far.
- **FR-005**: A watchdog stop MUST write `status = "completed"` and a distinct `stop_reason` indicating watchdog termination.
- **FR-006**: The CLI MUST expose watchdog settings for non-interactive training.
- **FR-007**: Default behavior MUST keep training bounded by `--generations` while enabling early stop with conservative defaults.
- **FR-008**: Existing summaries without watchdog fields MUST remain readable by replay and analysis tools.
- **FR-009**: `WHITEPAPER.md` MUST document the new parameters, log semantics, and operational guidance.

### Key Entities *(include if feature involves data)*

- **Training Watchdog Configuration**: Enablement and thresholds controlling early stopping decisions.
- **Watchdog Decision**: Per-generation result explaining whether training continues or stops and why.
- **Training Run Summary**: Existing JSON record extended by stop reasons and config fields.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: A deterministic plateau test stops before the configured maximum generation count.
- **SC-002**: 100% of watchdog stops preserve a best chromosome and best fitness in the summary.
- **SC-003**: CLI parsing covers every watchdog flag with field-level assertions.
- **SC-004**: Documentation lists all watchdog flags and the `watchdog_plateau` stop reason in English and Vietnamese.

## Assumptions

- The watchdog runs inside `run_training` after each generation instead of as an external process killer.
- A run stopped by watchdog is considered successfully completed because it ends intentionally with usable best weights.
- Conservative defaults should avoid stopping before at least one adaptive mutation surge has had a chance to affect evolution.
