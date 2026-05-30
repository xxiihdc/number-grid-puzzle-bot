#!/usr/bin/env python3
"""Focused checks for deterministic completed-game training fitness."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.features import FeaturePool
from bot.genetics import Chromosome, GamePhase
from bot.game_state import GameState
from bot.training_data import generate_dataset
from bot.training_runner import calculate_candidate_evaluation, select_training_slot, simulate_scenario


def _chromosome(weight=0.0):
    chromosome = Chromosome(len(FeaturePool().get_feature_names()))
    for phase in GamePhase:
        for feature_idx in range(chromosome.num_features):
            chromosome.set_gene(phase, feature_idx, 1, weight)
    return chromosome


def test_stable_tie_breaking():
    state = GameState()
    slot = select_training_slot(state, (7, 8, 9), _chromosome())
    assert slot == GameState.ALL_VALID_SLOTS[0]


def test_completed_game_is_deterministic():
    scenario = generate_dataset("train", "training", 123, 1, created_at="fixed").scenarios[0]
    first = simulate_scenario(_chromosome(), scenario)
    second = simulate_scenario(_chromosome(), scenario)
    assert first == second


def test_fitness_has_no_synthetic_noise():
    scenarios = generate_dataset("train", "training", 123, 4, created_at="fixed").scenarios
    first = calculate_candidate_evaluation(0, _chromosome(), scenarios, 0.15)
    second = calculate_candidate_evaluation(0, _chromosome(), scenarios, 0.15)
    assert first == second
    assert first.fitness == first.trimmed_mean_score - first.score_stddev * 0.15


if __name__ == "__main__":
    test_stable_tie_breaking()
    test_completed_game_is_deterministic()
    test_fitness_has_no_synthetic_noise()
    print("PASS: deterministic training runner checks")
