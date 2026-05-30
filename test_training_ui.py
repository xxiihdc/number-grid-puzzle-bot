#!/usr/bin/env python3
"""Checks for the local terminal training configuration flow."""

import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.training_config import TrainingConfig
from bot.training_data import generate_dataset, save_dataset
from bot.training_ui import collect_training_config


def test_prompt_defaults_and_confirmation():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "train.json")
        save_dataset(generate_dataset("train", "training", 123, 40), path)
        answers = iter([""] * 12 + ["y"])
        config = collect_training_config(
            TrainingConfig(training_dataset_path=path),
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
        )
        assert config.population_size == 50
        assert config.training_dataset_path == path


def test_cancel_returns_none():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "train.json")
        save_dataset(generate_dataset("train", "training", 123, 40), path)
        answers = iter([""] * 12 + ["n"])
        assert collect_training_config(
            TrainingConfig(training_dataset_path=path),
            input_fn=lambda _: next(answers),
            output_fn=lambda _: None,
        ) is None


def test_invalid_value_is_reported_and_corrected():
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "train.json")
        save_dataset(generate_dataset("train", "training", 123, 40), path)
        first_round = ["0"] + [""] * 11
        second_round = ["50"] + [""] * 11 + ["y"]
        answers = iter(first_round + second_round)
        messages = []
        config = collect_training_config(
            TrainingConfig(training_dataset_path=path),
            input_fn=lambda _: next(answers),
            output_fn=messages.append,
        )
        assert config.population_size == 50
        assert any("population_size" in message for message in messages)


if __name__ == "__main__":
    test_prompt_defaults_and_confirmation()
    test_cancel_returns_none()
    test_invalid_value_is_reported_and_corrected()
    print("PASS: training UI checks")
