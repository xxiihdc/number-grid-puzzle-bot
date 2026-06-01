#!/usr/bin/env python3
"""Checks for deterministic reevaluation from a run summary."""

import os
import sys
import tempfile
import json

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.training_config import TrainingConfig
from bot.training_data import generate_dataset, save_dataset
from bot.training_runner import replay_run, run_training


def test_replay_matches_recorded_best_fitness():
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_path = os.path.join(temp_dir, "train.json")
        save_dataset(generate_dataset("train", "training", 123, 1), dataset_path)
        config = TrainingConfig(
            population_size=2, generations=1, games_per_genome=1,
            elite_ratio=0.5, inject_ratio=0.0, tournament_size=1,
            worker_count=1, training_dataset_path=dataset_path,
        )
        summary_path = run_training(config, temp_dir)
        evaluation = replay_run(str(summary_path))
        with open(summary_path, encoding="utf-8") as source:
            summary = json.load(source)
        assert evaluation.fitness == summary["best_fitness"]


def test_replay_can_evaluate_validation_dataset():
    with tempfile.TemporaryDirectory() as temp_dir:
        training_path = os.path.join(temp_dir, "train.json")
        validation_path = os.path.join(temp_dir, "validation.json")
        save_dataset(generate_dataset("train", "training", 123, 1), training_path)
        save_dataset(generate_dataset("validation", "validation", 456, 2), validation_path)
        config = TrainingConfig(
            population_size=2, generations=1, games_per_genome=1,
            elite_ratio=0.5, inject_ratio=0.0, tournament_size=1,
            worker_count=1, training_dataset_path=training_path,
            validation_dataset_path=validation_path,
        )
        summary_path = run_training(config, temp_dir)
        evaluation = replay_run(str(summary_path), dataset_purpose="validation")
        assert len(evaluation.scenario_scores) == 2


if __name__ == "__main__":
    test_replay_matches_recorded_best_fitness()
    test_replay_can_evaluate_validation_dataset()
    print("PASS: training replay checks")
