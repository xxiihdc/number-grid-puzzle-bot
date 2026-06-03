#!/usr/bin/env python3
"""Checks for scripted training command parsing."""

import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.cli import build_parser, config_from_args, run_cli


def test_train_flags_build_config():
    args = build_parser().parse_args([
        "train", "--non-interactive", "--population-size", "4",
        "--generations", "2", "--games-per-genome", "1", "--mutation-rate", "0.3",
        "--elite-ratio", "0.25", "--tournament-size", "2", "--inject-ratio", "0.25",
        "--variance-penalty", "0.1", "--workers", "1", "--seed", "123",
        "--training-dataset", "train.json", "--validation-dataset", "validation.json",
        "--watchdog-patience", "8", "--watchdog-min-delta", "0.5",
        "--watchdog-min-generations", "6", "--watchdog-average-recovery", "1.25",
    ])
    config = config_from_args(args)
    assert config.population_size == 4
    assert config.games_per_genome == 1
    assert config.worker_count == 1
    assert config.training_dataset_path == "train.json"
    assert config.watchdog_patience == 8
    assert config.watchdog_min_delta == 0.5
    assert config.watchdog_min_generations == 6
    assert config.watchdog_average_recovery == 1.25


def test_training_watchdog_can_be_disabled():
    args = build_parser().parse_args([
        "train", "--non-interactive", "--disable-watchdog",
        "--training-dataset", "train.json",
    ])
    assert config_from_args(args).watchdog_enabled is False


def test_default_mode_is_play():
    assert build_parser().parse_args([]).mode is None
    assert build_parser().parse_args(["play"]).mode == "play"


def test_non_interactive_requires_dataset():
    try:
        run_cli(["train", "--non-interactive"])
    except SystemExit as error:
        assert "--training-dataset" in str(error)
    else:
        raise AssertionError("Expected missing training dataset rejection")


def test_replay_accepts_validation_dataset():
    args = build_parser().parse_args(["replay", "summary.json", "--dataset", "validation"])
    assert args.dataset == "validation"


if __name__ == "__main__":
    test_train_flags_build_config()
    test_training_watchdog_can_be_disabled()
    test_default_mode_is_play()
    test_non_interactive_requires_dataset()
    test_replay_accepts_validation_dataset()
    print("PASS: training CLI checks")
