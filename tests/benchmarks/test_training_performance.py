#!/usr/bin/env python3
"""Bounded local speed report for offline process-worker evaluation."""

import os
import sys
import time

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), "bot"))

from bot.features import FeaturePool
from bot.genetics import Chromosome
from bot.training_data import generate_dataset
from bot.training_runner import evaluate_generation


def run_benchmark():
    scenarios = generate_dataset("benchmark", "training", 123, 4, created_at="fixed").scenarios
    chromosomes = [Chromosome(len(FeaturePool().get_feature_names())) for _ in range(4)]
    started = time.perf_counter()
    single = evaluate_generation(chromosomes, scenarios, 0.15, worker_count=1)
    single_elapsed = time.perf_counter() - started
    workers = min(2, os.cpu_count() or 1)
    started = time.perf_counter()
    parallel = evaluate_generation(chromosomes, scenarios, 0.15, worker_count=workers)
    parallel_elapsed = time.perf_counter() - started
    assert single == parallel
    speedup = 0.0 if not single_elapsed else 1 - parallel_elapsed / single_elapsed
    print(
        f"single={single_elapsed:.3f}s parallel={parallel_elapsed:.3f}s "
        f"workers={workers} speedup={speedup * 100:.1f}% target=30.0%"
    )
    return speedup


if __name__ == "__main__":
    run_benchmark()
