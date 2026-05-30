#!/usr/bin/env python3
"""Focused checks for training-log chart generation."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "scripts"))

from plot_training_log import load_generation_series, plot_training_series


def test_training_chart_can_be_saved_headlessly():
    payload = {
        "run_id": "train-test",
        "status": "running",
        "generation_summaries": [
            {
                "generation_number": 1,
                "best_fitness": 300.0,
                "average_fitness": 200.0,
                "minimum_fitness": 100.0,
            },
            {
                "generation_number": 2,
                "best_fitness": 350.0,
                "average_fitness": 240.0,
                "minimum_fitness": 120.0,
            },
        ],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        summary_path = os.path.join(temp_dir, "summary.json")
        output_path = os.path.join(temp_dir, "chart.png")
        with open(summary_path, "w", encoding="utf-8") as output:
            json.dump(payload, output)

        series = load_generation_series(summary_path)
        plot_training_series(series, output=output_path, show_ui=False)

        assert series["best"] == [300.0, 350.0]
        assert series["average"] == [200.0, 240.0]
        assert os.path.getsize(output_path) > 0


def test_optional_plateau_diagnostics_are_loaded():
    payload = {
        "generation_summaries": [{
            "generation_number": 1,
            "best_fitness": 300.0,
            "average_fitness": 200.0,
            "minimum_fitness": 100.0,
            "plateau_diagnostics": {
                "chromosome_diversity_ratio": 0.75,
                "no_improvement_generations": 2,
                "adaptive_mutation_surge": False,
            },
        }],
    }
    with tempfile.TemporaryDirectory() as temp_dir:
        summary_path = os.path.join(temp_dir, "summary.json")
        with open(summary_path, "w", encoding="utf-8") as output:
            json.dump(payload, output)
        series = load_generation_series(summary_path)
    assert series["diversity_ratio"] == [0.75]
    assert series["no_improvement_generations"] == [2]
    assert series["adaptive_mutation_surge"] == [False]


if __name__ == "__main__":
    test_training_chart_can_be_saved_headlessly()
    test_optional_plateau_diagnostics_are_loaded()
    print("PASS: training plot checks")
