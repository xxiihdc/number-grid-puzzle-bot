#!/usr/bin/env python3
"""
Test file to demonstrate the basic functionality of the Number Grid Puzzle Bot.
"""

import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

from bot.main import main
from bot.game_state import GameState
from bot.features import FeaturePool
from bot.expectimax import ExpectimaxSearch


def test_game_state():
    """Test basic game state functionality."""
    print("Testing Game State...")
    state = GameState()

    print(f"Initial state (turn {state.turn_number}):")
    print(state)
    print(f"Valid slots: {len(state.get_valid_slots())}")

    # Test placing a block
    if state.get_valid_slots():
        slot = state.get_valid_slots()[0]
        x, y = slot
        block_values = [7, 8, 9]

        print(f"\nPlacing block {block_values} at slot ({x}, {y})")
        try:
            score = state.place_block(x, y, block_values)
            print(f"Score gained: {score}")
            print(f"New state (turn {state.turn_number}):")
            print(state)
        except Exception as e:
            print(f"Error placing block: {e}")


def test_features():
    """Test feature extraction."""
    print("\nTesting Feature Extraction...")
    state = GameState()
    feature_pool = FeaturePool()

    # Extract features from initial state
    features = feature_pool.extract_all_features(state)

    print("Features from empty board:")
    for name, value in features.items():
        print(f"  {name}: {value}")

    # Place a block and test again
    if state.get_valid_slots():
        slot = state.get_valid_slots()[0]
        x, y = slot
        block_values = [7, 7, 7]  # Three 7s should create some features
        state.place_block(x, y, block_values)

        features = feature_pool.extract_all_features(state)
        print("\nFeatures after placing [7,7,7]:")
        for name, value in features.items():
            if value != 0:  # Only show non-zero features
                print(f"  {name}: {value}")


def test_expectimax():
    """Test Expectimax search (basic)."""
    print("\nTesting Expectimax Search...")
    state = GameState()
    feature_pool = FeaturePool()
    search_engine = ExpectimaxSearch(feature_pool)

    # Test with shallow depth for quick results
    if state.get_valid_slots():
        slot, score = search_engine.search(state, depth=1)
        print(f"Best slot: {slot}, Expected score: {score}")


if __name__ == "__main__":
    print("Number Grid Puzzle Bot - Component Tests")
    print("=" * 50)

    test_game_state()
    test_features()
    test_expectimax()

    print("\n" + "=" * 50)
    print("All tests completed!")