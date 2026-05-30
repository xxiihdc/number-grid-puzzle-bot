#!/usr/bin/env python3
"""Plot fitness progress from one incremental training-run JSON summary."""

import argparse
import json
from pathlib import Path


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("summary", help="Path to training_runs/train-<timestamp>.json")
    parser.add_argument("--output", help="Optional PNG, PDF, or SVG output path")
    parser.add_argument("--no-ui", action="store_true", help="Do not open the chart window")
    return parser


def load_generation_series(path: str):
    """Load and validate generation-level fitness values from one training summary."""
    summary_path = Path(path)
    with summary_path.open(encoding="utf-8") as source:
        payload = json.load(source)
    generations = payload.get("generation_summaries")
    if not isinstance(generations, list) or not generations:
        raise ValueError("Training summary does not contain completed generations")

    required = ("generation_number", "best_fitness", "average_fitness", "minimum_fitness")
    for index, generation in enumerate(generations, start=1):
        if not isinstance(generation, dict) or any(key not in generation for key in required):
            raise ValueError(f"Generation entry {index} is missing required fitness fields")

    return {
        "run_id": str(payload.get("run_id", summary_path.stem)),
        "status": str(payload.get("status", "unknown")),
        "generations": [int(item["generation_number"]) for item in generations],
        "best": [float(item["best_fitness"]) for item in generations],
        "average": [float(item["average_fitness"]) for item in generations],
        "minimum": [float(item["minimum_fitness"]) for item in generations],
    }


def plot_training_series(series, output: str = None, show_ui: bool = True) -> None:
    """Render max, average, and minimum fitness progress."""
    import matplotlib.pyplot as plt

    figure, axis = plt.subplots(figsize=(11, 6))
    axis.plot(series["generations"], series["best"], label="Max fitness",
              color="#D62728", linewidth=2.2)
    axis.plot(series["generations"], series["average"], label="Average fitness",
              color="#1F77B4", linewidth=2.2)
    axis.plot(series["generations"], series["minimum"], label="Minimum fitness",
              color="#7F7F7F", linewidth=1.5, alpha=0.8)
    axis.set_title(f"Training Progress: {series['run_id']} ({series['status']})")
    axis.set_xlabel("Generation")
    axis.set_ylabel("Fitness score")
    axis.grid(True, linestyle="--", alpha=0.35)
    axis.legend()
    figure.tight_layout()

    if output:
        output_path = Path(output)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        figure.savefig(output_path, dpi=160)
        print(f"Saved chart: {output_path}")
    if show_ui:
        plt.show()
    else:
        plt.close(figure)


def main(argv=None) -> int:
    args = build_parser().parse_args(argv)
    series = load_generation_series(args.summary)
    print(
        f"run={series['run_id']} status={series['status']} "
        f"generations={len(series['generations'])} "
        f"latest_max={series['best'][-1]:.2f} "
        f"latest_avg={series['average'][-1]:.2f} "
        f"latest_min={series['minimum'][-1]:.2f}"
    )
    plot_training_series(series, output=args.output, show_ui=not args.no_ui)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
