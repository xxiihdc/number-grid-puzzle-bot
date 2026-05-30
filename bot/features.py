#!/usr/bin/env python3
"""
Feature extraction module for the Number Grid Puzzle Bot.
Implements the heuristic feature pool used by inference and offline training.
"""

import numpy as np
from typing import Dict, List, Tuple
from game_state import GameState


class FeaturePool:
    """Extracts features from game state for heuristic evaluation."""

    def __init__(self):
        """Initialize the feature pool with all supported features."""
        self.feature_names = [
            "f1_actual_score",
            "f2_potential_horizontal_pairs",
            "f3_potential_diagonal_pairs",
            "f4_column_bumpiness",
            "f5_center_bias",
            "f6_isolated_slots",
            "f7_dead_ends",
            "f8_max_height",
            "f9_number_density_7",
            "f10_number_density_8",
            "f11_number_density_9",
            "f12_number_density_10",
            "f13_vertical_match_interfaces",
            "f14_empty_slots_count",
            "f15_diagonal_cross_points",
            "f16_open_single_windows",
            "f17_open_pair_windows",
            "f18_blocked_windows",
            "f19_multi_line_completion_cells",
        ]
        self.num_features = len(self.feature_names)

    def get_feature_names(self) -> List[str]:
        """Get list of all feature names."""
        return self.feature_names.copy()

    def extract_all_features(self, state: GameState) -> Dict[str, float]:
        """
        Extract all features from the game state.
        Returns a dictionary mapping feature names to their values.
        """
        features = {}
        grid_2d = state.get_grid_2d()

        # f1_actual_score: Current score from placements
        features["f1_actual_score"] = float(state.total_score)

        # f2_potential_horizontal_pairs: Horizontal pairs with matching numbers and empty ends
        features["f2_potential_horizontal_pairs"] = self._count_horizontal_pairs(grid_2d)

        # f3_potential_diagonal_pairs: Diagonal pairs with matching numbers and empty ends
        features["f3_potential_diagonal_pairs"] = self._count_diagonal_pairs(grid_2d)

        # f4_column_bumpiness: Roughness of the grid (height differences between adjacent columns)
        features["f4_column_bumpiness"] = self._calculate_bumpiness(grid_2d)

        # f5_center_bias: Bonus for placing in center columns (3,4,5) in early game
        features["f5_center_bias"] = self._calculate_center_bias(state)

        # f6_isolated_slots: Empty slots completely surrounded by filled slots
        features["f6_isolated_slots"] = self._count_isolated_slots(state)

        # f7_dead_ends: Empty slots blocked by different numbers on both sides
        features["f7_dead_ends"] = self._count_dead_ends(grid_2d)

        # f8_max_height: Maximum height of any column
        features["f8_max_height"] = self._get_max_height(grid_2d)

        # f9_number_density_7: Clustering of number 7s
        features["f9_number_density_7"] = self._calculate_number_density(grid_2d, 7)

        # f10_number_density_8: Clustering of number 8s
        features["f10_number_density_8"] = self._calculate_number_density(grid_2d, 8)

        # f11_number_density_9: Clustering of number 9s
        features["f11_number_density_9"] = self._calculate_number_density(grid_2d, 9)

        # f12_number_density_10: Clustering of number 10s
        features["f12_number_density_10"] = self._calculate_number_density(grid_2d, 10)

        # f13_vertical_match_interfaces: Vertical matches between slots in same column
        features["f13_vertical_match_interfaces"] = self._count_vertical_matches(grid_2d)

        # f14_empty_slots_count: Number of remaining empty slots
        features["f14_empty_slots_count"] = float(state.get_empty_slots_count())

        # f15_diagonal_cross_points: Strategic empty slots where diagonals cross
        features["f15_diagonal_cross_points"] = self._count_diagonal_cross_points(grid_2d)

        line_windows = self._calculate_line_window_metrics(grid_2d)
        features["f16_open_single_windows"] = line_windows["open_single_windows"]
        features["f17_open_pair_windows"] = line_windows["open_pair_windows"]
        features["f18_blocked_windows"] = line_windows["blocked_windows"]
        features["f19_multi_line_completion_cells"] = line_windows["multi_line_completion_cells"]

        return features

    def _calculate_line_window_metrics(self, grid: np.ndarray) -> Dict[str, float]:
        """Count exact three-cell scoring windows in all four line directions."""
        height, width = grid.shape
        open_single_windows = 0
        open_pair_windows = 0
        blocked_windows = 0
        completion_counts = {}
        directions = ((1, 0), (0, 1), (1, 1), (1, -1))

        for dx, dy in directions:
            for y in range(height):
                for x in range(width):
                    end_x = x + 2 * dx
                    end_y = y + 2 * dy
                    if not (0 <= end_x < width and 0 <= end_y < height):
                        continue
                    coordinates = [(x + offset * dx, y + offset * dy) for offset in range(3)]
                    values = [grid[cell_y, cell_x] for cell_x, cell_y in coordinates]
                    filled = [value for value in values if value != 0]
                    empty_coordinates = [
                        coordinate for coordinate, value in zip(coordinates, values) if value == 0
                    ]
                    distinct_values = set(filled)
                    if len(distinct_values) > 1:
                        blocked_windows += 1
                    elif len(filled) == 1:
                        open_single_windows += 1
                    elif len(filled) == 2 and len(empty_coordinates) == 1:
                        open_pair_windows += 1
                        coordinate = empty_coordinates[0]
                        completion_counts[coordinate] = completion_counts.get(coordinate, 0) + 1

        return {
            "open_single_windows": float(open_single_windows),
            "open_pair_windows": float(open_pair_windows),
            "blocked_windows": float(blocked_windows),
            "multi_line_completion_cells": float(sum(
                count >= 2 for count in completion_counts.values()
            )),
        }

    def _count_horizontal_pairs(self, grid: np.ndarray) -> float:
        """
        f2_potential_horizontal_pairs: Count horizontal pairs of matching numbers
        with empty spaces on both ends (potential to form 3-in-a-row).
        """
        count = 0
        height, width = grid.shape

        for y in range(height):
            for x in range(width - 2):  # Need space for pair + one empty on each side
                # Check if we have a pair with potential to extend
                if (grid[y, x] != 0 and grid[y, x] == grid[y, x + 1] and
                    # Check if left side is empty or boundary
                    (x == 0 or grid[y, x - 1] == 0) and
                    # Check if right side is empty or boundary
                    (x + 2 >= width or grid[y, x + 2] == 0)):
                    count += 1
                # Also check the reverse orientation
                elif (grid[y, x] != 0 and grid[y, x] == grid[y, x + 1] and
                      # Check if we can extend to the left
                      (x >= 2 and grid[y, x - 1] == grid[y, x] and
                       (x == 0 or grid[y, x - 2] == 0))):
                    # This would be counted when we reach x-2, so skip to avoid double counting
                    pass

        return count

    def _count_diagonal_pairs(self, grid: np.ndarray) -> float:
        """
        f3_potential_diagonal_pairs: Count diagonal pairs of matching numbers
        with empty spaces on both ends (potential to form 3-in-a-row diagonally).
        """
        count = 0
        height, width = grid.shape

        # Check both diagonal directions: down-right and down-left
        for y in range(height - 2):
            for x in range(width - 2):
                # Down-right diagonal
                if (grid[y, x] != 0 and grid[y, x] == grid[y + 1, x + 1] and
                    # Check if we can extend backwards
                    (x == 0 or y == 0 or grid[y - 1, x - 1] == 0) and
                    # Check if we can extend forwards
                    (y + 2 >= height or x + 2 >= width or grid[y + 2, x + 2] == 0)):
                    count += 1

                # Down-left diagonal
                if (grid[y, x + 2] != 0 and grid[y, x + 2] == grid[y + 1, x + 1] and
                    # Check if we can extend backwards
                    (x + 3 >= width or y == 0 or grid[y - 1, x + 3] == 0) and
                    # Check if we can extend forwards
                    (y + 2 >= height or x - 1 < 0 or grid[y + 2, x] == 0)):
                    count += 1

        return count

    def _calculate_bumpiness(self, grid: np.ndarray) -> float:
        """
        f4_column_bumpiness: Sum of height differences between adjacent columns.
        Lower values are better (more flat surface for placing blocks).
        """
        height, width = grid.shape
        bumpiness = 0.0

        # Calculate height of each column (first non-zero from bottom, or height if empty)
        column_heights = []
        for x in range(width):
            height_col = 0
            for y in range(height - 1, -1, -1):  # Start from bottom
                if grid[y, x] != 0:
                    height_col = height - y
                    break
            column_heights.append(height_col)

        # Sum differences between adjacent columns
        for i in range(len(column_heights) - 1):
            bumpiness += abs(column_heights[i] - column_heights[i + 1])

        return bumpiness

    def _calculate_center_bias(self, state: GameState) -> float:
        """
        f5_center_bias: Reward for early game placement in center columns.
        Higher value in early game encourages building from center outward.
        """
        # Only apply in early game (turns 1-10)
        if state.turn_number >= 10:
            return 0.0

        center_columns = {3, 4, 5}  # 0-indexed columns 3,4,5
        valid_slots = state.get_valid_slots()

        # Count how many valid slots are in center columns
        center_slots = sum(1 for x, y in valid_slots if x in center_columns)
        total_slots = len(valid_slots)

        if total_slots == 0:
            return 0.0

        # Return ratio of center slots (higher is better)
        return center_slots / total_slots

    def _count_isolated_slots(self, state: GameState) -> float:
        """
        f6_isolated_slots: Count empty slots completely surrounded by filled slots.
        These are bad because they limit diagonal connections.
        """
        isolated_count = 0
        grid_2d = state.get_grid_2d()
        height, width = grid_2d.shape

        valid_slots = state.get_valid_slots()

        for slot_x, slot_y in valid_slots:
            # Check if this slot is isolated
            # A slot is isolated if all adjacent positions (that exist) are filled
            isolated = True

            # Check 8 neighbors (including diagonals)
            for dy in [-1, 0, 1]:
                for dx in [-1, 0, 1]:
                    if dx == 0 and dy == 0:
                        continue  # Skip the slot itself

                    neighbor_x, neighbor_y = slot_x + dx, slot_y + dy

                    # Check if neighbor is within bounds
                    if 0 <= neighbor_x < width and 0 <= neighbor_y < height:
                        # If neighbor is empty, then slot is not isolated
                        # But we need to check if the neighbor position is part of a valid slot
                        # For simplicity, we'll check if the cell itself is empty
                        if grid_2d[neighbor_y, neighbor_x] == 0:
                            isolated = False
                            break
                if not isolated:
                    break

            if isolated:
                isolated_count += 1

        return isolated_count

    def _count_dead_ends(self, grid: np.ndarray) -> float:
        """
        f7_dead_ends: Count empty positions where a number is blocked
        by different numbers on both sides in a line.
        """
        count = 0
        height, width = grid.shape

        # Check horizontal dead ends
        for y in range(height):
            for x in range(width):
                if grid[y, x] == 0:  # Empty cell
                    # Check left and right
                    left_val = grid[y, x - 1] if x > 0 else 0
                    right_val = grid[y, x + 1] if x < width - 1 else 0

                    # Dead end if both sides have numbers and they're different from each other
                    # (or one side is boundary and other has a number)
                    if ((left_val != 0 and right_val != 0 and left_val != right_val) or
                        (x == 0 and right_val != 0) or  # Left boundary, right has number
                        (x == width - 1 and left_val != 0)):  # Right boundary, left has number
                        count += 1

        # Check vertical dead ends
        for x in range(width):
            for y in range(height):
                if grid[y, x] == 0:  # Empty cell
                    # Check up and down
                    up_val = grid[y - 1, x] if y > 0 else 0
                    down_val = grid[y + 1, x] if y < height - 1 else 0

                    if ((up_val != 0 and down_val != 0 and up_val != down_val) or
                        (y == 0 and down_val != 0) or
                        (y == height - 1 and up_val != 0)):
                        count += 1

        return count

    def _get_max_height(self, grid: np.ndarray) -> float:
        """
        f8_max_height: Maximum height of any column.
        """
        height, width = grid.shape
        max_height = 0

        for x in range(width):
            for y in range(height):
                if grid[y, x] != 0:
                    column_height = height - y
                    max_height = max(max_height, column_height)
                    break

        return float(max_height)

    def _calculate_number_density(self, grid: np.ndarray, number: int) -> float:
        """
        f9-f12_number_density: Measure of clustering for a specific number.
        Higher values indicate more clustering (numbers grouped together).
        """
        height, width = grid.shape
        total_pairs = 0
        adjacent_pairs = 0

        # Count all occurrences of the number
        positions = []
        for y in range(height):
            for x in range(width):
                if grid[y, x] == number:
                    positions.append((y, x))

        if len(positions) < 2:
            return 0.0

        # Count adjacent pairs (including diagonals)
        for i, (y1, x1) in enumerate(positions):
            for j, (y2, x2) in enumerate(positions[i+1:], i+1):
                # Check if positions are adjacent (including diagonals)
                if abs(y2 - y1) <= 1 and abs(x2 - x1) <= 1:
                    adjacent_pairs += 1

        # Density ratio: adjacent pairs / total possible pairs
        total_possible = len(positions) * (len(positions) - 1) / 2
        if total_possible == 0:
            return 0.0

        return adjacent_pairs / total_possible

    def _count_vertical_matches(self, grid: np.ndarray) -> float:
        """
        f13_vertical_match_interfaces: Count vertical matches between slots.
        Looks for same numbers vertically adjacent in the same column.
        """
        count = 0
        height, width = grid.shape

        # Check vertical adjacency in each column
        for x in range(width):
            for y in range(height - 1):
                if grid[y, x] != 0 and grid[y, x] == grid[y + 1, x]:
                    count += 1

        return float(count)

    def _count_diagonal_cross_points(self, grid: np.ndarray) -> float:
        """
        f15_diagonal_cross_points: Count empty cells that lie on multiple
        potential diagonal lines (strategic positions).
        """
        count = 0
        height, width = grid.shape

        for y in range(height):
            for x in range(width):
                if grid[y, x] == 0:  # Empty cell
                    # Count how many diagonal lines pass through this cell
                    diagonal_lines = 0

                    # Check NW-SE diagonal (top-left to bottom-right)
                    # Look for same color numbers on this diagonal
                    if self._has_diagonal_pair(grid, y, x, -1, -1, 1, 1):
                        diagonal_lines += 1

                    # Check NE-SW diagonal (top-right to bottom-left)
                    if self._has_diagonal_pair(grid, y, x, -1, 1, 1, -1):
                        diagonal_lines += 1

                    # If this cell lies on 2 or more diagonal lines, it's a cross point
                    if diagonal_lines >= 2:
                        count += 1

        return float(count)

    def _has_diagonal_pair(self, grid: np.ndarray, y: int, x: int,
                          dy1: int, dx1: int, dy2: int, dx2: int) -> bool:
        """
        Helper to check if there's a pair of matching numbers on a diagonal
        passing through (y,x) in the direction specified.
        """
        height, width = grid.shape

        # Check in positive direction
        y1, x1 = y + dy2, x + dx2
        if (0 <= y1 < height and 0 <= x1 < width and grid[y1, x1] != 0):
            val = grid[y1, x1]
            # Check in negative direction for matching pair
            y2, x2 = y + dy1, x + dx1
            if (0 <= y2 < height and 0 <= x2 < width and grid[y2, x2] == val):
                return True

        # Check the other way around
        y1, x1 = y + dy1, x + dx1
        if (0 <= y1 < height and 0 <= x1 < width and grid[y1, x1] != 0):
            val = grid[y1, x1]
            y2, x2 = y + dy2, x + dx2
            if (0 <= y2 < height and 0 <= x2 < width and grid[y2, x2] == val):
                return True

        return False
