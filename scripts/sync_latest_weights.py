#!/usr/bin/env python3
"""Promote the newest trained chromosome into the active local model."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))

from training_weights import sync_latest_weights


def main(argv=None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary-directory", default="training_runs")
    parser.add_argument("--active-model", default="training_runs/active_chromosome.json")
    args = parser.parse_args(argv)
    path = sync_latest_weights(args.summary_directory, args.active_model)
    if path is None:
        print("No trained chromosome is available yet.")
        return 0
    print(f"Active chromosome: {path}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
