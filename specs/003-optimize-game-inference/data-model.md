# Data Model: Optimize Game Inference Performance

## Entities

### GameTurn

Represents one of the 27 placement opportunities.

**Fields**:
- `turn_number`: integer from 1 through 27
- `spawned_block`: three values, each in `{7, 8, 9, 10}`
- `available_slots`: unused aligned `(x, y)` slots
- `selected_slot`: one member of `available_slots`
- `search_stats`: metrics for the move-selection attempt

**Validation rules**:
- `selected_slot` must be aligned and unused before placement.
- The exact `spawned_block` evaluated by search must be placed into `selected_slot`.

### RuntimeBudget

Defines the time available to select one move.

**Fields**:
- `external_limit_seconds`: `0.200`
- `internal_search_limit_seconds`: `0.180`

**Validation rules**:
- Search uses the internal limit so return-path overhead remains within the external
  requirement.

### SearchStats

Describes the latest search call.

**Fields**:
- `elapsed_seconds`
- `target_depth`
- `completed_depth`
- `timed_out`
- `fallback_used`
- `nodes_evaluated`
- `cache_entries`

**Validation rules**:
- `completed_depth` is at least 1 when a valid move exists.
- `fallback_used` is true when search returns before completing `target_depth`.
- `cache_entries` never exceeds the configured cache limit.

### PerformanceValidationRun

Aggregates deterministic timing measurements.

**Fields**:
- `game_seeds`: ten fixed integer seeds
- `move_durations`: 270 search-only elapsed durations
- `slowest_move_seconds`
- `all_moves_valid`
- `passed`

**Validation rules**:
- `passed` is true only when all games complete, every move is valid, and every measured
  move duration is at most 200 milliseconds.

## State Transitions

1. Game mode spawns one block.
2. Search evaluates the current block and records a complete depth-1 fallback.
3. Search deepens while the internal runtime budget remains.
4. Search publishes the last completed iteration and its metrics.
5. Game mode places the exact spawned block at the selected slot.
6. Benchmark mode records search-only elapsed time separately from optional display.
