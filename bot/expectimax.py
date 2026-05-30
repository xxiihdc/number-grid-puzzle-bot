#!/usr/bin/env python3
"""Budgeted Expectimax search for real-time game-mode move selection."""

import math
import logging
import os
import random
import time
import zlib
from dataclasses import dataclass
from typing import Dict, List, Optional, Sequence, Tuple

from game_state import GameState
from features import FeaturePool

Slot = Tuple[int, int]
Block = Tuple[int, int, int]


@dataclass(frozen=True)
class SearchStats:
    """Metrics from the most recent search call."""

    elapsed_seconds: float
    target_depth: int
    completed_depth: int
    timed_out: bool
    fallback_used: bool
    fallback_reason: Optional[str]
    nodes_evaluated: int
    cache_entries: int


@dataclass(frozen=True)
class _Candidate:
    slot: Slot
    immediate_score: int
    fallback_value: float


class _SearchTimeout(Exception):
    """Raised internally when a deeper iteration exceeds the search budget."""


class ExpectimaxSearch:
    """Select moves with deterministic sampled lookahead under a hard deadline."""

    DEFAULT_TIMEOUT = 0.180
    BEAM_WIDTH = 3
    CHANCE_SAMPLES = 2
    MAX_CACHE_ENTRIES = 10_000

    def __init__(self, feature_pool: FeaturePool):
        self.feature_pool = feature_pool
        self.transposition_table: Dict[Tuple, float] = {}
        self.nodes_evaluated = 0
        self._chromosome = None
        self._deadline: Optional[float] = None
        self.timeout_occurred = False
        self._last_search_stats = SearchStats(
            0.0, 0, 0, False, False, None, 0, 0
        )

    def search(self, state: GameState, block_values: Sequence[int], depth: int,
               timeout: Optional[float] = DEFAULT_TIMEOUT) -> Tuple[Optional[Slot], float]:
        """
        Return the best available slot for the already-spawned block.

        A complete depth-1 scan runs first so the method always has a valid fallback.
        Deeper iterations are published only after they complete, avoiding candidate
        ordering bias when the deadline expires partway through an iteration.
        """
        started = time.perf_counter()
        self.nodes_evaluated = 0
        self.timeout_occurred = False
        self.clear_transposition_table()
        self._deadline = None if timeout is None else started + max(0.0, timeout)

        target_depth = max(1, depth)
        block = self._normalize_block(block_values)
        valid_slots = state.get_valid_slots()
        if not valid_slots:
            self._record_stats(started, target_depth, 0, "no_valid_slots")
            return None, 0.0

        working_state = state.copy()

        # This full root scan is intentionally deadline-independent: it is small and
        # guarantees a legal move even when a caller supplies a very small timeout.
        root_candidates = self._rank_candidates(
            working_state, block, valid_slots, enforce_deadline=False
        )
        best_slot = root_candidates[0].slot
        best_value = root_candidates[0].fallback_value
        completed_depth = 1

        for iteration_depth in range(2, target_depth + 1):
            try:
                self._check_deadline()
                iteration_slot, iteration_value = self._search_root(
                    working_state, block, root_candidates, iteration_depth
                )
            except _SearchTimeout:
                self.timeout_occurred = True
                break

            best_slot = iteration_slot
            best_value = iteration_value
            completed_depth = iteration_depth

        if self._deadline is not None and time.perf_counter() >= self._deadline:
            self.timeout_occurred = completed_depth < target_depth

        fallback_reason = "deadline_exceeded" if self.timeout_occurred else None
        self._record_stats(started, target_depth, completed_depth, fallback_reason)
        if self._last_search_stats.fallback_used:
            self._log_fallback(state, block, best_slot)
        return best_slot, best_value

    def _search_root(self, state: GameState, block: Block,
                     root_candidates: List[_Candidate], depth: int) -> Tuple[Slot, float]:
        """Expand the strongest root candidates for one complete depth iteration."""
        best_slot = root_candidates[0].slot
        best_value = -math.inf

        for candidate in root_candidates[:self.BEAM_WIDTH]:
            self._check_deadline()
            x, y = candidate.slot
            score_gained = state.place_block(x, y, block)
            try:
                value = score_gained + self._chance_value(state, depth - 1)
            finally:
                state._undo_block(x, y, score_gained)

            if value > best_value:
                best_value = value
                best_slot = candidate.slot

        return best_slot, best_value

    def _chance_value(self, state: GameState, depth: int) -> float:
        """Average future values over a reproducible sample of random blocks."""
        self._check_deadline()
        state_key = self._get_state_key("chance", state, None, depth)
        cached_value = self.transposition_table.get(state_key)
        if cached_value is not None:
            return cached_value

        self.nodes_evaluated += 1
        total_value = 0.0
        for future_block in self._sample_future_blocks(state):
            self._check_deadline()
            total_value += self._max_value(state, future_block, depth)

        expected_value = total_value / self.CHANCE_SAMPLES
        self._cache_value(state_key, expected_value)
        return expected_value

    def _max_value(self, state: GameState, block: Block, depth: int) -> float:
        """Choose the strongest slot for a sampled future block."""
        self._check_deadline()
        state_key = self._get_state_key("max", state, block, depth)
        cached_value = self.transposition_table.get(state_key)
        if cached_value is not None:
            return cached_value

        self.nodes_evaluated += 1
        valid_slots = state.get_valid_slots()
        if not valid_slots or state.is_game_over():
            value = self._evaluate_state(state)
            self._cache_value(state_key, value)
            return value

        candidates = self._rank_candidates(state, block, valid_slots)
        if depth <= 1:
            value = candidates[0].fallback_value
            self._cache_value(state_key, value)
            return value

        best_value = -math.inf
        for candidate in candidates[:self.BEAM_WIDTH]:
            self._check_deadline()
            x, y = candidate.slot
            score_gained = state.place_block(x, y, block)
            try:
                value = score_gained + self._chance_value(state, depth - 1)
            finally:
                state._undo_block(x, y, score_gained)
            best_value = max(best_value, value)

        self._cache_value(state_key, best_value)
        return best_value

    def _rank_candidates(self, state: GameState, block: Block,
                         valid_slots: Sequence[Slot],
                         enforce_deadline: bool = True) -> List[_Candidate]:
        """Rank slots by immediate score plus heuristic leaf evaluation."""
        candidates = []
        for x, y in valid_slots:
            if enforce_deadline:
                self._check_deadline()

            score_gained = state.place_block(x, y, block)
            try:
                self.nodes_evaluated += 1
                fallback_value = score_gained + self._evaluate_state(state)
            finally:
                state._undo_block(x, y, score_gained)

            candidates.append(_Candidate((x, y), score_gained, fallback_value))

        candidates.sort(key=lambda candidate: candidate.fallback_value, reverse=True)
        return candidates

    def _sample_future_blocks(self, state: GameState) -> Tuple[Block, ...]:
        """Generate stable samples without consuming the game RNG stream."""
        seed = zlib.crc32(state.grid.tobytes())
        seed = zlib.crc32(state.turn_number.to_bytes(2, "little"), seed)
        seed = zlib.crc32(state.total_score.to_bytes(4, "little", signed=True), seed)
        rng = random.Random(seed)
        numbers = GameState.VALID_NUMBER_SEQUENCE
        return tuple(
            tuple(rng.choice(numbers) for _ in range(GameState.BLOCK_HEIGHT))
            for _ in range(self.CHANCE_SAMPLES)
        )

    def _get_state_key(self, node_type: str, state: GameState,
                       block: Optional[Block], depth: int) -> Tuple:
        """Create a collision-safe cache key for one search node."""
        return (
            node_type,
            state.grid.tobytes(),
            state.total_score,
            state.turn_number,
            block,
            depth,
        )

    def _cache_value(self, state_key: Tuple, value: float) -> None:
        if len(self.transposition_table) < self.MAX_CACHE_ENTRIES:
            self.transposition_table[state_key] = value

    def _check_deadline(self) -> None:
        if self._deadline is not None and time.perf_counter() >= self._deadline:
            raise _SearchTimeout

    def _normalize_block(self, block_values: Sequence[int]) -> Block:
        block = tuple(int(value) for value in block_values)
        if len(block) != GameState.BLOCK_HEIGHT:
            raise ValueError("A block must contain exactly three values")
        if any(value not in GameState.VALID_NUMBERS for value in block):
            raise ValueError("Block values must be in {7, 8, 9, 10}")
        return block

    def _record_stats(self, started: float, target_depth: int,
                      completed_depth: int,
                      fallback_reason: Optional[str] = None) -> None:
        fallback_used = completed_depth < target_depth
        self._last_search_stats = SearchStats(
            elapsed_seconds=time.perf_counter() - started,
            target_depth=target_depth,
            completed_depth=completed_depth,
            timed_out=self.timeout_occurred,
            fallback_used=fallback_used,
            fallback_reason=fallback_reason if fallback_used else None,
            nodes_evaluated=self.nodes_evaluated,
            cache_entries=len(self.transposition_table),
        )

    def _log_fallback(self, state: GameState, block: Block,
                      selected_slot: Optional[Slot]) -> None:
        """Append one structured fallback event without configuring global logging."""
        stats = self._last_search_stats
        logger = logging.getLogger("bot.inference.fallback")
        if not logger.handlers:
            log_path = os.environ.get(
                "BOT_INFERENCE_LOG_PATH", "inference_performance.log"
            )
            handler = logging.FileHandler(log_path, mode="a", encoding="utf-8")
            handler.setFormatter(logging.Formatter("%(asctime)s %(message)s"))
            logger.addHandler(handler)
            logger.setLevel(logging.INFO)
            logger.propagate = False

        logger.info(
            "event=fallback turn=%d block=%s slot=%s reason=%s "
            "elapsed_ms=%.2f completed_depth=%d target_depth=%d "
            "nodes=%d cache_entries=%d",
            state.turn_number + 1,
            block,
            selected_slot,
            stats.fallback_reason,
            stats.elapsed_seconds * 1000,
            stats.completed_depth,
            stats.target_depth,
            stats.nodes_evaluated,
            stats.cache_entries,
        )

    def _evaluate_state(self, state: GameState) -> float:
        """Evaluate one leaf with either evolved or default heuristic weights."""
        if self._chromosome is not None:
            return self._chromosome.get_fitness(state, self.feature_pool)
        feature_values = self.feature_pool.extract_all_features(state)
        return sum(feature_values.values())

    def set_chromosome(self, chromosome) -> None:
        """Set the chromosome weights used for leaf evaluation."""
        self._chromosome = chromosome

    def get_nodes_evaluated(self) -> int:
        """Return the number of nodes evaluated during the latest search."""
        return self.nodes_evaluated

    def get_last_search_stats(self) -> SearchStats:
        """Return metrics for the most recent search call."""
        return self._last_search_stats

    def clear_transposition_table(self) -> None:
        """Clear cached node values."""
        self.transposition_table.clear()
