#!/usr/bin/env python3
"""Generate one reusable Common Random Numbers dataset."""

import argparse
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "bot"))

from training_data import generate_dataset, save_dataset


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dataset-id", required=True)
    parser.add_argument("--purpose", required=True, choices=("training", "validation"))
    parser.add_argument("--master-seed", required=True, type=int)
    parser.add_argument("--scenarios", required=True, type=int)
    parser.add_argument("--output", required=True)
    parser.add_argument("--overwrite", action="store_true")
    return parser


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    dataset = generate_dataset(args.dataset_id, args.purpose, args.master_seed, args.scenarios)
    path = save_dataset(dataset, args.output, overwrite=args.overwrite)
    print(
        f"Saved dataset={dataset.dataset_id} scenarios={dataset.scenario_count} "
        f"checksum={dataset.content_checksum} path={path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
