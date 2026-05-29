# Tasks: Post-Game Score Visualization

**Input**: Design documents from `/specs/002-post-game-score-display/`

**Prerequisites**: plan.md (required), spec.md (required for user stories), research.md, data-model.md, contracts/

**Tests**: The examples below include test tasks. Tests are OPTIONAL - only include them if explicitly requested in the feature specification.

**Organization**: Tasks are grouped by user story to enable independent implementation and testing of each story.

## Format: `[ID] [P?] [Story] Description`

- **[P]**: Can run in parallel (different files, no dependencies)
- **[Story]**: Which user story this task belongs to (e.g., US1, US2, US3)
- Include exact file paths in descriptions

## Path Conventions

- **Single project**: `src/`, `tests/` at repository root
- **Web app**: `backend/src/`, `frontend/src/`
- **Mobile**: `api/src/`, `ios/src/` or `android/src/`
- Paths shown below assume single project - adjust based on plan.md structure

<!--
  ============================================================================
  IMPORTANT: The tasks below are SAMPLE TASKS for illustration purposes only.

  The /speckit-tasks command MUST replace these with actual tasks based on:
  - User stories from spec.md (with their priorities P1, P2, P3...)
  - Feature requirements from plan.md
  - Entities from data-model.md
  - Endpoints from contracts/

  Tasks MUST be organized by user story so each story can be:
  - Implemented independently
  - Tested independently
  - Delivered as an MVP increment

  DO NOT keep these sample tasks in the generated tasks.md file.
  ============================================================================
-->

## Phase 1: Setup (Shared Infrastructure)

**Purpose**: Project initialization and basic structure

- [x] T001 Verify project structure and dependencies
- [x] T002 [P] Confirm Python 3.9+ environment
- [x] T003 [P] Verify numpy and matplotlib availability

## Phase 2: Foundational (Blocking Prerequisites)

**Purpose**: Core infrastructure that MUST be complete before ANY user story can be implemented

**⚠️ CRITICAL**: No user story work can begin until this phase is complete

For this feature, the foundational work is minimal since we're adding a display function to an existing codebase:
- [x] T004 Identify integration points in existing codebase (bot/main.py, ref/main.py)
- [x] T005 [P] Determine appropriate location for display function (utils/ or bot/)
- [x] T006 [P] Review existing SINGLE_MATCH_MODE flag usage
- [x] T007 [P] Establish error logging approach for headless environments

**Checkpoint**: Foundation ready - user story implementation can now begin

## Phase 3: User Story 1 - View Final Game Result (Priority: P1) 🎯 MVP

**Goal**: Provide a graphical window displaying the final game state after all 27 turns are completed, showing the game board, final score, winning streaks, and AI identification.

**Independent Test**: Run a complete game with any AI module, verify a graphical window appears after the game ends showing the grid (81 cells filled with numbers 7-10), final score, and winning streak highlights. Close the window to complete the test.

### Tests for User Story 1 (OPTIONAL - only if tests requested) ⚠️

> **NOTE: Write these tests FIRST, ensure they FAIL before implementation**

Given the nature of GUI testing and the fact that this is a visualization feature, explicit automated tests may be challenging. Manual verification is primarily recommended:
- [x] T008 [P] [US1] Create test plan for manual verification of display functionality
- [x] [P] [US1] Define test cases for different game outcomes (zero score, multiple streaks, etc.)

### Implementation for User Story 1

- [x] T009 [US1] Create display_final_game_state function in utils/display.py
- [x] T010 [US1] Implement function signature: display_final_game_state(board, score, streaks, ai_name)
- [x] T011 [US1] Implement board rendering using matplotlib (9x9 grid with numbers 7-10)
- [x] T012 [US1] Implement score display in window title/header
- [x] T013 [US1] Implement winning streak visualization with distinct color coding
- [x] T014 [US1] Implement AI name display in window
- [x] T015 [US1] Add proper window sizing and layout for readability
- [x] T016 [US1] Implement graceful error handling for headless environments (log error, return normally)
- [x] T017 [US1] Test function with sample data from ref/main.py
- [x] T018 [US1] Integrate function with existing play_game/run_single_match flow
- [x] T019 [US1] Verify display appears within 1 second of game completion
- [x] T020 [US1] Confirm window remains open until manually closed

**Checkpoint**: At this point, User Story 1 should be fully functional and testable independently

