#!/usr/bin/env python3
"""Focused tests for the weight-adjustment recommendation skill script."""

from importlib.util import module_from_spec, spec_from_file_location
import json
import os
from pathlib import Path
import sys
import tempfile


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / ".codex/skills/matrix-recommend-weight-adjustments/scripts/recommend_weight_adjustments.py"


def _load_module():
    spec = spec_from_file_location("recommend_weight_adjustments", SCRIPT)
    module = module_from_spec(spec)
    assert spec.loader is not None
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _chromosome(weight, mask=1):
    return {
        "genes": [
            [{"mask": mask, "weight": weight}],
            [{"mask": 1, "weight": 0.0}],
            [{"mask": 1, "weight": 0.0}],
        ]
    }


def _population_telemetry(top_weight, bottom_weight):
    return {
        "schema_version": 1,
        "candidate_count": 2,
        "ranked_candidates": [
            {
                "rank": 1,
                "fitness": 20.0,
                "chromosome": _chromosome(top_weight),
            },
            {
                "rank": 2,
                "fitness": 10.0,
                "chromosome": _chromosome(bottom_weight),
            },
        ],
        "gene_statistics": [
            {
                "phase_index": 0,
                "feature_index": 0,
                "weight_min": min(top_weight, bottom_weight),
                "weight_mean": (top_weight + bottom_weight) / 2,
                "weight_max": max(top_weight, bottom_weight),
                "weight_stddev": abs(top_weight - bottom_weight) / 2,
                "mask_activation_ratio": 1.0,
            }
        ],
    }


def _write_run(path, run_id, weights, fitnesses, validation_fitness):
    payload = {
        "run_id": run_id,
        "status": "completed",
        "stop_reason": "max_generations",
        "updated_at": "2026-06-10T00:00:00+00:00",
        "training_dataset": {
            "dataset_id": "train",
            "content_checksum": "sha256:train",
        },
        "validation_dataset": {
            "dataset_id": "validation",
            "content_checksum": "sha256:validation",
        },
        "best_fitness": fitnesses[-1],
        "validation_fitness": validation_fitness,
        "best_chromosome": _chromosome(weights[-1]),
        "generation_summaries": [
            {
                "generation_number": index + 1,
                "best_fitness": fitness,
                "best_chromosome": _chromosome(weight),
                "population_telemetry": _population_telemetry(weight + 1.0, weight - 1.0),
            }
            for index, (weight, fitness) in enumerate(zip(weights, fitnesses))
        ],
    }
    path.write_text(json.dumps(payload), encoding="utf-8")


def test_recommends_increase_from_improving_weight_delta():
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir)
        _write_run(runs_dir / "train-a.json", "a", [1.0, 5.0, 8.0], [10.0, 15.0, 20.0], 21.0)
        _write_run(runs_dir / "train-b.json", "b", [1.0, 2.0, 3.0], [10.0, 11.0, 12.0], 12.0)
        runs = module._load_runs(sorted(runs_dir.glob("train-*.json")))
        report = module.build_report(runs, runs_dir)

        assert report["report_type"] == "matrix_weight_adjustment_recommendation"
        assert report["analysis_mode"] == "read_only"
        assert report["evidence_scope"] == "population_telemetry_and_generation_best_chromosomes"
        recommendation = report["phase_recommendations"][0]
        assert recommendation["phase"] == "opening"
        assert recommendation["feature_index"] == 0
        assert recommendation["decision"] == "increase"
        assert recommendation["suggested_delta"] > 0
        assert os.path.exists(report["analysis_path"])


def test_missing_validation_is_reported_as_warning():
    module = _load_module()
    with tempfile.TemporaryDirectory() as temp_dir:
        runs_dir = Path(temp_dir)
        payload = {
            "run_id": "missing-validation",
            "status": "completed",
            "best_fitness": 10.0,
            "best_chromosome": _chromosome(2.0),
            "generation_summaries": [
                {"generation_number": 1, "best_fitness": 9.0, "best_chromosome": _chromosome(1.0)},
                {"generation_number": 2, "best_fitness": 10.0, "best_chromosome": _chromosome(2.0)},
            ],
        }
        (runs_dir / "train-missing.json").write_text(json.dumps(payload), encoding="utf-8")
        runs = module._load_runs(sorted(runs_dir.glob("train-*.json")))
        report = module.build_report(runs, runs_dir)

        warnings = report["datasets"]["warnings"]
        assert any("validation_fitness" in warning for warning in warnings)


if __name__ == "__main__":
    test_recommends_increase_from_improving_weight_delta()
    test_missing_validation_is_reported_as_warning()
    print("PASS: weight adjustment recommendation skill checks")
