#!/usr/bin/env python3
"""Checks for incremental JSON training-run records."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.training_config import TrainingConfig
from bot.training_data import generate_dataset, save_dataset
from bot.training_runner import run_training
from bot.training_runner import TrainingInterrupted
from bot.training_runner import evaluate_training_watchdog
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
        assert os.path.exists(os.path.join(temp_dir, "active_chromosome.json"))
        diagnostics = summary["generation_summaries"][0]["plateau_diagnostics"]
        assert diagnostics["unique_chromosome_count"] >= 1
        assert 0 < diagnostics["chromosome_diversity_ratio"] <= 1
        assert diagnostics["active_gene_count_min"] <= diagnostics["active_gene_count_average"]
        assert diagnostics["active_gene_count_average"] <= diagnostics["active_gene_count_max"]
        assert diagnostics["no_improvement_generations"] == 0
        assert diagnostics["adaptive_mutation_surge"] is False


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


def test_watchdog_plateau_stops_completed_run():
    original_evaluate = genetics.GeneticOptimizer._evaluate_population
    original_evolve = genetics.GeneticOptimizer.evolve_from_evaluated
    with tempfile.TemporaryDirectory() as temp_dir:
        dataset_path = os.path.join(temp_dir, "dataset.json")
        save_dataset(generate_dataset("train", "training", 123, 1), dataset_path)

        def plateau(self):
            if self.best_chromosome is None:
                self.best_chromosome = self.population[0].copy()
                self.best_fitness = 10.0
            else:
                self.generation_no_improvement += 1
            self.population[0].fitness = 10.0
            return [(self.population[0], 10.0), (self.population[1], 9.0)]

        genetics.GeneticOptimizer._evaluate_population = plateau
        genetics.GeneticOptimizer.evolve_from_evaluated = lambda self, evaluated: None
        try:
            summary_path = run_training(
                TrainingConfig(
                    population_size=2, generations=8, games_per_genome=1,
                    elite_ratio=0.5, inject_ratio=0.0, tournament_size=1,
                    worker_count=1, training_dataset_path=dataset_path,
                    watchdog_patience=4, watchdog_min_generations=5,
                    watchdog_average_recovery=0.1,
                ),
                temp_dir,
            )
        finally:
            genetics.GeneticOptimizer._evaluate_population = original_evaluate
            genetics.GeneticOptimizer.evolve_from_evaluated = original_evolve

        with open(summary_path, encoding="utf-8") as source:
            summary = json.load(source)
        assert summary["status"] == "completed"
        assert summary["stop_reason"] == "watchdog_plateau"
        assert len(summary["generation_summaries"]) < 8
        assert summary["best_chromosome"]
        assert summary["best_fitness"] == 10.0


def test_watchdog_min_delta_resets_no_improvement_streak():
    summaries = []
    best_values = [10.0, 10.0, 10.0, 10.0, 10.5, 10.5, 10.5]
    for index, best in enumerate(best_values, start=1):
        summaries.append({
            "generation_number": index,
            "best_fitness": best,
            "average_fitness": 9.0,
            "plateau_diagnostics": {
                "adaptive_mutation_surge": index == 4,
                "no_improvement_generations": index - 1,
            },
        })
    decision = evaluate_training_watchdog(
        TrainingConfig(
            training_dataset_path="training.json",
            watchdog_patience=4,
            watchdog_min_delta=0.5,
            watchdog_min_generations=5,
            watchdog_average_recovery=0.1,
        ),
        summaries,
    )
    assert decision.should_stop is False
    assert decision.reason == "patience"


if __name__ == "__main__":
    test_short_run_writes_completed_summary()
    test_failed_run_preserves_summary()
    test_interrupted_run_preserves_summary()
    test_watchdog_plateau_stops_completed_run()
    test_watchdog_min_delta_resets_no_improvement_streak()
    print("PASS: training record checks")
