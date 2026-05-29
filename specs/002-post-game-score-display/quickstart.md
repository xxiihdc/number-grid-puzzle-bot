# Quick Start: Post-Game Score Visualization

## Overview
This feature adds a graphical display function that shows the final state of a Number Grid Puzzle game after all 27 turns are completed. The display includes the game board with all numbers, the final score, winning streak patterns, and AI identification.

## Installation
No additional installation is required beyond the existing project dependencies:
- Python 3.9+
- numpy
- matplotlib

These are already used by the existing reference implementation in `ref/main.py`.

## Usage
The display function is called from the main bot game flow after a game completes:

```python
# In your game code, after completing a game:
final_score, winning_streaks = game_rules.evaluate_board(final_board, is_final=True, return_streaks=True)
ai_name = "ai_human"  # or whichever AI was used

# Call the display function (to be implemented)
display_final_game_state(final_board, final_score, winning_streaks, ai_name)
```

## Configuration
The feature respects the existing `SINGLE_MATCH_MODE` flag:
- When `SINGLE_MATCH_MODE = True`: Display activates after single match
- When `SINGLE_MATCH_MODE = False`: Display is suppressed during tournament/batch mode
- The main bot implementation reads this flag from `bot/config.py`.

## Customization
The display function can be customized by modifying:
- Colors and styling in the matplotlib drawing code
- Window size and title formatting
- Information displayed (currently shows board, score, streaks, and AI name)

## Testing
To test the display function:
1. Run a single match game (`SINGLE_MATCH_MODE = True`)
2. Verify a graphical window appears showing the final game state
3. Confirm the window shows correct numbers, score, and streaks
4. Close the window to continue

For batch/tournament mode testing:
1. Set `SINGLE_MATCH_MODE = False`
2. Run multiple games
3. Verify no graphical windows appear during processing
4. Check that all games complete successfully without display interruptions

## Mode-Dependent Verification Scenarios

### Scenario A: Single-Match Mode Displays Exactly Once
1. Set `SINGLE_MATCH_MODE = True` in `bot/config.py`.
2. Run one complete game through the single-match entry point.
3. Verify no display appears before turn 27 completes.
4. Verify exactly one display window opens after the final score is calculated.
5. Verify the window contains the final board, final score, highlighted streaks when present, and AI name.
6. Close the window and confirm the process returns or exits normally.

### Scenario B: Batch/Tournament Mode Suppresses Display
1. Set `SINGLE_MATCH_MODE = False` in `bot/config.py`.
2. Run multiple games through the batch or tournament entry point.
3. Verify no display windows appear during active gameplay.
4. Verify no display windows appear after individual games complete.
5. Verify all games finish without blocking on graphical UI.

### Scenario C: Headless Environment Returns Normally
1. Run a single completed game in an environment without an available graphical display.
2. Verify the display path logs an error or informational message.
3. Verify the game process does not crash because of the missing display.
