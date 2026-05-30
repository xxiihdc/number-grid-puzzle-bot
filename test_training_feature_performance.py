#!/usr/bin/env python3
"""Bounded extraction benchmark for the expanded offline-training feature pool."""

import os
import sys
from time import perf_counter

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.features import FeaturePool
from bot.game_state import GameState


def test_feature_extraction_benchmark():
    state = GameState()
    numbers = (7, 8, 9, 10)
    for index, slot in enumerate(state.get_valid_slots()[:18]):
        state.make_move(slot, (
            numbers[index % 4],
            numbers[(index + 1) % 4],
            numbers[(index + 2) % 4],
        ))

    pool = FeaturePool()
    iterations = 1000
    started = perf_counter()
    for _ in range(iterations):
        pool.extract_all_features(state)
    elapsed = perf_counter() - started
    per_extract_ms = elapsed / iterations * 1000
    print(
        f"Feature extraction benchmark: iterations={iterations} "
        f"elapsed={elapsed:.4f}s per_extract={per_extract_ms:.4f}ms"
    )
    assert per_extract_ms < 5.0


if __name__ == "__main__":
    test_feature_extraction_benchmark()
    print("PASS: training feature performance check")
