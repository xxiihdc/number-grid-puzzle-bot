# Feature Specification: Bilingual Project Whitepaper

**Feature Branch**: `006-bilingual-project-whitepaper`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Write one bilingual English-Vietnamese whitepaper or
equivalent page that introduces the project, commands, parameters, logs, and optimization
workflow. Update governance and agent guides so future features maintain the page."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Understand The Project From One Page (Priority: P1)

A developer opens one document and learns the puzzle rules, architecture, inference
strategy, offline training strategy, and generated artifacts in English and Vietnamese.

**Why this priority**: Project knowledge is currently spread across README, design notes,
spec quickstarts, source code, and agent guides.

**Independent Test**: A reader can locate the bilingual overview, architecture map, and
workflow summary without opening another document.

**Acceptance Scenarios**:

1. **Given** a new developer, **When** they open the whitepaper, **Then** they can explain
   the game objective, the 27-slot constraint, inference, and offline training.
2. **Given** a Vietnamese or English reader, **When** they inspect a major section,
   **Then** equivalent guidance is available in both languages.

---

### User Story 2 - Run And Diagnose The Bot (Priority: P2)

A developer uses the whitepaper as the operating manual for play, dataset generation,
training, replay, plotting, active-weight synchronization, known-future comparison, and
focused tests.

**Why this priority**: The repository exposes multiple commands and training parameters;
incorrect combinations waste long-running experiments.

**Independent Test**: Compare every documented command and parameter against the current
CLI parsers and confirm that log-reading guidance covers current summary fields.

**Acceptance Scenarios**:

1. **Given** a developer preparing training, **When** they read the command catalog,
   **Then** they can generate datasets and start interactive or scripted training.
2. **Given** a training summary, **When** they read the diagnostics section, **Then** they
   can interpret fitness, diversity, no-improvement streaks, and mutation pulses.
3. **Given** an interrupted run, **When** they follow the whitepaper, **Then** they can
   replay its best chromosome against training or validation data and promote weights.

---

### User Story 3 - Keep Documentation Current (Priority: P3)

A maintainer implementing a new feature is required by project governance and agent
instructions to update the whitepaper whenever commands, parameters, architecture, logs,
optimization guidance, or user-facing behavior change.

**Why this priority**: A one-page manual becomes harmful if it drifts from the code.

**Independent Test**: Inspect constitution, `CLAUDE.md`, and `AGENTS.md`; verify that each
contains an explicit whitepaper maintenance rule.

**Acceptance Scenarios**:

1. **Given** a future implementation that changes documented behavior, **When** the work
   is reviewed, **Then** whitepaper impact must be checked and applicable updates made.
2. **Given** a documentation-only or internal change with no whitepaper impact, **When**
   reviewed, **Then** maintainers may record that no whitepaper update is required.

### Edge Cases

- Commands that open graphical windows must document headless alternatives where available.
- Generated training paths and timestamps vary between runs and must be represented as placeholders.
- Historical benchmark values must be labeled as examples, not permanent guarantees.
- The whitepaper must remain navigable despite containing two languages.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: The repository MUST contain one discoverable bilingual whitepaper page.
- **FR-002**: The whitepaper MUST explain project purpose, puzzle rules, architecture,
  inference, training, heuristic features, and generated artifacts.
- **FR-003**: The whitepaper MUST document current play, dataset generation, training,
  replay, plot, sync, known-future comparison, and focused-test commands.
- **FR-004**: The whitepaper MUST document training parameters with meaning, valid range,
  and tuning guidance.
- **FR-005**: The whitepaper MUST explain how to read run summaries and diagnose plateaus.
- **FR-006**: The whitepaper MUST describe an optimization loop with reproducible
  comparisons and validation before promotion.
- **FR-007**: README MUST link prominently to the whitepaper.
- **FR-008**: The constitution MUST add a testable living-documentation requirement.
- **FR-009**: `CLAUDE.md` and `AGENTS.md` MUST require whitepaper impact review for future
  features and documentation updates when applicable.
- **FR-010**: Documentation MUST distinguish runtime inference from offline training.

### Key Entities

- **Whitepaper**: The bilingual project overview and operating manual.
- **Command Catalog**: Runnable examples and their purpose.
- **Parameter Reference**: Training controls, valid ranges, and tuning effects.
- **Documentation Impact Rule**: Governance requirement for future feature maintenance.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: One page covers 100% of the current top-level operational commands.
- **SC-002**: Every scripted training parameter exposed by the CLI is documented.
- **SC-003**: Constitution, `CLAUDE.md`, and `AGENTS.md` each contain an explicit
  whitepaper maintenance rule.
- **SC-004**: Every command example is validated against current CLI help or parser tests.
- **SC-005**: Readers can find both English and Vietnamese text for every major section.

## Assumptions

- `WHITEPAPER.md` at repository root is the single canonical project manual.
- Existing detailed specs and the original Vietnamese algorithm document remain useful
  references; the whitepaper links to them rather than replacing them.
- Bilingual content is organized as paired English and Vietnamese subsections for easy
  navigation.
