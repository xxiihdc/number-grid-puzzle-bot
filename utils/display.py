"""
Display utilities for Number Grid Puzzle game.
Provides graphical visualization of game states.
"""

import logging
import numpy as np
import matplotlib.pyplot as plt

logger = logging.getLogger(__name__)
BOARD_SIZE = 9

def display_final_game_state(board, final_score, winning_streaks, ai_name, block=True):
    """
    Display the final game state in a graphical window.

    Args:
        board: 9x9 numpy array representing the final game board
        final_score: Integer representing the final score
        winning_streaks: List of winning streak coordinate lists
        ai_name: String identifier of the AI used
        block: Whether to wait until the user closes the graphical windows
    """
    try:
        # Validate inputs
        if board is None or not isinstance(board, np.ndarray):
            logger.error("Invalid board provided to display function")
            return

        if board.shape != (9, 9):
            logger.error(f"Board must be 9x9, got shape {board.shape}")
            return

        # Create the visualization
        fig, ax = plt.subplots(figsize=(8, 8))

        # Set up the grid
        ax.set_xlim(-0.5, BOARD_SIZE - 0.5)
        ax.set_ylim(BOARD_SIZE - 0.5, -0.5)
        ax.set_xticks(np.arange(-0.5, BOARD_SIZE, 1), minor=True)
        ax.set_yticks(np.arange(-0.5, BOARD_SIZE, 1), minor=True)
        ax.grid(which="minor", color="black", linestyle='-', linewidth=2)
        ax.tick_params(which="both", bottom=False, left=False,
                      labelbottom=False, labelleft=False)

        # Draw the numbers on the board
        for r in range(BOARD_SIZE):
            for c in range(BOARD_SIZE):
                val = board[r, c]
                if val != 0:  # Only display non-zero values
                    ax.text(c, r, str(int(val)), va='center', ha='center',
                           fontsize=16, fontweight='bold')

        # Draw winning streaks if any
        if winning_streaks:
            colors = ['#FF4B4B', '#4B8BFF', '#28C76F', '#FF9F43', '#9C27B0', '#00BCD4']
            for i, streak in enumerate(winning_streaks):
                if len(streak) >= 3:  # Only draw valid streaks
                    xs = [coord[1] for coord in streak]
                    ys = [coord[0] for coord in streak]
                    ax.plot(xs, ys, color=colors[i % len(colors)],
                           linewidth=8, alpha=0.6, solid_capstyle='round')

        # Set title with score and AI information
        plt.title(f"AI: {ai_name.upper()} | Final Score: {final_score}",
                 fontsize=16, fontweight='bold', pad=20)

        plt.tight_layout()
        plt.show(block=block)

    except Exception as e:
        logger.error(f"Failed to display game state: {e}")
        # Gracefully handle headless or display errors - just log and return
        # This allows batch/tournament modes to continue without interruption
