#!/usr/bin/env python3
"""
Expectimax search implementation for the Number Grid Puzzle Bot.
Implements dynamic depth search with heuristic evaluation as per design document.
"""

import random
import math
import time
from typing import List, Tuple, Optional, Dict
import numpy as np

from game_state import GameState
from features import FeaturePool


class ExpectimaxSearch:
    """Expectimax search algorithm for finding optimal moves in the puzzle game."""

    def __init__(self, feature_pool: FeaturePool):
        """Initialize the Expectimax search with a feature pool for heuristic evaluation."""
        self.feature_pool = feature_pool
        self.transposition_table = {}  # Cache for previously evaluated states
        self.nodes_evaluated = 0  # For performance monitoring
        self._chromosome = None  # Will hold evolved weights if available
        self.start_time = None
        self.max_time = None
        self.timeout_occurred = False

    def search(self, state: GameState, depth: int, timeout: Optional[float] = None) -> Tuple[Optional[Tuple[int, int]], float]:
        """
        Perform Expectimax search to find the best move.

        Args:
            timeout: Maximum time in seconds to spend on this search. If None, no timeout.

        Returns:
            Tuple of (best_slot, expected_score) where best_slot is (x, y) coordinates
            and expected_score is the expected value from that move.
        """
        self.nodes_evaluated = 0
        best_slot = None
        best_expected_value = -math.inf
        self.start_time = time.time()
        self.max_time = timeout
        self.timeout_occurred = False

        valid_slots = state.get_valid_slots()
        if not valid_slots:
            return None, 0.0

        # For each valid slot, calculate the expected value
        for slot in valid_slots:
            if self.timeout_occurred:
                print(f"Search timed out after {time.time() - self.start_time:.2f}s. Returning best move found so far.")
                break
            x, y = slot

            # Calculate expected value over all possible block spawns (4^3 = 64 possibilities)
            expected_value = self._expectimax(state, slot, depth, is_chance_node=False)

            if expected_value > best_expected_value:
                best_expected_value = expected_value
                best_slot = slot

        return best_slot, best_expected_value

    def _expectimax(self, state: GameState, slot: Tuple[int, int],
                   depth: int, is_chance_node: bool) -> float:
        """
        Recursive Expectimax search.

        Args:
            state: Current game state
            slot: The slot being evaluated (for chance nodes, this is the slot to place block)
            depth: Remaining search depth
            is_chance_node: True if this is a chance node (random block spawn), False if max node (bot decision)

        Returns:
            Expected value of the position
        """
        # Timeout check
        if self.max_time is not None and (time.time() - self.start_time) > self.max_time:
            self.timeout_occurred = True
            # Return heuristic evaluation as fallback
            return self._evaluate_state(state)

        self.nodes_evaluated += 1

        # Check for transposition (state caching)
        state_key = self._get_state_key(state, slot, depth, is_chance_node)
        if state_key in self.transposition_table:
            return self.transposition_table[state_key]

        # Terminal conditions
        if depth == 0 or state.is_game_over():
            # Use heuristic evaluation at leaf nodes
            heuristic_value = self._evaluate_state(state)
            self.transposition_table[state_key] = heuristic_value
            return heuristic_value

        if is_chance_node:
            # Chance node: average over all possible block spawns
            x, y = slot
            total_value = 0.0
            count = 0

            # Generate all possible 3-block combinations (values 7,8,9,10)
            # This is 4^3 = 64 possibilities
            for v1 in [7, 8, 9, 10]:
                for v2 in [7, 8, 9, 10]:
                    for v3 in [7, 8, 9, 10]:
                        block_values = [v1, v2, v3]

                        # Check if we can place this block
                        if state.can_place_block(x, y):
                            # Create new state with this block placed
                            new_state = state.copy()
                            score_gained = new_state.place_block(x, y, block_values)

                            # Recursively evaluate the resulting state (now it's bot's turn)
                            future_value = self._expectimax(new_state, None, depth - 1, False)
                            total_value += score_gained + future_value
                            count += 1
                        # If we can't place the block, this spawn leads to invalid state
                        # In practice, the game mechanics might prevent this, but we'll treat it as 0 value

            # Average over all possible spawns
            expected_value = total_value / count if count > 0 else 0.0
            self.transposition_table[state_key] = expected_value
            return expected_value

        else:
            # Max node: bot chooses the best slot
            if state.is_game_over():
                heuristic_value = self._evaluate_state(state)
                self.transposition_table[state_key] = heuristic_value
                return heuristic_value

            valid_slots = state.get_valid_slots()
            if not valid_slots:
                heuristic_value = self._evaluate_state(state)
                self.transposition_table[state_key] = heuristic_value
                return heuristic_value

            best_value = -math.inf
            for next_slot in valid_slots:
                # For max nodes, we evaluate the chance node that follows placing a block
                # But since we don't know the block values yet, we go to the chance level
                value = self._expectimax(state, next_slot, depth, True)
                if value > best_value:
                    best_value = value

            self.transposition_table[state_key] = best_value
            return best_value

    def _get_state_key(self, state: GameState, slot: Optional[Tuple[int, int]],
                      depth: int, is_chance_node: bool) -> str:
        """Generate a unique key for state transposition caching."""
        # Include the grid state, slot being considered, depth, and node type
        grid_hash = hash(state.grid.tobytes())
        slot_info = str(slot) if slot is not None else "None"
        return f"{grid_hash}_{slot_info}_{depth}_{is_chance_node}"

    def _evaluate_state(self, state: GameState) -> float:
        """
        Evaluate a game state using the heuristic function.
        Implements the weighted sum of features from the design document.
        """
        if self._chromosome is not None:
            # Use evolved weights if available
            return self._chromosome.get_fitness(state, self.feature_pool)
        else:
            # Default equal weights for all features
            feature_values = self.feature_pool.extract_all_features(state)
            # Simple sum of all features (equal weighting)
            return sum(feature_values.values())

    def set_chromosome(self, chromosome):
        """Set the chromosome (weights) to use for evaluation."""
        self._chromosome = chromosome

    def get_nodes_evaluated(self) -> int:
        """Get the number of nodes evaluated in the last search."""
        return self.nodes_evaluated

    def clear_transposition_table(self):
        """Clear the transposition table."""
        self.transposition_table.clear()