## Phase 4: User Story 2 - Distinguish Active Gameplay from Post-Game Display (Priority: P2)

**Goal**: Ensure the display function only activates after game completion in single-match mode, and remains inactive during tournament/batch mode to prevent unwanted pop-ups.

**Independent Test**: Run a tournament of multiple games; verify no graphical windows appear during gameplay. Then run a single match; verify exactly one graphical window appears after completion.

### Tests for User Story 2 (OPTIONAL - only if tests requested) ⚠️

- [x] T021 [P] [US2] Create test scenarios for both single-match and batch modes
- [x] T021A [P] [US2] Define verification steps for mode-dependent display behavior

### Implementation for User Story 2

- [x] T022 [US2] Identify where SINGLE_MATCH_MODE flag is checked in existing code
- [x] T023 [US2] Ensure display function call is gated by SINGLE_MATCH_MODE flag
- [x] T024 [US2] Test batch mode (SINGLE_MATCH_MODE = False) - verify no display windows appear
- [x] T025 [US2] Test single-match mode (SINGLE_MATCH_MODE = True) - verify display appears after game
- [x] T026 [US2] Verify no interference between modes

**Checkpoint**: At this point, User Stories 1 AND 2 should both work independently

## Phase 5: Polish & Cross-Cutting Concerns

**Purpose**: Improvements that affect multiple user stories

- [x] T027 [P] Documentation updates: clarify display function usage in code comments
- [x] [P] T028 Code cleanup and refactoring of display function if needed
- [x] [P] T029 Verify error logging works correctly in headless environments
- [x] [P] T030 Validate performance goal: display appears within 1 second of game completion
- [x] [P] T031 Run quickstart.md validation
- [x] [P] T032 Final integration testing

**Checkpoint**: All user stories complete and working together

## Dependencies & Execution Order

### Phase Dependencies

- **Setup (Phase 1)**: No dependencies - can start immediately
- **Foundational (Phase 2)**: Depends on Setup completion - BLOCKS all user stories
- **User Stories (Phase 3+)**: All depend on Foundational phase completion
  - User stories can then proceed in parallel (if staffed)
  - Or sequentially in priority order (P1 → P2 → P3)
- **Polish (Final Phase)**: Depends on all desired user stories being complete

### User Story Dependencies

- **User Story 1 (P1)**: Can start after Foundational (Phase 2) - No dependencies on other stories
- **User Story 2 (P2)**: Can start after Foundational (Phase 2) - May integrate with US1 but should be independently testable
- **Polish Phase**: Depends on completion of both User Story 1 and User Story 2

### Within Each User Story

- Tests (if included) MUST be written and FAIL before implementation
- Implement core functionality before integration/testing
- Story complete before moving to next priority

### Parallel Opportunities

- All Setup tasks marked [P] can run in parallel
- All Foundational tasks marked [P] can run in parallel (within Phase 2)
- Once Foundational phase completes, all user stories can start in parallel (if team capacity allows)
- All tests for a user story marked [P] can run in parallel
- Different user stories can be worked on in parallel by different team members

## Parallel Example: User Story 1

```bash
# Launch all tests for User Story 1 together (if tests requested):
Task: "Create test plan for manual verification of display functionality"
Task: "Define test cases for different game outcomes (zero score, multiple streaks, etc.)"

# Launch implementation tasks for User Story 1 that can be parallelized:
Task: "Implement board rendering using matplotlib (9x9 grid with numbers 7-10)"
Task: "Implement score display in window title/header"
Task: "Implement winning streak visualization with distinct color coding"
Task: "Implement AI name display in window"
```

## Implementation Strategy

### MVP First (User Story 1 Only)

1. Complete Phase 1: Setup
2. Complete Phase 2: Foundational (CRITICAL - blocks all stories)
3. Complete Phase 3: User Story 1
4. **STOP and VALIDATE**: Test User Story 1 independently
5. Deploy/demo if ready

### Incremental Delivery

1. Complete Setup + Foundational → Foundation ready
2. Add User Story 1 → Test independently → Deploy/Demo (MVP!)
3. Add User Story 2 → Test independently → Deploy/Demo
4. Polish phase → Final validation
5. Each story adds value without breaking previous stories

### Parallel Team Strategy

With multiple developers:

1. Team completes Setup + Foundational together
2. Once Foundational is done:
   - Developer A: User Story 1
   - Developer B: User Story 2
3. Stories complete and integrate independently
