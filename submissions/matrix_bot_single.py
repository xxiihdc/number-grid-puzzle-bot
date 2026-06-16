#!/usr/bin/env python3
"""Single-file Matrix Game bot for stdin/stdout judges.

Input:
  N
  a b c
  81 integers for our board, using -1 for empty cells
  N-1 opponent boards, ignored by this bot

Output:
  one slot id in [0, 26]

Slot numbering follows the common 3x9 slot view:
  0..8   -> y=0, x=0..8
  9..17  -> y=3, x=0..8
  18..26 -> y=6, x=0..8
"""

import random
import sys
import time
import zlib

SIZE = 9
CELLS = 81
BLOCK_H = 3
VALUES = (7, 8, 9, 10)
DIRECTIONS = ((1, 0), (0, 1), (1, 1), (1, -1))
SLOTS = tuple((slot % 9, (slot // 9) * 3) for slot in range(27))

BEAM_WIDTH = 3
CHANCE_SAMPLES = 2
TIME_LIMIT = 1.82
CACHE_LIMIT = 12000

# Active trained chromosome from training_runs/active_chromosome.json.
# Feature order matches feature_values().
WEIGHTS = (
    (
        (1, 88.892676765138), (0, 43.025910943015), (0, -75.629183954579),
        (0, 38.944320627167), (1, -17.538374761136), (1, -13.247043576316),
        (0, -24.421082008386), (0, 80.049502504429), (1, 20.689048086522),
        (0, 53.639057044733), (1, 67.510343980836), (1, -47.488555778381),
        (1, 64.641972871571), (0, -43.570935896193), (0, -20.286980598974),
        (0, -80.512853929371), (1, 75.494269753369), (1, -33.508936961402),
        (1, -28.819326167247),
    ),
    (
        (1, 84.33347862913), (0, 65.484503392716), (1, -65.350895582633),
        (0, 67.323856127292), (0, -93.410713406252), (0, 40.561324261925),
        (0, 31.715005887247), (1, -51.361510539496), (1, -36.550015694656),
        (0, 31.551866352826), (1, -22.581086865073), (1, 60.049316683512),
        (0, 16.063935570178), (0, -31.39228957404), (1, -75.825821841457),
        (0, -74.704528843995), (1, 49.940191128957), (0, -56.151154278971),
        (0, 58.553469491237),
    ),
    (
        (1, 75.843029686943), (0, 41.385126907777), (1, 62.031414178224),
        (0, 99.400734674437), (1, 50.584060237261), (1, 75.500088581324),
        (1, 19.708756773793), (1, -13.198276760067), (0, 44.86527806821),
        (1, 55.721429673343), (1, -26.103635426074), (1, 9.544787186431),
        (0, 94.386801612142), (1, -82.106204925023), (1, 8.085361984609),
        (0, 48.996278946544), (0, -45.773825409066), (0, 90.546796547327),
        (0, -16.369942784675),
    ),
)


class Timeout(Exception):
    pass


def idx(x, y):
    return y * SIZE + x


def slot_id(x, y):
    return (y // 3) * 9 + x


def occupied_slots(board):
    used = set()
    for sid, (x, y) in enumerate(SLOTS):
        if board[idx(x, y)] != 0 or board[idx(x, y + 1)] != 0 or board[idx(x, y + 2)] != 0:
            used.add(sid)
    return used


def valid_slots(board):
    return [
        sid for sid, (x, y) in enumerate(SLOTS)
        if board[idx(x, y)] == 0 and board[idx(x, y + 1)] == 0 and board[idx(x, y + 2)] == 0
    ]


def place(board, sid, block):
    x, y = SLOTS[sid]
    for dy, value in enumerate(block):
        board[idx(x, y + dy)] = value


def undo(board, sid):
    x, y = SLOTS[sid]
    for dy in range(3):
        board[idx(x, y + dy)] = 0


def placement_score(board, sid, block):
    x, y = SLOTS[sid]
    score = 0
    for offset, value in enumerate(block):
        cy0 = y + offset
        for dx, dy in DIRECTIONS:
            count_pos = 0
            cx, cy = x + dx, cy0 + dy
            while 0 <= cx < SIZE and 0 <= cy < SIZE and board[idx(cx, cy)] == value:
                count_pos += 1
                cx += dx
                cy += dy

            count_neg = 0
            cx, cy = x - dx, cy0 - dy
            while 0 <= cx < SIZE and 0 <= cy < SIZE and board[idx(cx, cy)] == value:
                count_neg += 1
                cx -= dx
                cy -= dy

            length = count_pos + 1 + count_neg
            if length >= 3:
                score += length - 2
    return score


def apply_score(board, sid, block):
    place(board, sid, block)
    return placement_score(board, sid, block)


def count_horizontal_pairs(board):
    count = 0
    for y in range(9):
        base = y * 9
        for x in range(7):
            value = board[base + x]
            if value and value == board[base + x + 1]:
                if (x == 0 or board[base + x - 1] == 0) and (x + 2 >= 9 or board[base + x + 2] == 0):
                    count += 1
    return float(count)


def count_diagonal_pairs(board):
    count = 0
    for y in range(7):
        for x in range(7):
            value = board[idx(x, y)]
            if value and value == board[idx(x + 1, y + 1)]:
                if (x == 0 or y == 0 or board[idx(x - 1, y - 1)] == 0) and board[idx(x + 2, y + 2)] == 0:
                    count += 1
            value = board[idx(x + 2, y)]
            if value and value == board[idx(x + 1, y + 1)]:
                if (x + 3 >= 9 or y == 0 or board[idx(x + 3, y - 1)] == 0) and (x - 1 < 0 or board[idx(x, y + 2)] == 0):
                    count += 1
    return float(count)


def bumpiness(board):
    heights = []
    for x in range(9):
        height = 0
        for y in range(8, -1, -1):
            if board[idx(x, y)]:
                height = 9 - y
                break
        heights.append(height)
    return float(sum(abs(heights[i] - heights[i + 1]) for i in range(8)))


def center_bias(board, turn):
    if turn >= 10:
        return 0.0
    slots = valid_slots(board)
    if not slots:
        return 0.0
    return sum(1 for sid in slots if SLOTS[sid][0] in (3, 4, 5)) / float(len(slots))


def isolated_slots(board):
    count = 0
    for sid in valid_slots(board):
        x, y = SLOTS[sid]
        isolated = True
        for dy in (-1, 0, 1):
            for dx in (-1, 0, 1):
                if dx == 0 and dy == 0:
                    continue
                nx, ny = x + dx, y + dy
                if 0 <= nx < 9 and 0 <= ny < 9 and board[idx(nx, ny)] == 0:
                    isolated = False
                    break
            if not isolated:
                break
        if isolated:
            count += 1
    return float(count)


def dead_ends(board):
    count = 0
    for y in range(9):
        for x in range(9):
            if board[idx(x, y)]:
                continue
            left = board[idx(x - 1, y)] if x > 0 else 0
            right = board[idx(x + 1, y)] if x < 8 else 0
            if (left and right and left != right) or (x == 0 and right) or (x == 8 and left):
                count += 1
            up = board[idx(x, y - 1)] if y > 0 else 0
            down = board[idx(x, y + 1)] if y < 8 else 0
            if (up and down and up != down) or (y == 0 and down) or (y == 8 and up):
                count += 1
    return float(count)


def max_height(board):
    result = 0
    for x in range(9):
        for y in range(9):
            if board[idx(x, y)]:
                result = max(result, 9 - y)
                break
    return float(result)


def density(board, number):
    positions = []
    for i, value in enumerate(board):
        if value == number:
            positions.append((i % 9, i // 9))
    n = len(positions)
    if n < 2:
        return 0.0
    adjacent = 0
    for i in range(n):
        x1, y1 = positions[i]
        for j in range(i + 1, n):
            x2, y2 = positions[j]
            if abs(x2 - x1) <= 1 and abs(y2 - y1) <= 1:
                adjacent += 1
    return adjacent / float(n * (n - 1) / 2)


def vertical_matches(board):
    count = 0
    for x in range(9):
        for y in range(8):
            value = board[idx(x, y)]
            if value and value == board[idx(x, y + 1)]:
                count += 1
    return float(count)


def has_diagonal_pair(board, x, y, dx1, dy1, dx2, dy2):
    x1, y1 = x + dx2, y + dy2
    if 0 <= x1 < 9 and 0 <= y1 < 9 and board[idx(x1, y1)]:
        value = board[idx(x1, y1)]
        x2, y2 = x + dx1, y + dy1
        if 0 <= x2 < 9 and 0 <= y2 < 9 and board[idx(x2, y2)] == value:
            return True
    x1, y1 = x + dx1, y + dy1
    if 0 <= x1 < 9 and 0 <= y1 < 9 and board[idx(x1, y1)]:
        value = board[idx(x1, y1)]
        x2, y2 = x + dx2, y + dy2
        if 0 <= x2 < 9 and 0 <= y2 < 9 and board[idx(x2, y2)] == value:
            return True
    return False


def diagonal_cross_points(board):
    count = 0
    for y in range(9):
        for x in range(9):
            if board[idx(x, y)]:
                continue
            lines = 0
            if has_diagonal_pair(board, x, y, -1, -1, 1, 1):
                lines += 1
            if has_diagonal_pair(board, x, y, 1, -1, -1, 1):
                lines += 1
            if lines >= 2:
                count += 1
    return float(count)


def line_window_metrics(board):
    open_single = 0
    open_pair = 0
    blocked = 0
    completions = {}
    for dx, dy in DIRECTIONS:
        for y in range(9):
            for x in range(9):
                end_x = x + 2 * dx
                end_y = y + 2 * dy
                if not (0 <= end_x < 9 and 0 <= end_y < 9):
                    continue
                coords = ((x, y), (x + dx, y + dy), (end_x, end_y))
                vals = [board[idx(cx, cy)] for cx, cy in coords]
                filled = [v for v in vals if v]
                distinct = set(filled)
                if len(distinct) > 1:
                    blocked += 1
                elif len(filled) == 1:
                    open_single += 1
                elif len(filled) == 2:
                    for coord, value in zip(coords, vals):
                        if value == 0:
                            completions[coord] = completions.get(coord, 0) + 1
                            break
                    open_pair += 1
    multi = sum(1 for value in completions.values() if value >= 2)
    return float(open_single), float(open_pair), float(blocked), float(multi)


def feature_values(board, turn):
    f16, f17, f18, f19 = line_window_metrics(board)
    return (
        0.0,
        count_horizontal_pairs(board),
        count_diagonal_pairs(board),
        bumpiness(board),
        center_bias(board, turn),
        isolated_slots(board),
        dead_ends(board),
        max_height(board),
        density(board, 7),
        density(board, 8),
        density(board, 9),
        density(board, 10),
        vertical_matches(board),
        float(27 - len(occupied_slots(board))),
        diagonal_cross_points(board),
        f16,
        f17,
        f18,
        f19,
    )


def evaluate(board, turn):
    phase = 0 if turn < 10 else 1 if turn < 20 else 2
    features = feature_values(board, turn)
    total = 0.0
    for value, (mask, weight) in zip(features, WEIGHTS[phase]):
        if mask:
            total += weight * value
    return total


def check_deadline(deadline):
    if time.perf_counter() >= deadline:
        raise Timeout


def future_blocks(board, turn):
    data = bytes((value + 1) & 255 for value in board)
    seed = zlib.crc32(data)
    seed = zlib.crc32(turn.to_bytes(2, "little"), seed)
    rng = random.Random(seed)
    return tuple(tuple(rng.choice(VALUES) for _ in range(3)) for _ in range(CHANCE_SAMPLES))


def rank_candidates(board, block, turn, deadline=None):
    candidates = []
    for sid in valid_slots(board):
        if deadline is not None:
            check_deadline(deadline)
        gained = apply_score(board, sid, block)
        try:
            value = gained + evaluate(board, turn + 1)
        finally:
            undo(board, sid)
        candidates.append((value, gained, sid))
    candidates.sort(reverse=True)
    return candidates


def chance_value(board, turn, depth, deadline, cache):
    check_deadline(deadline)
    key = ("c", tuple(board), turn, depth)
    if key in cache:
        return cache[key]
    total = 0.0
    for block in future_blocks(board, turn):
        total += max_value(board, block, turn, depth, deadline, cache)
    value = total / CHANCE_SAMPLES
    if len(cache) < CACHE_LIMIT:
        cache[key] = value
    return value


def max_value(board, block, turn, depth, deadline, cache):
    check_deadline(deadline)
    key = ("m", tuple(board), block, turn, depth)
    if key in cache:
        return cache[key]
    slots = valid_slots(board)
    if not slots or turn >= 27:
        value = evaluate(board, turn)
    else:
        candidates = rank_candidates(board, block, turn, deadline)
        if depth <= 1:
            value = candidates[0][0]
        else:
            value = -1.0e100
            for _, _, sid in candidates[:BEAM_WIDTH]:
                gained = apply_score(board, sid, block)
                try:
                    value = max(value, gained + chance_value(board, turn + 1, depth - 1, deadline, cache))
                finally:
                    undo(board, sid)
    if len(cache) < CACHE_LIMIT:
        cache[key] = value
    return value


def choose_slot(board, block):
    slots = valid_slots(board)
    if not slots:
        return 0
    turn = len(occupied_slots(board))
    target_depth = 2 if turn < 10 else 3 if turn < 20 else 4
    deadline = time.perf_counter() + TIME_LIMIT

    # Complete one full root scan before honoring the deadline, so output is always legal.
    root = rank_candidates(board, block, turn, None)
    best_sid = root[0][2]
    best_value = root[0][0]
    cache = {}

    for depth in range(2, target_depth + 1):
        try:
            check_deadline(deadline)
            current_sid = best_sid
            current_value = -1.0e100
            for _, _, sid in root[:BEAM_WIDTH]:
                check_deadline(deadline)
                gained = apply_score(board, sid, block)
                try:
                    value = gained + chance_value(board, turn + 1, depth - 1, deadline, cache)
                finally:
                    undo(board, sid)
                if value > current_value:
                    current_value = value
                    current_sid = sid
            best_sid = current_sid
            best_value = current_value
        except Timeout:
            break

    if best_sid not in slots:
        best_sid = slots[0]
    return best_sid


def parse_input():
    data = sys.stdin.read().strip().split()
    if len(data) < 86:
        return (7, 8, 9), [0] * 81
    n = int(data[0])
    block = tuple(int(value) for value in data[1:4])
    raw = [int(value) for value in data[4:85]]
    board = [0 if value == -1 else value for value in raw]
    if len(block) != 3 or any(value not in VALUES for value in block):
        block = (7, 8, 9)
    return block, board


def main():
    board = [0] * 81
    try:
        block, board = parse_input()
        sid = choose_slot(board, block)
        sys.stdout.write(str(int(sid)))
    except Exception:
        slots = valid_slots(board)
        sys.stdout.write(str(slots[0] if slots else 0))


if __name__ == "__main__":
    main()
