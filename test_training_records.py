#!/usr/bin/env python3
"""Checks for incremental JSON training-run records."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.training_config import TrainingConfig
from bot.training_data import generate_dataset, save_dataset
from bot.training_runner import run_training
from bot.training_runner import TrainingInterrupted
import genetics


def test_short_run_writes_completed_summary():
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_path = os.path.join(temp_dir, "train.json")
        save_dataset(generate_dataset("train", "training", 123, 1), dataset_path)
        config = TrainingConfig(
            population_size=2, generations=1, games_per_genome=1,
            elite_ratio=0.5, inject_ratio=0.0, tournament_size=1,
            worker_count=1, training_dataset_path=dataset_path,
        )
        summary_path = run_training(config, temp_dir)
        with open(summary_path, encoding="utf-8") as source:
            summary = json.load(source)
        assert summary["status"] == "completed"
        assert len(summary["generation_summaries"]) == 1
        assert summary["best_chromosome"]
        assert summary["best_fitness"] is not None


def _config_for(dataset_path):
    return TrainingConfig(
        population_size=2, generations=1, games_per_genome=1,
        elite_ratio=0.5, inject_ratio=0.0, tournament_size=1,
        worker_count=1, training_dataset_path=dataset_path,
    )


def _only_summary(temp_dir):
    names = [name for name in os.listdir(temp_dir) if name.startswith("train-") and name.endswith(".json")]
    assert len(names) == 1
    with open(os.path.join(temp_dir, names[0]), encoding="utf-8") as source:
        return json.load(source)


def test_failed_run_preserves_summary():
    original = genetics.GeneticOptimizer._evaluate_population
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_path = os.path.join(temp_dir, "dataset.json")
        save_dataset(generate_dataset("train", "training", 123, 1), dataset_path)
        genetics.GeneticOptimizer._evaluate_population = lambda self: (_ for _ in ()).throw(RuntimeError("boom"))
        try:
            try:
                run_training(_config_for(dataset_path), temp_dir)
            except RuntimeError:
                pass
            else:
                raise AssertionError("Expected failed training")
        finally:
            genetics.GeneticOptimizer._evaluate_population = original
        assert _only_summary(temp_dir)["status"] == "failed"


def test_interrupted_run_preserves_summary():
    original = genetics.GeneticOptimizer._evaluate_population
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_path = os.path.join(temp_dir, "dataset.json")
        save_dataset(generate_dataset("train", "training", 123, 1), dataset_path)
        genetics.GeneticOptimizer._evaluate_population = lambda self: (_ for _ in ()).throw(KeyboardInterrupt())
        try:
            try:
                run_training(_config_for(dataset_path), temp_dir)
            except TrainingInterrupted:
                pass
            else:
                raise AssertionError("Expected interrupted training")
        finally:
            genetics.GeneticOptimizer._evaluate_population = original
        assert _only_summary(temp_dir)["status"] == "interrupted"


if __name__ == "__main__":
    test_short_run_writes_completed_summary()
    test_failed_run_preserves_summary()
    test_interrupted_run_preserves_summary()
    print("PASS: training record checks")
