# Feature Specification: Optimize Game Inference Performance

**Feature Branch**: `003-optimize-game-inference`

**Created**: 2026-05-30

**Status**: Draft

**Input**: User description: "Cải thiện hiệu năng mode chạy game để phù hợp với cấu hình máy; thời gian tối đa cho mỗi nước đi là 200ms."

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Complete Each Move Within the Runtime Budget (Priority: P1)

A player or developer runs a normal game and receives an AI-selected placement quickly enough for gameplay to remain responsive. Every turn, including the most demanding late-game turns, completes within 200 milliseconds.

**Why this priority**: This is the core performance requirement. A strong strategy is not usable in game mode if move selection stalls gameplay.

**Independent Test**: Run complete 27-turn games on the target development machine, record the elapsed selection time for every turn, and verify that each recorded value is at most 200 milliseconds.

**Acceptance Scenarios**:

1. **Given** a normal game is running on the target development machine, **When** the AI selects a slot during any turn from 1 through 27, **Then** it returns a valid available slot within 200 milliseconds.
2. **Given** the game is in a denser middlegame or endgame state, **When** the AI reaches its time budget, **Then** it still returns a valid available slot without delaying the turn beyond 200 milliseconds.
3. **Given** a complete 27-turn game, **When** move durations are collected, **Then** no individual move duration exceeds 200 milliseconds.

---

### User Story 2 - Preserve Valid Gameplay While Optimizing Runtime (Priority: P2)

A player or developer can run the optimized game mode without invalid placements, incomplete games, or runtime failures caused by the performance changes.

**Why this priority**: Faster decisions have no value if they break the puzzle rules or prevent a full game from completing.

**Independent Test**: Run repeated complete games and verify that every selected placement uses one available aligned slot, every game reaches exactly 27 turns, and the final board contains all 81 placed cells.

**Acceptance Scenarios**:

1. **Given** one or more slots remain available, **When** the AI returns a move, **Then** the selected slot is one of the currently available aligned slots.
2. **Given** a game starts with an empty board, **When** game mode completes normally, **Then** exactly 27 blocks have been placed and the 9x9 board is full.
3. **Given** performance measurements are enabled, **When** a game completes, **Then** measurement collection does not change the selected-slot validity or prevent normal completion.

---

### User Story 3 - Compare Runtime Performance Reproducibly (Priority: P3)

A developer can measure game-mode responsiveness consistently and determine whether a change satisfies the runtime budget before accepting it.

**Why this priority**: Performance regressions must be visible and repeatable on the actual machine used to run the bot.

**Independent Test**: Execute the documented performance validation on a fixed set of repeatable games and verify that it reports per-move timing, the slowest move, and whether the 200-millisecond requirement passed.

**Acceptance Scenarios**:

1. **Given** a fixed repeatable game workload, **When** a developer runs performance validation, **Then** the result includes the duration of each move and identifies the slowest move.
2. **Given** any move exceeds 200 milliseconds, **When** validation finishes, **Then** the overall result is reported as failing the runtime requirement.
3. **Given** all moves finish within 200 milliseconds, **When** validation finishes, **Then** the overall result is reported as passing the runtime requirement.

---

### Edge Cases

- The first turn has the largest number of available slots; it must still finish within 200 milliseconds.
- Middlegame turns may have more competing continuations than opening turns; they must still respect the same runtime budget.
- Endgame turns may use deeper analysis where feasible, but they must not exceed the runtime budget.
- If the time budget is nearly exhausted before all candidate placements have been considered equally, the bot must still return a valid available slot.
- If only one valid slot remains, the bot must return it promptly and complete the game normally.
- Runtime measurement must distinguish move-selection time from optional post-game visualization time.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: In game mode, the system MUST return a valid available slot for every move within a maximum elapsed time of 200 milliseconds on the target development machine.
- **FR-002**: The system MUST apply the same 200-millisecond maximum to every game phase: opening, middlegame, and endgame.
- **FR-003**: The system MUST return a valid available slot when the move-selection time budget is nearly exhausted, even if additional analysis could otherwise continue.
- **FR-004**: The system MUST preserve the existing puzzle constraints: each selected slot is aligned, unused, and able to accept one vertical three-cell block.
- **FR-005**: The system MUST allow a normal game to complete exactly 27 turns and fill all 81 cells after the performance improvement.
- **FR-006**: The system MUST keep game-mode move selection separate from offline training activity.
- **FR-007**: The system MUST provide a repeatable way to validate game-mode performance using a fixed workload.
- **FR-008**: Performance validation MUST record each move's selection duration, identify the slowest move, and report whether any move exceeded 200 milliseconds.
- **FR-009**: Performance validation MUST measure move selection independently from optional final-score visualization.
- **FR-010**: The system MUST preserve the ability to evaluate candidate moves using the block spawned for the current turn.

### Key Entities

- **Game Turn**: One of the 27 placement opportunities in a game, including its phase, spawned block, available aligned slots, selected slot, and move-selection duration.
- **Runtime Budget**: The maximum permitted elapsed selection time for one game-mode move, fixed at 200 milliseconds.
- **Performance Validation Run**: A repeatable collection of complete games used to record move timings, identify the slowest move, and determine whether the runtime budget was satisfied.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: During performance validation on the target development machine, 100% of game-mode move selections complete in at most 200 milliseconds.
- **SC-002**: During performance validation, 100% of returned moves select an available aligned slot.
- **SC-003**: Every normal validation game completes all 27 turns and fills all 81 cells.
- **SC-004**: A developer can determine the slowest move and pass/fail result for the 200-millisecond limit from one performance validation run.
- **SC-005**: Offline training is not started or performed while a normal game-mode move is being selected.

## Assumptions

- The target environment is the current development machine used to run this repository.
- The 200-millisecond limit applies to move selection only; startup, console output, offline training, and optional post-game visualization are outside that timing window.
- The game follows the existing 9x9 grid, 27-turn, aligned vertical three-cell block rules.
- A block is spawned before the AI selects its placement, matching the existing game flow represented by the reference game runner.
- Repeatable validation uses fixed random inputs so performance comparisons are meaningful across changes.
- Strategy quality remains important, but this feature's acceptance gate is runtime responsiveness and valid gameplay rather than a guaranteed score improvement.
