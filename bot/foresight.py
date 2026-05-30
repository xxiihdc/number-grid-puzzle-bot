"""Offline full-sequence baselines for deterministic block scenarios."""

from dataclasses import dataclass
from typing import Dict, Sequence, Tuple

from game_state import GameState
from scoring import evaluate_board

Slot = Tuple[int, int]
Block = Tuple[int, int, int]


@dataclass(frozen=True)
class ForesightResult:
    """One completed placement path and its board score after every turn."""

    slots: Tuple[Slot, ...]
    turn_scores: Tuple[int, ...]
    final_score: int
    expanded_states: int


@dataclass
class _BeamState:
    state: GameState
    slots: Tuple[Slot, ...]
    rank_score: int


def _normalize_blocks(blocks: Sequence[Sequence[int]]) -> Tuple[Block, ...]:
    normalized = tuple(tuple(int(value) for value in block) for block in blocks)
    if not normalized or len(normalized) > GameState.TOTAL_TURNS:
        raise ValueError("blocks must contain between 1 and 27 turns")
    for block in normalized:
        if len(block) != GameState.BLOCK_HEIGHT:
            raise ValueError("each block must contain exactly three values")
        if any(value not in GameState.VALID_NUMBERS for value in block):
            raise ValueError("block values must be in {7, 8, 9, 10}")
    return normalized


def _board_score(state: GameState, is_final: bool) -> int:
    return int(evaluate_board(state.get_grid_2d(), is_final=is_final))


def _score_path(blocks: Tuple[Block, ...], slots: Tuple[Slot, ...]) -> Tuple[int, ...]:
    scores = []
    state = GameState()
    for turn_index, (block, slot) in enumerate(zip(blocks, slots)):
        state.make_move(slot, block)
        scores.append(_board_score(state, is_final=turn_index == len(blocks) - 1))
    return tuple(scores)


def replay_slots(blocks: Sequence[Sequence[int]], slots: Sequence[Slot]) -> GameState:
    """Replay a placement path and return its final state for reporting or display."""
    normalized = _normalize_blocks(blocks)
    normalized_slots = tuple(slots)
    if len(normalized_slots) != len(normalized):
        raise ValueError("slots must contain exactly one placement per block")
    state = GameState()
    for block, slot in zip(normalized, normalized_slots):
        state.make_move(slot, block)
    return state


def simulate_greedy_board_score(blocks: Sequence[Sequence[int]]) -> ForesightResult:
    """Choose the best currently visible board score without future knowledge."""
    normalized = _normalize_blocks(blocks)
    state = GameState()
    slots = []
    scores = []
    expanded_states = 0
    for turn_index, block in enumerate(normalized):
        is_final = turn_index == len(normalized) - 1
        best_slot = None
        best_score = -1
        for slot in state.get_valid_slots():
            x, y = slot
            score_gained = state.place_block(x, y, block)
            try:
                score = _board_score(state, is_final=is_final)
                expanded_states += 1
            finally:
                state._undo_block(x, y, score_gained)
            if score > best_score:
                best_slot = slot
                best_score = score
        if best_slot is None:
            raise RuntimeError("No valid slot available")
        state.make_move(best_slot, block)
        slots.append(best_slot)
        scores.append(best_score)
    return ForesightResult(tuple(slots), tuple(scores), scores[-1], expanded_states)


def optimize_known_blocks(blocks: Sequence[Sequence[int]], beam_width: int = 500) -> ForesightResult:
    """
    Use every future block to search for a strong completed placement path.

    This is an offline comparison baseline, not a proof of optimality: beam pruning
    discards paths with weaker intermediate boards to keep the 27-turn search usable.
    """
    normalized = _normalize_blocks(blocks)
    if beam_width <= 0:
        raise ValueError("beam_width must be positive")

    beam = [_BeamState(GameState(), (), 0)]
    expanded_states = 0
    for turn_index, block in enumerate(normalized):
        is_final = turn_index == len(normalized) - 1
        candidates: Dict[bytes, _BeamState] = {}
        for beam_state in beam:
            for slot in beam_state.state.get_valid_slots():
                state = beam_state.state.copy()
                state.make_move(slot, block)
                score = _board_score(state, is_final=is_final)
                expanded_states += 1
                candidate = _BeamState(state, beam_state.slots + (slot,), score)
                key = state.grid.tobytes()
                previous = candidates.get(key)
                if previous is None or candidate.rank_score > previous.rank_score:
                    candidates[key] = candidate
        if not candidates:
            raise RuntimeError("No candidate paths remain")
        beam = sorted(
            candidates.values(),
            key=lambda candidate: (candidate.rank_score, candidate.state.total_score),
            reverse=True,
        )[:beam_width]

    best = beam[0]
    turn_scores = _score_path(normalized, best.slots)
    return ForesightResult(best.slots, turn_scores, turn_scores[-1], expanded_states)
