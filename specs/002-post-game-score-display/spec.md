# Feature Specification: Post-Game Score Visualization

**Feature Branch**: `002-post-game-score-display`

**Created**: 2026-05-29

**Status**: Draft

**Input**: User description: "I want to create a function that displays a graphical interface for a game, not for each turn, but only after the game is finished, to show the score visually. (Reference: ref/main.py)"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - View Final Game Result (Priority: P1)

A player or developer runs a single match of the Number Grid Puzzle game. After all 27 turns are completed and the final score is calculated, a graphical window appears showing the complete game board with all numbers placed, the final score, the AI name used, and winning streak patterns highlighted.

**Why this priority**: This is the core feature — the entire purpose is to visualize the completed game state. Without this, there is no feature.

**Independent Test**: Run a complete game with any AI module, verify a graphical window appears after the game ends showing the grid, score, and streaks. Close the window to complete the test.

**Acceptance Scenarios**:

1. **Given** a game has just completed all 27 turns, **When** the final evaluation is done, **Then** a graphical window opens displaying the 9x9 game grid with all 81 cells filled with numbers (7-10).
2. **Given** the graphical window is open, **When** the user views the display, **Then** the final score is shown in the window title or header area, and all winning streak lines are highlighted on the board.
3. **Given** the graphical window is open, **When** the user closes the window, **Then** the program terminates (or returns control to the caller).

---

### User Story 2 - Distinguish Active Gameplay from Post-Game Display (Priority: P2)

As a developer running experiments or tournaments, the display function must NOT activate during active gameplay — it only triggers once when the game is fully complete. This prevents unwanted pop-ups during batch processing or tournament runs.

**Why this priority**: Ensures the feature doesn't interfere with automated tournament/batch modes where visual output would be disruptive.

**Independent Test**: Run a tournament of multiple games; verify no graphical windows appear during gameplay. Then run a single match; verify exactly one graphical window appears after completion.

**Acceptance Scenarios**:

1. **Given** a tournament/batch mode is running, **When** multiple games complete, **Then** no graphical windows appear during or after the games.
2. **Given** single-match mode is active, **When** the game completes, **Then** exactly one graphical window appears showing the final result.

---

### Edge Cases

- What happens if the game completed with a score of zero (no winning streaks)? The display should still show the board with all numbers but no highlighted streaks.
- What happens if the board has empty cells (an incomplete game)? The function should only be called for complete games; if called with an incomplete board, it should still render what is available without crashing.
- What happens if the graphical display environment is not available (headless server)? The function should log an error message and return normally without crashing, allowing batch/tournament modes to continue.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: System MUST provide a function that renders the complete 9x9 game board as a graphical window after a game has finished.
- **FR-002**: System MUST display all numbers (7-10) placed in each cell of the grid during the completed game.
- **FR-003**: System MUST visually highlight all winning streak patterns (3+ identical numbers in a continuous horizontal, vertical, or diagonal line) on the board.
- **FR-004**: System MUST display the final computed score in the graphical window.
- **FR-005**: System MUST display the identifier (name) of the AI or player that completed the game.
- **FR-006**: The graphical display function MUST only be invoked after the game finishes (i.e., after all 27 turns are played and the final board evaluation is complete), not during active gameplay or on a per-turn basis.
- **FR-007**: The graphical window MUST remain open until the user manually closes it, allowing time to review the result.

### Key Entities

- **Game Board**: A 9x9 grid of cells, each containing a number (7-10) or empty (0). After game completion, all 81 cells are filled.
- **Winning Streak**: A set of 3 or more identical numbers forming a continuous line (horizontal, vertical, or diagonal) on the board. Each streak has coordinates and a number value.
- **Final Score**: The total points accumulated from all scoring events during the game, computed after all 27 turns.
- **AI/Player Identifier**: A name string identifying which strategy or player was used to play the game.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: The graphical window appears within 1 second of the game completing its final evaluation.
- **SC-002**: All numbers on the board are clearly readable at standard screen resolution (1920x1080 or higher).
- **SC-003**: Winning streaks are visually distinguishable from non-winning cells with distinct color coding or highlighting.
- **SC-004**: The display does not activate during tournament/batch mode (zero unwanted pop-ups).
- **SC-005**: A user can understand the game outcome (score, AI used, winning patterns) from the display within 10 seconds of viewing.

## Assumptions

- The game follows the existing 9x9 grid, 27-turn, 3x1 vertical block rules defined in the project.
- The graphical display uses a standard windowing system available on the target platform (macOS, as indicated by the development environment).
- The existing `draw_visual_board` function in `ref/main.py` serves as a reference implementation that already handles the core rendering logic.
- The function will be callable from the existing `play_game` / `run_single_match` flow after game completion, not as a per-turn callback.
- Tournament/batch mode is controlled by the main bot configuration flag (`SINGLE_MATCH_MODE` in `bot/config.py`) and will be respected.
- The display function does not need to support interactivity beyond window close — it is a static result view.

## Clarifications

### Session 2026-05-29

- Q: What specific behavior constitutes "graceful handling" when the display environment is unavailable? Should the function return an error code, log a message, raise a specific exception, or take some other action? → A: Log an error message and return normally (non-blocking)
