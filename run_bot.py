#!/usr/bin/env python3
"""
Simple script to run the Number Grid Puzzle Bot.
"""

import os
import sys

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

from bot.cli import run_cli

if __name__ == "__main__":
    raise SystemExit(run_cli())
