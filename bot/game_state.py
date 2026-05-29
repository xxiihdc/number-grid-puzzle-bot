#!/usr/bin/env python3
"""
Game state representation for the Number Grid Puzzle.
Implements the 9x9 grid with 3x1 vertical blocks and scoring mechanics.
"""

import numpy as np
from typing import List, Tuple, Optional


class GameState:
    """Represents the state of the 9x9 number grid puzzle."""

    # Constants from the design document
    GRID_SIZE = 9
    TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 81
    TOTAL_TURNS = 27
    BLOCK_HEIGHT = 3
    BLOCK_WIDTH = 1
    VALID_NUMBERS = {7, 8, 9, 10}
    VALID_X_POSITIONS = list(range(GRID_SIZE))  # 0-8
    VALID_Y_ANCHORS = [0, 3, 6]  # Top row of each 3-cell slot

    def __init__(self):
        """Initialize an empty 9x9 grid."""
        # Using 1D array for better cache performance as suggested in design doc
        self.grid = np.zeros(self.TOTAL_CELLS, dtype=int)
        self.occupied_slots = set()  # Track which slots have been used
        self.turn_number = 0
        self.total_score = 0

    @property
    def VALID_SLOTS(self) -> List[Tuple[int, int]]:
        """Get list of all valid slots (27 total). Computed on-demand."""
        return [(x, y) for x in self.VALID_X_POSITIONS for y in self.VALID_Y_ANCHORS]

    def _to_index(self, x: int, y: int) -> int:
        """Convert 2D coordinates to 1D array index."""
        return y * self.GRID_SIZE + x

    def _from_index(self, index: int) -> Tuple[int, int]:
        """Convert 1D array index to 2D coordinates."""
        y = index // self.GRID_SIZE
        x = index % self.GRID_SIZE
        return x, y

    def is_valid_slot(self, x: int, y: int) -> bool:
        """Check if a slot position is valid (within bounds and follows slot rules)."""
        return (x in self.VALID_X_POSITIONS and
                y in self.VALID_Y_ANCHORS and
                (x, y) not in self.occupied_slots)

    def get_valid_slots(self) -> List[Tuple[int, int]]:
        """Get list of all currently valid (unoccupied) slots."""
        return [slot for slot in self.VALID_SLOTS if slot not in self.occupied_slots]

    def can_place_block(self, x: int, y: int) -> bool:
        """Check if a 3x1 block can be placed at position (x, y)."""
        if not self.is_valid_slot(x, y):
            return False

        # Check if all three cells in the column are empty
        for dy in range(self.BLOCK_HEIGHT):
            target_y = y + dy
            if target_y >= self.GRID_SIZE:
                return False
            if self.grid[self._to_index(x, target_y)] != 0:
                return False

        return True

    def place_block(self, x: int, y: int, block_values: List[int]) -> int:
        """
        Place a 3x1 block at position (x, y) with given values.
        Returns the score gained from this placement.
        """
        if not self.can_place_block(x, y):
            raise ValueError(f"Cannot place block at slot ({x}, {y})")

        # Place the block values
        score_gained = 0
        for dy, value in enumerate(block_values):
            target_y = y + dy
            index = self._to_index(x, target_y)
            self.grid[index] = value

        # Calculate score from the placement (local ray-casting as per design)
        score_gained = self._calculate_placement_score(x, y, block_values)

        # Mark slot as occupied
        self.occupied_slots.add((x, y))
        self.turn_number += 1
        self.total_score += score_gained

        return score_gained

    def make_move(self, slot: Tuple[int, int]) -> int:
        """
        Make a move by placing a randomly spawned 3x1 block at the given slot.
        Each turn spawns one 3x1 vertical block with 3 random numbers from {7,8,9,10}.
        Returns the score gained from this placement.
        """
        import random
        x, y = slot

        # Generate random block values (each number is independently chosen from {7,8,9,10})
        block_values = [random.choice([7, 8, 9, 10]) for _ in range(3)]

        # Place the block and return the score gained
        return self.place_block(x, y, block_values)

    def _calculate_placement_score(self, x: int, y: int, block_values: List[int]) -> int:
        """
        Calculate score gained from placing a block using local ray-casting.
        Only checks lines that pass through the newly placed blocks.
        Implements the O(1) local scoring algorithm from design doc.
        """
        score = 0

        # For each of the 3 newly placed blocks, check in 4 directions
        for dy, value in enumerate(block_values):
            target_y = y + dy

            # Check 4 directions: horizontal (1,0), vertical (0,1), diagonal down-right (1,1), diagonal down-left (1,-1)
            directions = [(1, 0), (0, 1), (1, 1), (1, -1)]

            for dx, dy_dir in directions:
                # Count in positive direction
                count_pos = 0
                cx, cy = x + dx, target_y + dy_dir
                while (0 <= cx < self.GRID_SIZE and 0 <= cy < self.GRID_SIZE and
                       self.grid[self._to_index(cx, cy)] == value):
                    count_pos += 1
                    cx += dx
                    cy += dy_dir

                # Count in negative direction
                count_neg = 0
                cx, cy = x - dx, target_y - dy_dir
                while (0 <= cx < self.GRID_SIZE and 0 <= cy < self.GRID_SIZE and
                       self.grid[self._to_index(cx, cy)] == value):
                    count_neg += 1
                    cx -= dx
                    cy -= dy_dir

                # Total length including the center block
                total_length = count_pos + 1 + count_neg

                # Score if we have 3 or more in a row (as per scoring mechanism)
                if total_length >= 3:
                    # Each additional block beyond 2 gives points
                    # This is simplified - actual scoring might be more complex
                    score += (total_length - 2)  # 3-in-a-row = 1 point, 4-in-a-row = 2 points, etc.

        return score

    def get_grid_2d(self) -> np.ndarray:
        """Get the grid as a 2D numpy array for easier visualization."""
        return self.grid.reshape((self.GRID_SIZE, self.GRID_SIZE))

    def is_game_over(self) -> bool:
        """Check if the game is over (27 turns completed)."""
        return self.turn_number >= self.TOTAL_TURNS

    def get_empty_slots_count(self) -> int:
        """Get number of remaining empty slots."""
        return len(self.VALID_SLOTS) - len(self.occupied_slots)

    def __str__(self) -> str:
        """String representation of the game state."""
        grid_2d = self.get_grid_2d()
        lines = []
        for y in range(self.GRID_SIZE):
            row = []
            for x in range(self.GRID_SIZE):
                val = grid_2d[y, x]
                row.append(f"{val:2d}" if val != 0 else "..")
            lines.append(" ".join(row))
        return "\n".join(lines)

    def copy(self) -> 'GameState':
        """Create a deep copy of the game state."""
        new_state = GameState()
        new_state.grid = self.grid.copy()
        new_state.occupied_slots = self.occupied_slots.copy()
        new_state.turn_number = self.turn_number
        new_state.total_score = self.total_score
        return new_state