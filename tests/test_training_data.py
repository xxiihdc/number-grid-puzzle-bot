#!/usr/bin/env python3
"""Focused checks for persisted Common Random Numbers datasets."""

import json
import os
import sys
import tempfile

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(__file__)), "bot"))

from bot.training_data import DatasetValidationError, generate_dataset, load_dataset, save_dataset


def test_generation_is_reproducible():
    first = generate_dataset("train", "training", 123, 3, created_at="fixed")
    second = generate_dataset("train", "training", 123, 3, created_at="fixed")
    assert first.content_checksum == second.content_checksum
    assert first.scenarios == second.scenarios


def test_save_load_and_overwrite_protection():
    dataset = generate_dataset("train", "training", 123, 2, created_at="fixed")
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "train.json")
        save_dataset(dataset, path)
        loaded = load_dataset(path)
        assert loaded == dataset
        try:
            save_dataset(dataset, path)
        except FileExistsError:
            pass
        else:
            raise AssertionError("Expected overwrite protection")


def test_malformed_dataset_is_rejected():
    dataset = generate_dataset("train", "training", 123, 1, created_at="fixed").to_dict()
    dataset["scenarios"][0]["blocks"] = dataset["scenarios"][0]["blocks"][:-1]
    with tempfile.TemporaryDirectory() as temp_dir:
        path = os.path.join(temp_dir, "bad.json")
        with open(path, "w", encoding="utf-8") as output:
            json.dump(dataset, output)
        try:
            load_dataset(path)
        except DatasetValidationError:
            pass
        else:
            raise AssertionError("Expected malformed scenario rejection")


if __name__ == "__main__":
    test_generation_is_reproducible()
    test_save_load_and_overwrite_protection()
    test_malformed_dataset_is_rejected()
    print("PASS: training dataset checks")
