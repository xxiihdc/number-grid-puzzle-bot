# Data Model: Post-Game Score Visualization

## Entities

### GameBoard
**Description**: Represents the state of the 9x9 number grid puzzle after game completion.

**Fields**:
- `cells`: 2D array (9x9) of integers representing the numbers (7-10) in each cell, or 0 for empty (should be fully populated after game completion)
- `width`: Integer, constant value of 9
- `height`: Integer, constant value of 9

**Relationships**:
- Contains zero or more WinningStreak entities
- Associated with one FinalScore value
- Associated with one AIPlayerIdentifier

### WinningStreak
**Description**: Represents a continuous line of 3 or more identical numbers on the game board.

**Fields**:
- `number`: Integer (7-10) representing the value that forms the streak
- `coordinates`: List of (row, column) tuples indicating the positions of the streak
- `length`: Integer >= 3 indicating how many cells are in the streak
- `direction`: Enum indicating the orientation: HORIZONTAL, VERTICAL, DIAGONAL_DOWN_RIGHT, DIAGONAL_DOWN_LEFT

**Relationships**:
- Belongs to one GameBoard

### FinalScore
**Description**: Represents the total points accumulated during the game.

**Fields**:
- `points`: Integer >= 0 representing the total score

**Relationships**:
- Associated with one GameBoard

### AIPlayerIdentifier
**Description**: Identifies which AI strategy or player was used to play the game.

**Fields**:
- `name`: String identifier for the AI/player (e.g., "ai_human", "ai_random")
- `display_name`: Optional formatted string for presentation (e.g., "Human Player", "Random AI")

**Relationships**:
- Associated with one GameBoard

## Validation Rules

### GameBoard
- `cells` must be a 9x9 array after game completion (all 81 positions filled with values 7-10)
- All values in `cells` must be integers in the range [7, 10] for a completed game
- For incomplete games (edge case), values may include 0 for empty cells

### WinningStreak
- `length` must be >= 3
- All coordinates in `coordinates` must be within bounds [0, 8] for both row and column
- All cells at the specified coordinates in the GameBoard must contain the same `number` value
- Coordinates must form a continuous line in the specified `direction`

### FinalScore
- `points` must be an integer >= 0

### AIPlayerIdentifier
- `name` must be a non-empty string
- `display_name` if provided must be a non-empty string

## State Transitions

This feature deals with the final state of the game only, so there are no state transitions to model. The entities represent a snapshot of the game at completion.

## Data Flow

1. Game engine produces final GameBoard state after 27 turns
2. Game engine calculates FinalScore from the GameBoard
3. Game engine identifies all WinningStreak patterns in the GameBoard
4. Game engine provides AIPlayerIdentifier used for the game
5. Display function receives all four entities as input parameters
6. Display function renders the visualization using the entity data