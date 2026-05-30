#!/usr/bin/env python3
"""Checks for latest-weight promotion and warm-start training."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.features import FeaturePool
from bot.game_state import GameState
from bot.genetics import Chromosome, GeneticOptimizer
from bot.training_weights import load_active_chromosome, sync_latest_weights


def _summary(path, run_id, updated_at, fitness, chromosome):
    path.write_text(json.dumps({
        "run_id": run_id,
        "updated_at": updated_at,
        "best_fitness": fitness,
        "validation_fitness": None,
        "best_chromosome": chromosome.to_payload(),
    }), encoding="utf-8")


def test_newest_summary_is_promoted_and_loaded():
    with tempfile.TemporaryDirectory() as temp_dir:
        from pathlib import Path
        root = Path(temp_dir)
        older = Chromosome(len(FeaturePool().get_feature_names()))
        newer = Chromosome(len(FeaturePool().get_feature_names()))
        newer.genes[0][0].weight = 42.0
        _summary(root / "train-old.json", "old", "2026-05-30T00:00:00Z", 1.0, older)
        _summary(root / "train-new.json", "new", "2026-05-30T01:00:00Z", 2.0, newer)
        active = root / "active_chromosome.json"
        assert sync_latest_weights(temp_dir, str(active)) == active
        loaded = load_active_chromosome(str(active))
        assert loaded.genes[0][0].weight == 42.0


def test_optimizer_keeps_active_baseline_in_population():
    chromosome = Chromosome(len(FeaturePool().get_feature_names()))
    chromosome.genes[0][0].weight = 42.0
    optimizer = GeneticOptimizer(
        FeaturePool(), search_engine=None, population_size=3,
        initial_chromosome=chromosome,
    )
    assert optimizer.population[0].to_payload() == chromosome.to_payload()
    assert len(optimizer.population) == 3


def test_legacy_chromosome_expands_with_neutral_genes():
    chromosome = Chromosome(15)
    chromosome.genes[0][0].weight = 42.0
    chromosome.normalize_feature_count(len(FeaturePool().get_feature_names()))
    assert chromosome.num_features == 19
    assert chromosome.genes[0][0].weight == 42.0
    assert all(gene.mask == 0 and gene.weight == 0.0 for gene in chromosome.genes[0][15:])
    assert isinstance(chromosome.get_fitness(GameState(), FeaturePool()), float)


def test_oversized_chromosome_is_rejected():
    chromosome = Chromosome(len(FeaturePool().get_feature_names()) + 1)
    try:
        chromosome.normalize_feature_count(len(FeaturePool().get_feature_names()))
    except ValueError as error:
        assert "more features" in str(error)
    else:
        raise AssertionError("Expected oversized chromosome rejection")


if __name__ == "__main__":
    test_newest_summary_is_promoted_and_loaded()
    test_optimizer_keeps_active_baseline_in_population()
    test_legacy_chromosome_expands_with_neutral_genes()
    test_oversized_chromosome_is_rejected()
    print("PASS: latest training weight synchronization checks")
