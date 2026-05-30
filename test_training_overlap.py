#!/usr/bin/env python3
"""Checks for training and validation scenario overlap reports."""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "bot"))

from bot.training_data import SeedDataset, compare_dataset_overlap, generate_dataset


def test_complete_overlap():
    training = generate_dataset("train", "training", 123, 2, created_at="fixed")
    validation_payload = training.to_dict()
    validation_payload["dataset_id"] = "validation"
    validation_payload["purpose"] = "validation"
    validation = SeedDataset.from_dict(validation_payload)
    report = compare_dataset_overlap(training, validation)
    assert report["scenario_count"] == 2


def test_no_overlap():
    training = generate_dataset("train", "training", 123, 2, created_at="fixed")
    validation = generate_dataset("validation", "validation", 456, 2, created_at="fixed")
    assert compare_dataset_overlap(training, validation)["scenario_count"] == 0


if __name__ == "__main__":
    test_complete_overlap()
    test_no_overlap()
    print("PASS: dataset overlap checks")
