# Number Grid Puzzle Bot - Development Guide

## Project Overview
This project implements an AI bot for the Number Grid Puzzle game, where the goal is to maximize score over 27 turns by placing 3x1 vertical blocks containing random numbers (7-10) on a 9x9 grid. Points are scored when 3+ identical numbers form a continuous line (horizontal, vertical, or diagonal).

## Game Rules & Constraints
- **Grid:** 9x9 matrix (81 cells), coordinates (0,0) to (8,8)
- **Turns:** Fixed at 27 turns (27 × 3 cells = 81 cells - perfect packing)
- **Blocks:** Each turn spawns one 3x1 vertical block with 3 random numbers from {7,8,9,10}
- **Scoring:** When 3+ identical numbers form a continuous line; scored blocks remain for reuse
- **Critical Constraint:** Perfect packing requirement means any placement creating isolated 1-2 cell gaps leads to mathematical impossibility of filling the grid

## Action Space Reduction
Due to the perfect packing constraint and fixed block orientation:
- **X Coordinate (Column):** Free choice from 0-8 (9 options)
- **Y Coordinate (Row):** Must be from {0, 3, 6} to maintain alignment (3 options)
- **Result:** Exactly 27 valid slots (9 × 3) per turn - no need to evaluate invalid positions

## Core Algorithms & Techniques

### 1. Inference Engine (Real-time Move Selection)
- **Search Algorithm:** Dynamic Depth Expectimax
  - Opening (Turns 1-10): Depth 2
  - Middlegame (Turns 11-20): Depth 3  
  - Endgame (Turns 21-27): Depth 4-5
- **Data Structure:** 1D array (length 81) for cache efficiency
- **Scoring:** Local ray-casting O(1) algorithm from newly placed blocks in 4 directions
- **Transposition Table:** Used to avoid recomputing identical states

### 2. Training Engine (Offline Heuristic Optimization)
- **Algorithm:** Enhanced Genetic Algorithm with:
  - Common Random Numbers (CRN): Fixed seed set for fair evaluation
  - Adaptive Mutation: Increases from 5% to 25% when fitness plateaus
  - Phase-based Genomes: Separate weights for opening/midgame/endgame
  - Feature Discovery: Binary masking to automatically select relevant heuristics

### 3. Heuristic Function
General form: H(state) = Σ(W_i × f_i(state))
Features include:
- Immediate score (f1_actual_score)
- Potential pairs (horizontal, diagonal)
- Column bumpiness (penalty for uneven heights)
- Center bias (early game)
- Isolated slots, dead ends, max height
- Number density clustering (per number type)
- Vertical match interfaces
- Empty slots count
- Diagonal cross points

## Development Guidelines

### Implementation Standards
- **Language:** Python 3.9+ with Numba/JIT for performance-critical sections
- **Grid Representation:** 1D array (row-major: index = y×9 + x)
- **Profiling:** Required for all algorithm changes; optimize hot paths
- **Memory:** Minimize allocations in search loops; reuse data structures
- **Vectorization:** Use NumPy where beneficial for clustering calculations

### Quality Requirements
- **Test-First:** Write expected move outcomes before search implementation
- **Mathematical Verification:** All heuristics must have clear rationale
- **Performance Benchmarks:** Measure states/second for search algorithm changes
- **Reproducibility:** Log all random seeds; use CRN in GA experiments
- **Code Reviews:** Focus on algorithm correctness and efficiency

### Experiment Tracking
- Weekly self-play tournaments to compare strategy versions
- A/B testing of heuristic weights using phase-specific genomes
- Documentation of all experiment parameters and results
- Version control of strong heuristic sets for rollback capability

## Constitution Principles
Refer to `.specify/memory/constitution.md` for the governing principles:
I. Mathematical Rigor
II. Algorithmic Efficiency  
III. Adaptive Phased Strategies
IV. Automated Feature Discovery
V. Genetic Algorithm Optimization
VI. Separation of Concerns (Inference vs Training)
VII. Action Space Reduction

## Getting Started
1. Review the game analysis in `thiet_ke_thuat_toan_bot_puzzle.md`
2. Study the constitution at `.specify/memory/constitution.md`
3. Examine existing code in `bot/` directory (if present)
4. Reference legacy implementation in `ref/` directory for historical context
5. Run baseline implementation to verify performance targets
6. Proceed with feature implementation following test-first approach

<!-- SPECKIT START -->
active_plan: specs/005-training-plateau-features/plan.md
<!-- SPECKIT END -->

## Performance Targets
- Search speed: >10,000 states/second on modern CPU
- Memory usage: <50 MB for search tables
- Move selection time: <100ms per turn (allowing for deeper search)
- GA convergence: Significant improvement over baseline within 50 generations
