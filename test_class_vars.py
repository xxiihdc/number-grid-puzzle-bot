#!/usr/bin/env python3
"""Test class variable initialization order."""

class TestClass:
    GRID_SIZE = 9
    TOTAL_CELLS = GRID_SIZE * GRID_SIZE  # 81
    TOTAL_TURNS = 27
    BLOCK_HEIGHT = 3
    BLOCK_WIDTH = 1
    VALID_NUMBERS = {7, 8, 9, 10}
    VALID_X_POSITIONS = list(range(GRID_SIZE))  # 0-8
    VALID_Y_ANCHORS = [0, 3, 6]  # Top row of each 3-cell slot

    @property
    def VALID_SLOTS(self):
        """Get all valid slots (27 total). Computed on-demand."""
        return [(x, y) for x in self.VALID_X_POSITIONS for y in self.VALID_Y_ANCHORS]

    def __init__(self):
        print("GRID_SIZE:", self.GRID_SIZE)
        print("VALID_X_POSITIONS:", self.VALID_X_POSITIONS)
        print("VALID_Y_ANCHORS:", self.VALID_Y_ANCHORS)
        print("VALID_SLOTS:", self.VALID_SLOTS)
        print("Number of slots:", len(self.VALID_SLOTS))

if __name__ == "__main__":
    t = TestClass()
