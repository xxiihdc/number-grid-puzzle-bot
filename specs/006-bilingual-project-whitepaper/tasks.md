# Tasks: Bilingual Project Whitepaper

**Input**: Design documents from `/specs/006-bilingual-project-whitepaper/`

## Phase 1: User Story 1 - Understand The Project From One Page (Priority: P1)

**Independent Test**: Read one page and locate bilingual rules, architecture, inference,
training, features, and generated artifacts.

- [x] T001 [US1] Create the canonical paired English-Vietnamese project overview in `WHITEPAPER.md`
- [x] T002 [US1] Add a prominent canonical-manual link in `README.md`

## Phase 2: User Story 2 - Run And Diagnose The Bot (Priority: P2)

**Independent Test**: Compare each documented command and training flag against current
CLI help output and confirm log guidance covers plateau diagnostics.

- [x] T003 [US2] Document commands, parameters, logs, headless usage, and optimization workflow in `WHITEPAPER.md`
- [x] T004 [US2] Validate command examples with CLI help and `python3 tests/test_training_cli.py`

## Phase 3: User Story 3 - Keep Documentation Current (Priority: P3)

**Independent Test**: Inspect governance and agent guides for explicit whitepaper impact
review requirements.

- [x] T005 [P] [US3] Amend living-documentation governance and sync impact report in `.specify/memory/constitution.md`
- [x] T006 [P] [US3] Add future whitepaper maintenance rules in `CLAUDE.md` and `AGENTS.md`
- [x] T007 [US3] Add whitepaper impact review to `.specify/templates/tasks-template.md`

## Phase 4: Polish & Cross-Cutting Concerns

- [x] T008 Run `git diff --check` and verify all Speckit checklists in `specs/006-bilingual-project-whitepaper/checklists/requirements.md`
- [x] T009 Validate links, command help, parser checks, and governance references from `specs/006-bilingual-project-whitepaper/quickstart.md`
- [x] T010 Add a bilingual glossary for training-analysis and GA terminology in `WHITEPAPER.md`
- [x] T011 Document the versioned latest-training-run analyzer handoff for downstream agents
- [x] T012 Document persisted analyzer handoffs and the no-overwrite old-log guard
- [x] T013 Organize executable checks under `tests/`, separate benchmarks under
  `tests/benchmarks/`, move manual diagnostics under `scripts/diagnostics/`, and update
  the canonical manual for the new command paths

## Dependencies & Execution Order

- T001 establishes the whitepaper before command and governance references are validated.
- T003 extends T001 with the operating manual.
- T005 and T006 can proceed in parallel after the canonical whitepaper path is fixed.
- T007 propagates the governance rule into future Speckit tasks.
- T008 and T009 run after all documentation edits.

## Implementation Strategy

Deliver the canonical manual first, then propagate its maintenance rule into governance
and agent instructions. Finish by validating every documented command surface.
