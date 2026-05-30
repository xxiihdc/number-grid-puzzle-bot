#!/usr/bin/env python3
"""
Main entry point for the Number Grid Puzzle Bot.
Implements the Expectimax search with dynamic depth and heuristic evaluation.
"""

import sys
import os

# Add the project root to the sys.path so top-level modules can be imported.
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

from config import SINGLE_MATCH_MODE
from game_state import GameState
from expectimax import ExpectimaxSearch
from features import FeaturePool
from scoring import evaluate_board


def run_play_mode():
    """Run one normal puzzle with the newest promoted chromosome when available."""
    print("Number Grid Puzzle Bot Initializing...")
    print("=" * 50)

    # Initialize game state
    game_state = GameState()

    # Initialize the shared inference and offline-training feature pool.
    feature_pool = FeaturePool()

    # Initialize Expectimax search
    search_engine = ExpectimaxSearch(feature_pool)
    from training_weights import load_active_chromosome, sync_latest_weights

    active_path = sync_latest_weights()
    active_chromosome = load_active_chromosome()
    if active_chromosome is not None:
        search_engine.set_chromosome(active_chromosome)
        print(f"Loaded active trained chromosome: {active_path}")

    print("Starting puzzle solving...")
    play_game(game_state, search_engine)


def run_training_mode(config, output_directory="training_runs"):
    """Run the offline optimizer only when explicitly requested."""
    from training_runner import TrainingInterrupted, run_training

    print("Starting genetic algorithm training...")
    try:
        summary_path = run_training(config, output_directory)
    except TrainingInterrupted as error:
        print(f"Training interrupted. Summary: {error.summary_path}")
        return error.summary_path
    print(f"Training summary: {summary_path}")
    return summary_path


def main(argv=None):
    """Compatibility entry point for direct module execution."""
    from cli import run_cli
    return run_cli(argv)


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
            depth = 5

        # Spawn first so search evaluates the exact block that will be placed.
        block_values = game_state.spawn_block()
        best_slot, expected_score = search_engine.search(
            game_state, block_values, depth, timeout=ExpectimaxSearch.DEFAULT_TIMEOUT
        )
        stats = search_engine.get_last_search_stats()

        print(f"Spawned block: {block_values}")
        print(
            f"Search took {stats.elapsed_seconds * 1000:.2f}ms "
            f"(depth {stats.completed_depth}/{stats.target_depth}, "
            f"nodes={stats.nodes_evaluated}, cache={stats.cache_entries}, "
            f"timeout={stats.timed_out}, fallback={stats.fallback_used}, "
            f"reason={stats.fallback_reason})"
        )
        print(f"Best slot: {best_slot} (Expected score: {expected_score:.2f})")

        # Apply the exact block that search evaluated.
        if best_slot is not None:
            score_gained = game_state.make_move(best_slot, block_values)
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
