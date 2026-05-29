#!/usr/bin/env python3
"""
Simple script to run the Number Grid Puzzle Bot.
"""

import sys
import os

# Add the bot directory to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'bot'))

from bot.main import main

if __name__ == "__main__":
    # Run the bot with command line arguments
    main()