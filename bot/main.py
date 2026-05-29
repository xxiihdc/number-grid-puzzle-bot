#!/usr/bin/env python3
"""
Main entry point for the Number Grid Puzzle Bot.
Implements the Expectimax search with dynamic depth and heuristic evaluation.
"""

import sys
import os
import time
from typing import Tuple, List, Optional
import numpy as np

# Add the project root to the sys.path so top-level modules can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SINGLE_MATCH_MODE
from game_state import GameState
from expectimax import ExpectimaxSearch
from genetics import GeneticOptimizer
from features import FeaturePool
from scoring import evaluate_board


def main():
    """Main function to run the puzzle bot."""
    print("Number Grid Puzzle Bot Initializing...")
    print("=" * 50)

    # Initialize game state
    game_state = GameState()

    # Initialize feature pool (15 features from design doc)
    feature_pool = FeaturePool()

    # Initialize Expectimax search
    search_engine = ExpectimaxSearch(feature_pool)

    # Initialize genetic optimizer (for offline training)
    optimizer = GeneticOptimizer(feature_pool, search_engine)

    # Check if we should train or play
    if len(sys.argv) > 1 and sys.argv[1] == "train":
        print("Starting genetic algorithm training...")
        optimizer.train()
    else:
        print("Starting puzzle solving...")
        play_game(game_state, search_engine)


def play_game(game_state: GameState, search_engine: ExpectimaxSearch):
    """Play a complete game of 27 turns."""
    total_score = 0

    for turn in range(1, 28):  # 27 turns
        print(f"\nTurn {turn}/27")
        print(f"Current Score: {total_score}")
        print("Board State:")
        print(game_state)

        # Determine search depth based on game phase
        if turn <= 10:
            depth = 2
        elif turn <= 20:
            depth = 3
        else:
            depth = 4  # or 5 for endgame

        # Get best move from Expectimax search with timeout of 3 seconds
        start_time = time.time()
        best_slot, expected_score = search_engine.search(game_state, depth, timeout=3.0)
        search_time = time.time() - start_time

        print(f"Search took {search_time:.2f}s")
        print(f"Best slot: {best_slot} (Expected score: {expected_score:.2f})")

        # Apply the move (spawns a random block and places it)
        if best_slot is not None:
            score_gained = game_state.make_move(best_slot)
            total_score += score_gained
            print(f"Score gained: {score_gained}")
        else:
            print("No valid moves available!")
            break

    print("\n" + "=" * 50)
    print(f"Game Over! Final Score: {total_score}")
    print("Final Board:")
    print(game_state)

    # Display final game state if enabled (respecting SINGLE_MATCH_MODE)
    try:
        # Import here to avoid issues if matplotlib is not available
        from utils.display import display_final_game_state

        # Only display in single match mode
        if SINGLE_MATCH_MODE:
            # Get the final board state
            board = game_state.get_grid_2d()

            # Evaluate the final board to get score and winning streaks
            # We use return_streaks=True to get both score and streaks
            evaluation_result = evaluate_board(board, is_final=True, return_streaks=True)

            # Handle the return value - it should be a tuple (score, streaks) when return_streaks=True
            if isinstance(evaluation_result, tuple) and len(evaluation_result) == 2:
                final_score, winning_streaks = evaluation_result
            else:
                # Fallback: if it's not a tuple, use our calculated total_score and empty streaks
                final_score = total_score
                winning_streaks = []

            ai_name = "expectimax"  # This could be made configurable

            print("Opening final game visualization...")
            display_final_game_state(board, final_score, winning_streaks, ai_name)
        else:
            print("Skipping display in batch/tournament mode (SINGLE_MATCH_MODE=False)")
    except ImportError as e:
        print(f"Display not available: {e}")
    except Exception as e:
        # Handle any other display errors gracefully
        import logging
        logger = logging.getLogger(__name__)
        logger.error(f"Display error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
