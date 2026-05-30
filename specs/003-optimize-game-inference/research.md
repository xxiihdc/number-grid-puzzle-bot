# Research Findings: Optimize Game Inference Performance

## Decision: Spawn the Current Block Before Search

**Chosen**: Match the reference game flow: spawn a block, choose its slot, then place the
same block.

**Rationale**: The current implementation chooses a slot before knowing the block and
expands 64 possible blocks at the root. `ref/main.py` makes the current block observable
before slot selection. Restoring that contract removes unnecessary root uncertainty and
lets the AI select a placement appropriate for the actual block.

**Alternatives considered**:
- Preserve hidden current blocks: inconsistent with the reference flow and much slower.
- Select a slot greedily after spawning: fast, but discards the required Expectimax
  lookahead.

## Decision: Budgeted Expectimax with Completed Iterations

**Chosen**: Compute a complete depth-1 fallback, then deepen toward phase targets while
time remains. Publish only the last completed iteration.

**Rationale**: Baseline profiling on the target machine showed the previous depth-1
search at approximately 265 milliseconds and depth-2 search exceeding the deadline.
A complete known-block root scan takes approximately 4 milliseconds, providing a valid
fallback before deeper analysis begins.

**Alternatives considered**:
- Exact full-expansion Expectimax: cannot guarantee a 200-millisecond move deadline.
- Greedy-only evaluation: meets timing but abandons phased lookahead.
- Publish partial iterations: introduces candidate-order bias when a timeout occurs.

## Decision: Deterministic Sampled Chance Nodes

**Chosen**: Evaluate two deterministic future blocks per chance node and use a beam
width of three for deeper candidate expansion.

**Rationale**: Every random block has 64 possible value combinations. Sampling bounds
the work performed per node, while deterministic seeds make repeated evaluation and
benchmark comparisons reproducible without consuming the game RNG stream.

**Alternatives considered**:
- Expand all 64 blocks: too expensive for the target deadline.
- Use global random sampling: causes non-repeatable search behavior and interferes with
  reproducible benchmarks.
- Use one sample: faster but unnecessarily fragile given the available budget.

## Decision: Apply/Undo Simulation and Bounded Cache

**Chosen**: Simulate search moves on one working state with guaranteed undo and clear a
10,000-entry transposition table at the start of each move.

**Rationale**: Copying board arrays and occupied-slot sets at every node allocates
unnecessary objects in the hot path. Apply/undo keeps mutations local to search.
A per-move bounded cache avoids unbounded growth while retaining repeated-state reuse.

**Alternatives considered**:
- Copy each child state: simpler but slower and allocation-heavy.
- Retain an unbounded cache across games: increases memory use and mixes unrelated
  runtime searches.

## Decision: Keep Scoring Semantics Out of Scope

**Chosen**: Preserve existing local placement scoring for runtime simulation.

**Rationale**: The local placement score and final board score currently use different
scales. Aligning them changes strategic behavior and requires a separate correctness
specification. This feature is limited to runtime responsiveness and valid gameplay.

**Alternatives considered**:
- Align scoring in the same change: broader behavioral risk and harder performance
  attribution.
