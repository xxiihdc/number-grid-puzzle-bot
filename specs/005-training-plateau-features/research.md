# Research: Improve Training Plateau Signals

## Plateau Evidence

**Decision**: Treat the inspected run as a confirmed plateau requiring better signals and
diagnostics.

**Rationale**: `train-20260530T083521.294234Z.json` records 80 generations. Global best
fitness reached `472.644385` at generation 13 and never improved afterward. Validation
fitness is `409.070609`, below training best. Existing summaries do not record diversity.

## Feature Design

**Decision**: Add one-match open windows, two-match open windows, blocked windows, and
multi-line completion cells using exact contiguous length-three segments in all four
scoring directions.

**Rationale**: Existing horizontal and diagonal pair features are direction-specific and
do not cover a uniform scoring-window model. Several current signals are constant or
nearly constant across aligned perfect-packing choices at a fixed turn. Exact windows add
placement-sensitive information directly related to scoring opportunities.

**Alternatives considered**:
- Add more per-number densities: already represented and weakly tied to imminent lines.
- Replace existing features: higher migration risk and unnecessary for automated masking.
- Add search depth during training: substantially increases evaluation cost and does not
  solve missing heuristic signal quality.

## Chromosome Migration

**Decision**: Append disabled zero-weight genes when loading a chromosome with fewer
features than the active pool; reject oversized chromosomes.

**Rationale**: Appending neutral genes preserves legacy behavior while allowing warm-start
evolution to activate new features.

## Diagnostics

**Decision**: Persist unique chromosome count, diversity ratio, active-gene count range and
average, no-improvement streak, and adaptive-surge state per generation.

**Rationale**: These fields separate representation limits from premature convergence
without changing fitness behavior.
