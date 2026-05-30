#!/usr/bin/env python3
"""Focused functional checks for the Number Grid Puzzle Bot."""

import logging
import os
import random
import sys
import tempfile

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.expectimax import ExpectimaxSearch
from bot.features import FeaturePool
from bot.game_state import GameState


def _target_depth(turn: int) -> int:
    if turn <= 10:
        return 2
    if turn <= 20:
        return 3
    return 5


def test_game_state() -> None:
    """A pre-spawned block must be placed unchanged."""
    state = GameState()
    block = (7, 8, 9)
    slot = state.get_valid_slots()[0]

    score = state.make_move(slot, block)

    assert score == 0
    assert tuple(state.get_grid_2d()[0:3, 0]) == block
    assert state.turn_number == 1
    assert slot not in state.get_valid_slots()


def test_spawn_block() -> None:
    """Seeded spawning is reproducible and does not modify the board."""
    state = GameState()
    first = state.spawn_block(random.Random(12345))
    second = state.spawn_block(random.Random(12345))

    assert first == second
    assert len(first) == 3
    assert all(value in GameState.VALID_NUMBERS for value in first)
    assert state.turn_number == 0
    assert not state.grid.any()


def test_features() -> None:
    """Feature extraction still reports the state after deterministic placement."""
    state = GameState()
    state.make_move((0, 0), (7, 7, 7))

    features = FeaturePool().extract_all_features(state)

    assert features["f1_actual_score"] > 0
    assert features["f13_vertical_match_interfaces"] == 2.0


def test_expectimax_preserves_state() -> None:
    """Search must undo every simulated move before returning."""
    state = GameState()
    original_grid = state.grid.copy()
    original_slots = state.occupied_slots.copy()
    search_engine = ExpectimaxSearch(FeaturePool())

    slot, _ = search_engine.search(state, (7, 8, 9), depth=2)
    stats = search_engine.get_last_search_stats()

    assert slot in state.get_valid_slots()
    assert (state.grid == original_grid).all()
    assert state.occupied_slots == original_slots
    assert state.turn_number == 0
    assert stats.completed_depth >= 1
    assert stats.cache_entries <= search_engine.MAX_CACHE_ENTRIES


def test_expectimax_timeout_returns_valid_fallback() -> None:
    """A deadline hit during deeper search must keep the complete root result."""
    state = GameState()
    search_engine = ExpectimaxSearch(FeaturePool())

    slot, _ = search_engine.search(state, (7, 8, 9), depth=5, timeout=0.0)
    stats = search_engine.get_last_search_stats()

    assert slot in state.get_valid_slots()
    assert stats.completed_depth == 1
    assert stats.timed_out
    assert stats.fallback_used
    assert stats.fallback_reason == "deadline_exceeded"


def test_expectimax_fallback_writes_structured_log() -> None:
    """Fallback diagnostics must be persisted for algorithm analysis."""
    state = GameState()
    search_engine = ExpectimaxSearch(FeaturePool())

    with tempfile.TemporaryDirectory() as temp_dir:
        log_path = os.path.join(temp_dir, "inference.log")
        original_log_path = os.environ.get("BOT_INFERENCE_LOG_PATH")
        os.environ["BOT_INFERENCE_LOG_PATH"] = log_path
        logger = logging.getLogger("bot.inference.fallback")
        for handler in logger.handlers[:]:
            logger.removeHandler(handler)
            handler.close()

        try:
            search_engine.search(state, (7, 8, 9), depth=5, timeout=0.0)
            for handler in logger.handlers:
                handler.flush()
            with open(log_path, encoding="utf-8") as log_file:
                log_contents = log_file.read()
        finally:
            for handler in logger.handlers[:]:
                logger.removeHandler(handler)
                handler.close()
            if original_log_path is None:
                os.environ.pop("BOT_INFERENCE_LOG_PATH", None)
            else:
                os.environ["BOT_INFERENCE_LOG_PATH"] = original_log_path

    assert "event=fallback" in log_contents
    assert "reason=deadline_exceeded" in log_contents
    assert "completed_depth=1 target_depth=5" in log_contents


def test_last_slot_returns_promptly() -> None:
    """The final aligned slot is selected without invalid simulation."""
    state = GameState()
    for slot in state.get_valid_slots()[:-1]:
        state.make_move(slot, (7, 8, 9))

    expected_slot = state.get_valid_slots()[0]
    search_engine = ExpectimaxSearch(FeaturePool())
    slot, _ = search_engine.search(state, (10, 10, 10), depth=5)

    assert slot == expected_slot
    assert search_engine.get_last_search_stats().elapsed_seconds < 0.2


def test_complete_game_packing() -> None:
    """A deterministic full game still places exactly 27 aligned blocks."""
    state = GameState()
    search_engine = ExpectimaxSearch(FeaturePool())
    rng = random.Random(20260530)

    for turn in range(1, GameState.TOTAL_TURNS + 1):
        block = state.spawn_block(rng)
        available_slots = set(state.get_valid_slots())
        slot, _ = search_engine.search(
            state, block, depth=_target_depth(turn), timeout=0.0
        )
        assert slot in available_slots
        state.make_move(slot, block)

    assert state.turn_number == GameState.TOTAL_TURNS
    assert len(state.occupied_slots) == GameState.TOTAL_TURNS
    assert not state.get_valid_slots()
    assert (state.grid != 0).sum() == GameState.TOTAL_CELLS


if __name__ == "__main__":
    tests = [
        test_game_state,
        test_spawn_block,
        test_features,
        test_expectimax_preserves_state,
        test_expectimax_timeout_returns_valid_fallback,
        test_expectimax_fallback_writes_structured_log,
        test_last_slot_returns_promptly,
        test_complete_game_packing,
    ]

    print("Number Grid Puzzle Bot - Functional Checks")
    print("=" * 50)
    for test in tests:
        test()
        print(f"PASS: {test.__name__}")
    print("=" * 50)
    print(f"All {len(tests)} checks passed.")
