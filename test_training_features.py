#!/usr/bin/env python3
"""Controlled-board checks for generalized training line-window features."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.features import FeaturePool
from bot.game_state import GameState


def _state(values):
    state = GameState()
    for (x, y), value in values.items():
        state.grid[state._to_index(x, y)] = value
    return state


def _features(values):
    return FeaturePool().extract_all_features(_state(values))


def test_expanded_feature_names():
    names = FeaturePool().get_feature_names()
    assert names[-4:] == [
        "f16_open_single_windows",
        "f17_open_pair_windows",
        "f18_blocked_windows",
        "f19_multi_line_completion_cells",
    ]


def test_open_single_window_count():
    features = _features({(0, 0): 7})
    assert features["f16_open_single_windows"] == 3.0


def test_open_pair_windows_cover_all_directions():
    coordinate_pairs = (
        ((0, 0), (1, 0)),
        ((0, 0), (0, 1)),
        ((0, 0), (1, 1)),
        ((8, 0), (7, 1)),
    )
    for first, second in coordinate_pairs:
        features = _features({first: 7, second: 7})
        assert features["f17_open_pair_windows"] == 1.0


def test_blocked_window_count():
    features = _features({(0, 0): 7, (1, 0): 8})
    assert features["f18_blocked_windows"] == 1.0


def test_multi_line_completion_cell_count():
    features = _features({
        (3, 4): 7,
        (5, 4): 7,
        (4, 3): 7,
        (4, 5): 7,
    })
    assert features["f19_multi_line_completion_cells"] >= 1.0


if __name__ == "__main__":
    test_expanded_feature_names()
    test_open_single_window_count()
    test_open_pair_windows_cover_all_directions()
    test_blocked_window_count()
    test_multi_line_completion_cell_count()
    print("PASS: training feature checks")
