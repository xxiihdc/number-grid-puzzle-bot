# Number Grid Puzzle Bot

An AI bot designed to play the Number Grid Puzzle game optimally using Expectimax search with dynamic depth and genetic algorithm-optimized heuristics.

## Project Structure

```
matrix/
├── bot/
│   ├── __init__.py
│   ├── main.py          # Main entry point
│   ├── game_state.py    # Game state representation and logic
│   ├── expectimax.py    # Expectimax search implementation
│   ├── genetics.py      # Genetic algorithm for heuristic optimization
│   └── features.py      # Feature extraction (15 features from design doc)
├── utils/               # Utility functions
├── tests/               # Test files
├── config/              # Configuration files
├── test_bot.py          # Basic functionality tests
└── thiet_ke_thuat_toan_bot_puzzle.md  # Original design document
```

## Features Implemented

1. **Game State Representation**: 9x9 grid with 3x1 vertical blocks using 1D array for cache efficiency
2. **Expectimax Search**: With dynamic depth based on game phase (depth 2 for turns 1-10, depth 3 for turns 11-20, depth 4 for turns 21-27)
3. **Local Ray-casting Scoring**: O(1) scoring algorithm that only checks lines through newly placed blocks
4. **Feature Pool**: All 15 features from the design document implemented:
   - Actual score
   - Potential horizontal/diagonal pairs
   - Column bumpiness
   - Center bias
   - Isolated slots and dead ends
   - Max height
   - Number density for each value (7,8,9,10)
   - Vertical match interfaces
   - Empty slots count
   - Diagonal cross points
5. **Genetic Algorithm Optimizer**: With advanced techniques:
   - Common Random Numbers (CRN) for reduced noise
   - Adaptive Mutation Surge
   - Phase-based Genomes (different weights for early/mid/late game)
   - Feature Pool with Binary Masking for automatic feature selection

## Usage

### To run the bot (play a game):
```bash
python bot/main.py
```
Alternatively, you can use the convenience script:
```bash
python run_bot.py
```

### To train the heuristic weights:
```bash
python bot/main.py train
```
Or using the convenience script:
```bash
python run_bot.py train
```

### To run tests:
```bash
python test_bot.py
```

## Design Document Reference

See `thiet_ke_thuat_toan_bot_puzzle.md` for the complete algorithm design and mathematical analysis.

## Requirements

- Python 3.x
- NumPy (for array operations)

Install dependencies with:
```bash
pip install numpy
```