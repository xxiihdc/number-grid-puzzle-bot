#!/usr/bin/env python3
"""Focused checks for offline training configuration."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.training_config import TrainingConfig, TrainingConfigError


def _valid(**overrides):
    values = {"training_dataset_path": "training.json"}
    values.update(overrides)
    return TrainingConfig(**values)


def _assert_invalid(field, **overrides):
    try:
        _valid(**overrides).validate(training_scenario_count=40)
    except TrainingConfigError as error:
        assert field in str(error), str(error)
    else:
        raise AssertionError(f"Expected invalid field: {field}")


def test_defaults_and_derived_counts():
    config = _valid()
    config.validate(training_scenario_count=40)
    assert config.population_size == 50
    assert config.generations == 100
    assert config.games_per_genome == 40
    assert config.elite_count == 5
    assert config.inject_count == 5
    assert config.watchdog_enabled is True
    assert config.watchdog_patience == 12
    assert config.watchdog_min_generations == 10


def test_numeric_validation():
    _assert_invalid("population_size", population_size=0)
    _assert_invalid("mutation_rate", mutation_rate=1.1)
    _assert_invalid("variance_penalty", variance_penalty=-0.1)
    _assert_invalid("tournament_size", population_size=4, tournament_size=5)
    _assert_invalid("games_per_genome", games_per_genome=41)
    _assert_invalid("watchdog_patience", watchdog_patience=0)
    _assert_invalid("watchdog_min_delta", watchdog_min_delta=-0.1)
    _assert_invalid("watchdog_min_generations", watchdog_min_generations=0)
    _assert_invalid("watchdog_average_recovery", watchdog_average_recovery=-0.1)


if __name__ == "__main__":
    test_defaults_and_derived_counts()
    test_numeric_validation()
    print("PASS: training configuration checks")
