#!/usr/bin/env python3
"""Deterministic game-mode performance gate for budgeted Expectimax."""

import os
import random
import sys
import time
from dataclasses import dataclass
from typing import List, Optional

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bot"))

from bot.expectimax import ExpectimaxSearch
from bot.features import FeaturePool
from bot.game_state import GameState

EXTERNAL_MOVE_LIMIT_SECONDS = 0.200
GAME_SEEDS = tuple(range(2026053001, 2026053011))


@dataclass(frozen=True)
class MoveTiming:
    game_number: int
    turn: int
    elapsed_seconds: float
    completed_depth: int
    target_depth: int
    fallback_used: bool
    fallback_reason: Optional[str]


def _target_depth(turn: int) -> int:
    if turn <= 10:
        return 2
    if turn <= 20:
        return 3
    return 5


def run_performance_gate() -> List[MoveTiming]:
    """Run ten fixed-seed games and assert the externally visible deadline."""
    timings = []

    for game_number, seed in enumerate(GAME_SEEDS, start=1):
        state = GameState()
        search_engine = ExpectimaxSearch(FeaturePool())
        rng = random.Random(seed)

        for turn in range(1, GameState.TOTAL_TURNS + 1):
            block = state.spawn_block(rng)
            available_slots = set(state.get_valid_slots())
            target_depth = _target_depth(turn)

            started = time.perf_counter()
            slot, _ = search_engine.search(state, block, depth=target_depth)
            elapsed = time.perf_counter() - started
            stats = search_engine.get_last_search_stats()

            assert slot in available_slots, (
                f"Game {game_number}, turn {turn}: invalid slot {slot}"
            )
            assert elapsed <= EXTERNAL_MOVE_LIMIT_SECONDS, (
                f"Game {game_number}, turn {turn}: {elapsed * 1000:.2f}ms exceeds "
                f"{EXTERNAL_MOVE_LIMIT_SECONDS * 1000:.0f}ms"
            )

            timings.append(
                MoveTiming(
                    game_number=game_number,
                    turn=turn,
                    elapsed_seconds=elapsed,
                    completed_depth=stats.completed_depth,
                    target_depth=stats.target_depth,
                    fallback_used=stats.fallback_used,
                    fallback_reason=stats.fallback_reason,
                )
            )
            print(
                f"game={game_number:02d} turn={turn:02d} "
                f"elapsed={elapsed * 1000:7.2f}ms "
                f"depth={stats.completed_depth}/{stats.target_depth} "
                f"fallback={stats.fallback_used} reason={stats.fallback_reason}"
            )
            state.make_move(slot, block)

        assert state.turn_number == GameState.TOTAL_TURNS
        assert (state.grid != 0).sum() == GameState.TOTAL_CELLS

    return timings


if __name__ == "__main__":
    results = run_performance_gate()
    slowest = max(results, key=lambda timing: timing.elapsed_seconds)
    print("=" * 72)
    print(
        f"PASS: {len(results)} valid moves across {len(GAME_SEEDS)} games; "
        f"slowest={slowest.elapsed_seconds * 1000:.2f}ms "
        f"at game={slowest.game_number}, turn={slowest.turn}; "
        f"limit={EXTERNAL_MOVE_LIMIT_SECONDS * 1000:.0f}ms"
    )
