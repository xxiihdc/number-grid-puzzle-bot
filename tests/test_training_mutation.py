#!/usr/bin/env python3
"""Checks for adaptive mutation pulses after a plateau."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.features import FeaturePool
from bot.genetics import GeneticOptimizer


def test_adaptive_surge_uses_one_generation_pulses():
    optimizer = GeneticOptimizer(FeaturePool(), search_engine=None, population_size=2)
    expected = {
        0: False,
        1: False,
        2: False,
        3: True,
        4: False,
        5: False,
        6: False,
        7: True,
    }
    for streak, should_surge in expected.items():
        optimizer.generation_no_improvement = streak
        assert optimizer.should_use_adaptive_surge() is should_surge
        assert optimizer.get_plateau_diagnostics()["adaptive_mutation_surge"] is should_surge


if __name__ == "__main__":
    test_adaptive_surge_uses_one_generation_pulses()
    print("PASS: adaptive mutation pulse checks")
