#!/usr/bin/env python3
"""Regression checks for the latest-training-run agent handoff contract."""

from __future__ import annotations

import importlib.util
import json
from pathlib import Path
import tempfile


SCRIPT = (
    Path(__file__).parent
    / ".codex/skills/matrix-analyze-latest-training-run/scripts/analyze_latest_training_run.py"
)


def load_analyzer():
    spec = importlib.util.spec_from_file_location("analyze_latest_training_run", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
    return module


def test_agent_handoff_contract(analyzer) -> None:
    payload = {
        "run_id": "train-test",
        "status": "completed",
        "stop_reason": "max_generations",
        "updated_at": "2026-06-01T00:00:00+00:00",
        "config": {
            "generations": 2,
            "population_size": 4,
            "games_per_genome": 3,
            "worker_count": 1,
            "mutation_rate": 0.05,
            "validation_dataset_path": "training_data/validation.json",
        },
        "training_dataset": {"dataset_id": "train"},
        "validation_dataset": {"dataset_id": "validation"},
        "overlap_report": {"scenario_count": 0, "scenario_ids": []},
        "best_fitness": 12.0,
        "generation_summaries": [
            {
                "generation_number": 1,
                "best_fitness": 10.0,
                "elapsed_seconds": 1.5,
                "plateau_diagnostics": {
                    "chromosome_diversity_ratio": 1.0,
                    "no_improvement_generations": 0,
                    "adaptive_mutation_surge": False,
                    "active_gene_count_min": 2,
                    "active_gene_count_average": 3.0,
                    "active_gene_count_max": 4,
                },
            },
            {
                "generation_number": 2,
                "best_fitness": 12.0,
                "elapsed_seconds": 2.0,
                "plateau_diagnostics": {
                    "chromosome_diversity_ratio": 0.75,
                    "no_improvement_generations": 0,
                    "adaptive_mutation_surge": True,
                    "active_gene_count_min": 2,
                    "active_gene_count_average": 2.5,
                    "active_gene_count_max": 3,
                },
            },
        ],
    }
    report = analyzer.analyze(Path("training_runs/train-test.json"), payload, Path("missing"), 10)
    json.dumps(report)
    assert report["schema_version"] == 1
    assert report["report_type"] == "matrix_training_run_analysis"
    assert report["analysis_mode"] == "read_only"
    assert report["total_best_fitness_delta"] == 2.0
    assert report["improvement_generations"] == [1, 2]
    assert report["plateau_diagnostics"]["mutation_pulse_generations"] == [2]
    assert report["assessment"]["validation_status"] == "dataset_available_replay_required"
    assert report["recommended_next_action"]["action"] == "replay_validation"
    assert report["recommended_next_action"]["command"].endswith("--dataset validation")
    assert "## Assessment" in analyzer.render_markdown(report)


def test_latest_summary_selection(analyzer) -> None:
    with tempfile.TemporaryDirectory() as directory:
        root = Path(directory)
        (root / "train-older.json").write_text(
            json.dumps({"updated_at": "2026-05-01T00:00:00+00:00"}),
            encoding="utf-8",
        )
        newest = root / "train-newest.json"
        newest.write_text(
            json.dumps({"updated_at": "2026-06-01T00:00:00+00:00"}),
            encoding="utf-8",
        )
        path, _ = analyzer.find_latest_summary(root)
        assert path == newest


def main() -> None:
    analyzer = load_analyzer()
    test_agent_handoff_contract(analyzer)
    test_latest_summary_selection(analyzer)
    print("PASS: latest-training-run skill agent handoff checks")


if __name__ == "__main__":
    main()
