#!/usr/bin/env python3
"""
Command-line interface for the Number Grid Puzzle Bot.
"""

import argparse
import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from main import main


def run_cli():
    """Run the command-line interface."""
    parser = argparse.ArgumentParser(description="Number Grid Puzzle Bot")
    parser.add_argument(
        "mode",
        nargs="?",
        default="play",
        choices=["play", "train"],
        help="Mode to run: 'play' to solve a puzzle, 'train' to optimize heuristics"
    )
    parser.add_argument(
        "--generations",
        type=int,
        default=50,
        help="Number of generations for training (default: 50)"
    )
    parser.add_argument(
        "--population",
        type=int,
        default=30,
        help="Population size for genetic algorithm (default: 30)"
    )

    args = parser.parse_args()

    if args.mode == "play":
        print("Starting puzzle solving mode...")
        # Call main with no arguments (defaults to play)
        main()
    elif args.mode == "train":
        print(f"Starting training mode with {args.population} population for {args.generations} generations...")
        # We'll need to modify main to accept these parameters, or create a training function
        # For now, we'll just call main with a special argument
        sys.argv = [sys.argv[0], "train"]
        main()


if __name__ == "__main__":
    run_cli()