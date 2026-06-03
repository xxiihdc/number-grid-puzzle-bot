#!/usr/bin/env python3
"""Command-line interface for play, offline training, and replay."""

import argparse
from dataclasses import replace


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="Number Grid Puzzle Bot")
    subparsers = parser.add_subparsers(dest="mode")
    subparsers.add_parser("play", help="Solve one puzzle")
    train = subparsers.add_parser("train", help="Optimize heuristic weights offline")
    train.add_argument("--non-interactive", action="store_true")
    train.add_argument("--population-size", type=int)
    train.add_argument("--generations", type=int)
    train.add_argument("--games-per-genome", type=int)
    train.add_argument("--mutation-rate", type=float)
    train.add_argument("--elite-ratio", type=float)
    train.add_argument("--tournament-size", type=int)
    train.add_argument("--inject-ratio", type=float)
    train.add_argument("--variance-penalty", type=float)
    train.add_argument("--workers", type=int)
    train.add_argument("--seed", type=int)
    train.add_argument("--training-dataset")
    train.add_argument("--validation-dataset")
    train.add_argument("--output-directory", default="training_runs")
    train.add_argument("--disable-watchdog", action="store_true")
    train.add_argument("--watchdog-patience", type=int)
    train.add_argument("--watchdog-min-delta", type=float)
    train.add_argument("--watchdog-min-generations", type=int)
    train.add_argument("--watchdog-average-recovery", type=float)
    replay = subparsers.add_parser("replay", help="Replay the best candidate from a run")
    replay.add_argument("summary_path")
    replay.add_argument("--dataset", choices=("training", "validation"), default="training")
    return parser


def config_from_args(args):
    """Apply provided CLI overrides to the legacy-compatible defaults."""
    from training_config import TrainingConfig

    mapping = {
        "population_size": args.population_size,
        "generations": args.generations,
        "games_per_genome": args.games_per_genome,
        "mutation_rate": args.mutation_rate,
        "elite_ratio": args.elite_ratio,
        "tournament_size": args.tournament_size,
        "inject_ratio": args.inject_ratio,
        "variance_penalty": args.variance_penalty,
        "worker_count": args.workers,
        "reproducibility_seed": args.seed,
        "training_dataset_path": args.training_dataset,
        "validation_dataset_path": args.validation_dataset,
        "watchdog_patience": args.watchdog_patience,
        "watchdog_min_delta": args.watchdog_min_delta,
        "watchdog_min_generations": args.watchdog_min_generations,
        "watchdog_average_recovery": args.watchdog_average_recovery,
    }
    overrides = {key: value for key, value in mapping.items() if value is not None}
    if args.disable_watchdog:
        overrides["watchdog_enabled"] = False
    return replace(TrainingConfig(), **overrides)


def run_cli(argv=None) -> int:
    args = build_parser().parse_args(argv)
    mode = args.mode or "play"
    if mode == "play":
        from main import run_play_mode
        run_play_mode()
        return 0
    if mode == "replay":
        from training_runner import replay_run
        evaluation = replay_run(args.summary_path, dataset_purpose=args.dataset)
        print(f"Replayed {args.dataset} fitness: {evaluation.fitness:.4f}")
        return 0

    from main import run_training_mode
    from training_ui import collect_training_config
    config = config_from_args(args)
    if args.non_interactive:
        if not config.training_dataset_path:
            raise SystemExit("--training-dataset is required with --non-interactive")
    else:
        config = collect_training_config(config)
        if config is None:
            print("Training cancelled.")
            return 0
    run_training_mode(config, args.output_directory)
    return 0


if __name__ == "__main__":
    raise SystemExit(run_cli())
