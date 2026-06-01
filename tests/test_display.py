#!/usr/bin/env python3
"""
Test script to verify the display function works correctly
"""

import numpy as np
import sys
import os

# Add the project root to the sys.path so we can import from utils
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__))))

from utils.display import display_final_game_state

def test_display_function():
    """Test the display function with sample data"""
    # Create a sample 9x9 board with some numbers
    board = np.zeros((9, 9), dtype=int)

    # Fill in some sample data
    board[0, 0] = 7
    board[0, 1] = 7
    board[0, 2] = 7  # Horizontal streak of 7s

    board[1, 0] = 8
    board[2, 0] = 8
    board[3, 0] = 8  # Vertical streak of 8s

    board[4, 4] = 9
    board[5, 5] = 9
    board[6, 6] = 9  # Diagonal streak of 9s

    # Some other numbers
    board[0, 3] = 10
    board[1, 4] = 7
    board[2, 5] = 8

    final_score = 42
    winning_streaks = [
        [(0, 0), (0, 1), (0, 2)],  # Horizontal 7s
        [(1, 0), (2, 0), (3, 0)],  # Vertical 8s
        [(4, 4), (5, 5), (6, 6)]   # Diagonal 9s
    ]
    ai_name = "test_ai"

    print("Testing display function with sample data...")
    print(f"Board shape: {board.shape}")
    print(f"Final score: {final_score}")
    print(f"Winning streaks: {winning_streaks}")
    print(f"AI name: {ai_name}")

    # Call the display function
    try:
        display_final_game_state(board, final_score, winning_streaks, ai_name)
        print("Display function executed successfully!")
    except Exception as e:
        print(f"Error in display function: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_display_function()