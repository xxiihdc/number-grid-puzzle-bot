"""Board evaluation helpers for the main bot implementation."""

from typing import List, Sequence, Tuple

import numpy as np

BOARD_SIZE = 9
Coord = Tuple[int, int]
Streak = List[Coord]


def get_lines_with_coords(board: np.ndarray) -> List[List[Tuple[int, Coord]]]:
    """Return all horizontal, vertical, and diagonal board lines with coordinates."""
    lines = []

    for row in range(BOARD_SIZE):
        lines.append([(int(board[row, col]), (row, col)) for col in range(BOARD_SIZE)])

    for col in range(BOARD_SIZE):
        lines.append([(int(board[row, col]), (row, col)) for row in range(BOARD_SIZE)])

    for offset in range(-(BOARD_SIZE - 1), BOARD_SIZE):
        line = [
            (int(board[row, row - offset]), (row, row - offset))
            for row in range(BOARD_SIZE)
            if 0 <= row - offset < BOARD_SIZE
        ]
        if line:
            lines.append(line)

    for row_col_sum in range(2 * BOARD_SIZE - 1):
        line = [
            (int(board[row, row_col_sum - row]), (row, row_col_sum - row))
            for row in range(BOARD_SIZE)
            if 0 <= row_col_sum - row < BOARD_SIZE
        ]
        if line:
            lines.append(line)

    return lines


def calculate_streak_score(count: int, is_final: bool) -> int:
    """Calculate score for a contiguous same-number streak."""
    if count == 2 and not is_final:
        return 2
    if count == 3:
        return 10
    if count == 4:
        return 25
    if count >= 5:
        return 50 * (count - 4)
    return 0


def evaluate_board(board: np.ndarray, is_final: bool = False, return_streaks: bool = False):
    """Evaluate a board and optionally return winning streak coordinates."""
    score = 0
    winning_streaks: List[Streak] = []

    for line in get_lines_with_coords(board):
        if len(line) < 2:
            continue

        streak_coords = [line[0][1]]
        streak_value = line[0][0]

        for value, coord in line[1:]:
            if value == streak_value and value != 0:
                streak_coords.append(coord)
            else:
                points = calculate_streak_score(len(streak_coords), is_final)
                if points > 0:
                    score += points
                    if return_streaks:
                        winning_streaks.append(streak_coords)
                streak_coords = [coord]
                streak_value = value

        points = calculate_streak_score(len(streak_coords), is_final)
        if points > 0:
            score += points
            if return_streaks:
                winning_streaks.append(streak_coords)

    if return_streaks:
        return score, winning_streaks
    return score

