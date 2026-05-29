# Number Grid Puzzle Bot Constitution

## Core Principles

### I. Mathematical Rigor
All game analysis and algorithm design must be grounded in mathematical proofs and formal reasoning. Heuristics and strategies must be derived from combinatorial game theory, probability theory, and optimization principles rather than intuition alone.
**Why:** Ensures the bot's decision-making is sound and optimal rather than relying on anecdotal success.

### II. Algorithmic Efficiency
Prioritize time and space complexity in all implementations. Use cache-friendly data structures (e.g., 1D arrays for grid representation), local scoring algorithms with O(1) complexity, and prune search spaces using domain-specific constraints.
**Why:** The game requires evaluating thousands of states per second; inefficiencies directly reduce search depth and solution quality.

### III. Adaptive Phased Strategies
Strategies must evolve across game phases: opening (depth 2 search), midgame (depth 3-4), endgame (depth 4-5+). Fixed strategies are insufficient due to changing board density and combo opportunities.
**Why:** Early game favors board control; late game requires exhaustive search for remaining slots. Adaptation maximizes scoring potential throughout.

### IV. Automated Feature Discovery
Heuristic feature weights must be discovered through automated processes (e.g., genetic algorithms with feature masking) rather than manual selection. Human bias must be excluded from the feature selection process.
**Why:** Manual feature selection overlooks non-obvious but powerful patterns; automation finds globally optimal feature sets.

### V. Genetic Algorithm Optimization
Use genetic algorithms with adaptive mutation, common random numbers, and phase-based genomes to optimize heuristic weights. Premature convergence must be actively countered.
**Why:** Simple GAs plateau due to RNG noise; advanced techniques maintain diversity and find better optima.

### VI. Separation of Concerns
Strictly decouple inference (real-time move selection) from training (offline heuristic optimization). The inference engine must rely solely on precomputed heuristics without runtime learning.
**Why:** Real-time constraints prevent training during gameplay; separation ensures consistent performance and simplifies debugging.

### VII. Action Space Reduction
Exploit game constraints to reduce the action space from 81×9 possibilities to exactly 27 valid slots per move. Any algorithm must operate within this reduced space.
**Why:** The "perfect packing" constraint (27 turns × 3 cells = 81 cells) makes non-slot placements mathematically invalid and leads to unrecoverable states.

## Technology and Implementation Standards
- Primary language: Python 3.9+ with Numba/JIT for performance-critical path
- Use of bitboards or array representations for grid state
- Mandatory use of profiling tools to identify bottlenecks
- All search algorithms must implement transposition tables
- Numerical computations must use vectorized operations where possible
- Memory allocation must be minimized in hot paths

## Development Workflow and Quality
- Test-first approach: write expected move outcomes before implementing search
- Code reviews must verify mathematical correctness of heuristics
- Performance benchmarks required for any algorithm change
- Weekly self-play tournaments to evaluate strategy improvements
- All random seeds must be logged for experiment reproducibility
- Genetic algorithm experiments must use common random numbers across populations
- Reference legacy implementation in `ref/` directory for historical context

## Governance
This constitution is the supreme authority for project practices. Amendments require: (1) written proposal documenting changes, (2) approval via consensus among maintainers, (3) migration plan for existing code. All PRs must include a constitution compliance check. Use CLAUDE.md for runtime development guidance.

**Version**: 1.0.0 | **Ratified**: TODO(RATIFICATION_DATE): date unknown | **Last Amended**: 2026-05-28