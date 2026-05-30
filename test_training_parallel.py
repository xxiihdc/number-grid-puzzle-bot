#!/usr/bin/env python3
"""Worker-count equivalence checks for offline training evaluation."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.features import FeaturePool
from bot.genetics import Chromosome, GamePhase
from bot.training_data import generate_dataset
from bot.training_runner import evaluate_generation


def _chromosome(weight):
    chromosome = Chromosome(len(FeaturePool().get_feature_names()))
    for phase in GamePhase:
        for feature_idx in range(chromosome.num_features):
            chromosome.set_gene(phase, feature_idx, 1, weight)
    return chromosome


def test_worker_counts_are_equivalent():
    scenarios = generate_dataset("train", "training", 123, 2, created_at="fixed").scenarios
    chromosomes = [_chromosome(weight) for weight in (0.0, 0.5)]
    single = evaluate_generation(chromosomes, scenarios, 0.15, worker_count=1)
    parallel = evaluate_generation(chromosomes, scenarios, 0.15, worker_count=2)
    assert single == parallel
    assert [result.candidate_index for result in parallel] == [0, 1]


if __name__ == "__main__":
    test_worker_counts_are_equivalent()
    print("PASS: parallel worker equivalence checks")
