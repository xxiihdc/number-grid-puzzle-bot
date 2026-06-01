#!/usr/bin/env python3
"""Summarize the newest GA run and persist a handoff without modifying training state."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
from pathlib import Path
import sys
from typing import Any, Dict, Iterable, List, Optional, Tuple


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", help="Analyze this run summary instead of the newest run")
    parser.add_argument("--summary-directory", default="training_runs")
    parser.add_argument("--active-model", default="training_runs/active_chromosome.json")
    parser.add_argument("--trend-window", type=int, default=10)
    parser.add_argument(
        "--json",
        action="store_true",
        help="Emit versioned agent-handoff JSON instead of the human-readable report",
    )
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


def analysis_path_for_summary(summary_path: Path) -> Path:
    return summary_path.with_name(f"analysis-{summary_path.stem}.json")


def persist_analysis(path: Path, report: Dict[str, Any]) -> None:
    with path.open("x", encoding="utf-8", errors="strict") as output:
        output.write(f"{json.dumps(report, indent=2)}\n")


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
        "mutation_pulse_generations": [
            generation.get("generation_number")
            for generation in generations
            if isinstance(generation.get("plateau_diagnostics"), dict)
            and generation["plateau_diagnostics"].get("adaptive_mutation_surge") is True
        ],
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


def _recommended_next_action(report: Dict[str, Any]) -> Dict[str, Any]:
    status = report["status"]
    if status == "failed":
        return {
            "action": "inspect_failed_run",
            "rationale": "The run failed, so its stop reason must be diagnosed before another experiment.",
            "command": None,
            "requires_explicit_user_request": False,
        }
    if not report["generation_count"]:
        return {
            "action": "inspect_run_setup",
            "rationale": "No completed generation is available for evidence-based tuning.",
            "command": None,
            "requires_explicit_user_request": False,
        }
    if status == "running":
        return {
            "action": "continue_monitoring",
            "rationale": "The selected run is still active; avoid starting a competing experiment.",
            "command": None,
            "requires_explicit_user_request": False,
        }
    if report["validation_fitness"] is None and report["has_validation_dataset"]:
        return {
            "action": "replay_validation",
            "rationale": "The run records a validation dataset but has no validation fitness.",
            "command": (
                f"python3 run_bot.py replay {report['summary_path']} --dataset validation"
            ),
            "requires_explicit_user_request": False,
        }
    if report["validation_fitness"] is None:
        return {
            "action": "select_validation_dataset",
            "rationale": "No validation evidence is available for this candidate.",
            "command": None,
            "requires_explicit_user_request": False,
        }
    diagnostics = report["plateau_diagnostics"]
    if (
        diagnostics.get("available")
        and (diagnostics.get("final_no_improvement_generations") or 0) >= 3
        and (report["recent_best_fitness_delta"] or 0) <= 0
    ):
        return {
            "action": "run_controlled_exploration_experiment",
            "rationale": "Recent best fitness is flat and the no-improvement streak is at least three generations.",
            "command": None,
            "requires_explicit_user_request": True,
        }
    if not report["active_model"].get("same_as_analyzed_run"):
        return {
            "action": "compare_with_active_model",
            "rationale": "The analyzed candidate is not the active model; compare both on the same validation dataset.",
            "command": None,
            "requires_explicit_user_request": False,
        }
    return {
        "action": "run_controlled_follow_up_experiment",
        "rationale": "Keep this validated active run as the baseline and define one controlled follow-up experiment.",
        "command": None,
        "requires_explicit_user_request": True,
    }


def _assessment(report: Dict[str, Any]) -> Dict[str, Any]:
    diagnostics = report["plateau_diagnostics"]
    if not diagnostics.get("available"):
        plateau_status = "unavailable"
    elif (
        (diagnostics.get("final_no_improvement_generations") or 0) >= 3
        and (report["recent_best_fitness_delta"] or 0) <= 0
    ):
        plateau_status = "plateau_signal"
    elif (diagnostics.get("maximum_no_improvement_generations") or 0) >= 3:
        plateau_status = "historical_plateau_with_recent_improvement"
    else:
        plateau_status = "no_strong_plateau_signal"

    if report["validation_fitness"] is not None:
        validation_status = "available"
    elif report["has_validation_dataset"]:
        validation_status = "dataset_available_replay_required"
    else:
        validation_status = "missing_dataset"

    active = report["active_model"]
    if not active.get("available"):
        active_model_relation = "unavailable"
    elif active.get("same_as_analyzed_run"):
        active_model_relation = "same_run"
    else:
        active_model_relation = "different_run"

    facts = [
        f"Run status is {report['status']}.",
        f"Completed generations: {report['generation_count']} of {_format(report['configured_generations'])}.",
        f"Best training fitness: {_format(report['best_fitness'])}.",
        f"Validation fitness: {_format(report['validation_fitness'])}.",
    ]
    inferences = []
    caveats = [
        "Training fitness alone does not establish superiority on unseen scenarios.",
        "A high chromosome diversity ratio shows that chromosomes differ; it does not prove useful exploration.",
    ]
    if plateau_status == "historical_plateau_with_recent_improvement":
        inferences.append(
            "The run encountered plateau periods but still produced a later improvement."
        )
    elif plateau_status == "plateau_signal":
        inferences.append(
            "The recent flat trend and current no-improvement streak are evidence of a plateau."
        )
    if report["validation_gap"] is not None and report["validation_gap"] < 0:
        inferences.append(
            "Validation fitness is below training fitness; treat the negative gap as a generalization warning."
        )
    return {
        "plateau_status": plateau_status,
        "validation_status": validation_status,
        "active_model_relation": active_model_relation,
        "facts": facts,
        "inferences": inferences,
        "caveats": caveats,
    }


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
    initial_best = best_values[0] if best_values else None
    config = payload.get("config") if isinstance(payload.get("config"), dict) else {}
    report = {
        "schema_version": 1,
        "report_type": "matrix_training_run_analysis",
        "analysis_mode": "read_only",
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
        "initial_best_fitness": initial_best,
        "total_best_fitness_delta": _difference(payload.get("best_fitness"), initial_best),
        "improvement_generations": [
            item.get("generation_number")
            for index, item in enumerate(generations)
            if index == 0
            or (
                isinstance(item.get("best_fitness"), (int, float))
                and isinstance(generations[index - 1].get("best_fitness"), (int, float))
                and item["best_fitness"] > generations[index - 1]["best_fitness"]
            )
        ],
        "total_generation_seconds": sum(
            _numeric(item.get("elapsed_seconds") for item in generations)
        ),
        "datasets": {
            "training": payload.get("training_dataset"),
            "validation": payload.get("validation_dataset"),
            "overlap_report": payload.get("overlap_report"),
        },
        "plateau_diagnostics": _diagnostics(generations),
        "active_model": _active_context(active_model, summary_path, payload),
    }
    report["assessment"] = _assessment(report)
    report["recommended_next_action"] = _recommended_next_action(report)
    report["recommendation"] = report["recommended_next_action"]["rationale"]
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
    assessment = report["assessment"]
    action = report["recommended_next_action"]
    lines = [
        "# Latest Training Run Analysis",
        "",
        f"- Summary: `{report['summary_path']}`",
        f"- Persisted analysis: `{_format(report.get('analysis_path'))}`",
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
            f"- Mutation-pulse generations: `{_format(diagnostics['mutation_pulse_generations'])}`",
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
    lines.extend([
        "",
        "## Assessment",
        "",
        f"- Plateau status: `{assessment['plateau_status']}`",
        f"- Validation status: `{assessment['validation_status']}`",
        f"- Active-model relation: `{assessment['active_model_relation']}`",
    ])
    for inference in assessment["inferences"]:
        lines.append(f"- Inference: {inference}")
    for caveat in assessment["caveats"]:
        lines.append(f"- Caveat: {caveat}")
    lines.extend([
        "",
        "## Recommended Next Action",
        "",
        f"- Action: `{action['action']}`",
        f"- Rationale: {action['rationale']}",
    ])
    if action["command"]:
        lines.append(f"- Command: `{action['command']}`")
    lines.append(
        f"- Requires explicit user request: `{_format(action['requires_explicit_user_request'])}`"
    )
    return "\n".join(lines)


def main(argv: Optional[List[str]] = None) -> int:
    args = build_parser().parse_args(argv)
    if args.summary:
        summary_path = Path(args.summary)
        payload = _load_json(summary_path)
    else:
        summary_path, payload = find_latest_summary(Path(args.summary_directory))
    analysis_path = analysis_path_for_summary(summary_path)
    if analysis_path.exists():
        print(
            f"WARNING: analysis already exists for old log {summary_path}: {analysis_path}",
            file=sys.stderr,
        )
        return 2
    report = analyze(summary_path, payload, Path(args.active_model), args.trend_window)
    report["analysis_path"] = str(analysis_path)
    try:
        persist_analysis(analysis_path, report)
    except FileExistsError:
        print(
            f"WARNING: analysis already exists for old log {summary_path}: {analysis_path}",
            file=sys.stderr,
        )
        return 2
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
