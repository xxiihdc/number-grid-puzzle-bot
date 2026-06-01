#!/usr/bin/env python3
"""Focused checks for the offline known-future comparison baseline."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.foresight import optimize_known_blocks, replay_slots, simulate_greedy_board_score


def test_two_turn_exhaustive_beam_is_at_least_as_strong_as_greedy():
    blocks = ((7, 8, 9), (7, 8, 9))
    greedy = simulate_greedy_board_score(blocks)
    foresight = optimize_known_blocks(blocks, beam_width=729)

    assert len(foresight.slots) == 2
    assert len(foresight.turn_scores) == 2
    assert foresight.final_score >= greedy.final_score


def test_invalid_beam_width_is_rejected():
    try:
        optimize_known_blocks(((7, 8, 9),), beam_width=0)
    except ValueError:
        pass
    else:
        raise AssertionError("Expected invalid beam width rejection")


def test_replay_slots_returns_final_board():
    blocks = ((7, 8, 9), (10, 10, 10))
    state = replay_slots(blocks, ((0, 0), (1, 3)))

    assert state.turn_number == 2
    assert tuple(state.get_grid_2d()[0:3, 0]) == blocks[0]
    assert tuple(state.get_grid_2d()[3:6, 1]) == blocks[1]


if __name__ == "__main__":
    test_two_turn_exhaustive_beam_is_at_least_as_strong_as_greedy()
    test_invalid_beam_width_is_rejected()
    test_replay_slots_returns_final_board()
    print("PASS: offline foresight checks")
