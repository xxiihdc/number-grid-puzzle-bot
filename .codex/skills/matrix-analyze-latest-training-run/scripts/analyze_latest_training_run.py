#!/usr/bin/env python3
"""Summarize the newest Number Grid Puzzle GA training run without modifying files."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", help="Analyze this run summary instead of the newest run")
    parser.add_argument("--summary-directory", default="training_runs")
    parser.add_argument("--active-model", default="training_runs/active_chromosome.json")
    parser.add_argument("--trend-window", type=int, default=10)
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON")
    return parser


def _parse_timestamp(value: Any) -> Optional[datetime]:
    if not isinstance(value, str) or not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None


def _load_json(path: Path) -> Dict[str, Any]:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise ValueError(f"{path} must contain a JSON object")
    return payload


def find_latest_summary(directory: Path) -> Tuple[Path, Dict[str, Any]]:
    candidates: List[Tuple[Tuple[int, str, str], Path, Dict[str, Any]]] = []
    for path in directory.glob("train-*.json"):
        try:
            payload = _load_json(path)
        except (OSError, json.JSONDecodeError, ValueError):
            continue
        updated_at = _parse_timestamp(payload.get("updated_at"))
        sort_key = (
            1 if updated_at else 0,
            updated_at.isoformat() if updated_at else "",
            path.name,
        )
        candidates.append((sort_key, path, payload))
    if not candidates:
        raise ValueError(f"No parseable train-*.json summaries found in {directory}")
    _, path, payload = max(candidates, key=lambda item: item[0])
    return path, payload


def _numeric(values: Iterable[Any]) -> List[float]:
    return [float(value) for value in values if isinstance(value, (int, float))]


def _diagnostics(generations: List[Dict[str, Any]]) -> Dict[str, Any]:
    diagnostics = [
        generation.get("plateau_diagnostics")
        for generation in generations
        if isinstance(generation.get("plateau_diagnostics"), dict)
    ]
    if not diagnostics:
        return {"available": False}
    final = diagnostics[-1]
    diversity = _numeric(item.get("chromosome_diversity_ratio") for item in diagnostics)
    streaks = _numeric(item.get("no_improvement_generations") for item in diagnostics)
    return {
        "available": True,
        "final_diversity_ratio": final.get("chromosome_diversity_ratio"),
        "minimum_diversity_ratio": min(diversity) if diversity else None,
        "final_no_improvement_generations": final.get("no_improvement_generations"),
        "maximum_no_improvement_generations": int(max(streaks)) if streaks else None,
        "mutation_pulse_count": sum(
            item.get("adaptive_mutation_surge") is True for item in diagnostics
        ),
        "final_active_gene_count_min": final.get("active_gene_count_min"),
        "final_active_gene_count_average": final.get("active_gene_count_average"),
        "final_active_gene_count_max": final.get("active_gene_count_max"),
    }


def _active_context(path: Path, summary_path: Path, payload: Dict[str, Any]) -> Dict[str, Any]:
    if not path.exists():
        return {"available": False}
    try:
        active = _load_json(path)
    except (OSError, json.JSONDecodeError, ValueError) as error:
        return {"available": False, "error": str(error)}
    source_summary = active.get("source_summary")
    same_summary = False
    if isinstance(source_summary, str):
        same_summary = Path(source_summary).name == summary_path.name
    return {
        "available": True,
        "source_summary": source_summary,
        "source_run_id": active.get("source_run_id"),
        "same_as_analyzed_run": same_summary,
        "best_fitness": active.get("best_fitness"),
        "validation_fitness": active.get("validation_fitness"),
        "candidate_training_fitness_delta": _difference(
            payload.get("best_fitness"), active.get("best_fitness")
        ),
        "candidate_validation_fitness_delta": _difference(
            payload.get("validation_fitness"), active.get("validation_fitness")
        ),
    }


def _difference(left: Any, right: Any) -> Optional[float]:
    if isinstance(left, (int, float)) and isinstance(right, (int, float)):
        return float(left) - float(right)
    return None


def _recommendation(report: Dict[str, Any]) -> str:
    status = report["status"]
    if status == "failed":
        return "Inspect stop_reason and fix the failed run before starting another experiment."
    if not report["generation_count"]:
        return "Inspect the run setup because no completed generation is available."
    if status == "running":
        return "Continue monitoring the current run; do not start a competing experiment yet."
    if report["validation_fitness"] is None and report["has_validation_dataset"]:
        return "Replay the best chromosome on the recorded validation dataset before tuning or promotion."
    if report["validation_fitness"] is None:
        return "Generate or select a validation CRN dataset before trusting this candidate."
    diagnostics = report["plateau_diagnostics"]
    if (
        diagnostics.get("available")
        and (diagnostics.get("final_no_improvement_generations") or 0) >= 3
        and (report["recent_best_fitness_delta"] or 0) <= 0
    ):
        return "Treat this as a plateau: preserve the candidate and run one controlled exploration experiment."
    if not report["active_model"].get("same_as_analyzed_run"):
        return "Compare this candidate with the active chromosome on the same validation dataset before promotion."
    return "Keep this run as the current baseline and define one controlled follow-up experiment."


def analyze(summary_path: Path, payload: Dict[str, Any], active_model: Path,
            trend_window: int) -> Dict[str, Any]:
    if trend_window < 1:
        raise ValueError("--trend-window must be at least 1")
    generations = [
        generation for generation in payload.get("generation_summaries", [])
        if isinstance(generation, dict)
    ]
    best_values = _numeric(item.get("best_fitness") for item in generations)
    best_generation = None
    if best_values:
        maximum = max(best_values)
        best_generation = next(
            item.get("generation_number")
            for item in generations
            if item.get("best_fitness") == maximum
        )
    window = best_values[-trend_window:]
    recent_delta = window[-1] - window[0] if len(window) > 1 else None
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    report = {
        "summary_path": str(summary_path),
        "run_id": payload.get("run_id"),
        "status": payload.get("status", "unknown"),
        "stop_reason": payload.get("stop_reason"),
        "updated_at": payload.get("updated_at"),
        "generation_count": len(generations),
        "configured_generations": config.get("generations"),
        "population_size": config.get("population_size"),
        "games_per_genome": config.get("games_per_genome"),
        "worker_count": config.get("worker_count"),
        "mutation_rate": config.get("mutation_rate"),
        "best_fitness": payload.get("best_fitness"),
        "validation_fitness": payload.get("validation_fitness"),
        "validation_gap": _difference(payload.get("validation_fitness"), payload.get("best_fitness")),
        "has_validation_dataset": bool(config.get("validation_dataset_path")),
        "best_generation": best_generation,
        "recent_trend_window": min(trend_window, len(window)),
        "recent_best_fitness_delta": recent_delta,
        "total_generation_seconds": sum(
            _numeric(item.get("elapsed_seconds") for item in generations)
        ),
        "plateau_diagnostics": _diagnostics(generations),
        "active_model": _active_context(active_model, summary_path, payload),
    }
    report["recommendation"] = _recommendation(report)
    return report


def _format(value: Any, digits: int = 4) -> str:
    if value is None:
        return "unavailable"
    if isinstance(value, float):
        return f"{value:.{digits}f}"
    return str(value)


def render_markdown(report: Dict[str, Any]) -> str:
    diagnostics = report["plateau_diagnostics"]
    active = report["active_model"]
    lines = [
        "# Latest Training Run Analysis",
        "",
        f"- Summary: `{report['summary_path']}`",
        f"- Status: `{report['status']}` (`{_format(report['stop_reason'])}`)",
        f"- Generations: `{report['generation_count']}` / `{_format(report['configured_generations'])}`",
        f"- Config: population=`{_format(report['population_size'])}`, "
        f"games/genome=`{_format(report['games_per_genome'])}`, "
        f"workers=`{_format(report['worker_count'])}`, mutation=`{_format(report['mutation_rate'])}`",
        f"- Best fitness: `{_format(report['best_fitness'])}` at generation "
        f"`{_format(report['best_generation'])}`",
        f"- Validation fitness: `{_format(report['validation_fitness'])}` "
        f"(validation - training: `{_format(report['validation_gap'])}`)",
        f"- Recent best-fitness movement: `{_format(report['recent_best_fitness_delta'])}` "
        f"across `{report['recent_trend_window']}` generation(s)",
        f"- Recorded generation time: `{_format(report['total_generation_seconds'], 2)}` seconds",
    ]
    if diagnostics.get("available"):
        lines.extend([
            f"- Diversity: final=`{_format(diagnostics['final_diversity_ratio'])}`, "
            f"minimum=`{_format(diagnostics['minimum_diversity_ratio'])}`",
            f"- Plateau streak: final=`{_format(diagnostics['final_no_improvement_generations'])}`, "
            f"maximum=`{_format(diagnostics['maximum_no_improvement_generations'])}`",
            f"- Adaptive mutation pulses: `{_format(diagnostics['mutation_pulse_count'])}`",
            f"- Active genes in final population: min=`{_format(diagnostics['final_active_gene_count_min'])}`, "
            f"average=`{_format(diagnostics['final_active_gene_count_average'])}`, "
            f"max=`{_format(diagnostics['final_active_gene_count_max'])}`",
        ])
    else:
        lines.append("- Plateau diagnostics: `unavailable` (legacy or incomplete summary)")
    if active.get("available"):
        lines.append(
            f"- Active model: source=`{_format(active.get('source_summary'))}`, "
            f"same run=`{_format(active.get('same_as_analyzed_run'))}`"
        )
    else:
        lines.append("- Active model: `unavailable`")
    lines.extend(["", f"Recommendation: {report['recommendation']}"])
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.summary:
        summary_path = Path(args.summary)
        payload = _load_json(summary_path)
    else:
        summary_path, payload = find_latest_summary(Path(args.summary_directory))
    report = analyze(summary_path, payload, Path(args.active_model), args.trend_window)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
