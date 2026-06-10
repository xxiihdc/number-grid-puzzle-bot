#!/usr/bin/env python3
"""Recommend directional heuristic weight adjustments from GA training summaries."""

from __future__ import annotations

import argparse
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import shlex
import statistics
from typing import DefaultDict, Dict, Iterable, List, Optional, Sequence, Tuple


PHASE_NAMES = ("opening", "midgame", "endgame")
FEATURE_NAMES = (
    "f1_actual_score",
    "f2_potential_horizontal_pairs",
    "f3_potential_diagonal_pairs",
    "f4_column_bumpiness",
    "f5_center_bias",
    "f6_isolated_slots",
    "f7_dead_ends",
    "f8_max_height",
    "f9_number_density_7",
    "f10_number_density_8",
    "f11_number_density_9",
    "f12_number_density_10",
    "f13_vertical_match_interfaces",
    "f14_empty_slots_count",
    "f15_diagonal_cross_points",
    "f16_open_single_windows",
    "f17_open_pair_windows",
    "f18_blocked_windows",
    "f19_multi_line_completion_cells",
)
REPORT_TYPE = "matrix_weight_adjustment_recommendation"
EVIDENCE_SCOPE = "generation_best_chromosomes_only"
POPULATION_EVIDENCE_SCOPE = "population_telemetry_and_generation_best_chromosomes"


@dataclass(frozen=True)
class GeneValue:
    mask: int
    weight: float


@dataclass(frozen=True)
class RunRecord:
    path: Path
    payload: Dict[str, object]


def _load_json(path: Path) -> Optional[Dict[str, object]]:
    try:
        return json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return None


def _parse_time(value: object) -> str:
    return str(value or "")


def _candidate_paths(summary: Optional[str], runs_dir: Path) -> List[Path]:
    if summary:
        return [Path(summary)]
    return sorted(runs_dir.glob("train-*.json"))


def _load_runs(paths: Sequence[Path]) -> List[RunRecord]:
    runs: List[RunRecord] = []
    for path in paths:
        payload = _load_json(path)
        if not isinstance(payload, dict):
            continue
        if not isinstance(payload.get("generation_summaries"), list):
            continue
        runs.append(RunRecord(path=path, payload=payload))
    return sorted(
        runs,
        key=lambda run: (
            _parse_time(run.payload.get("updated_at")),
            str(run.path),
        ),
    )


def _chromosome_genes(chromosome: object) -> Dict[Tuple[int, int], GeneValue]:
    if not isinstance(chromosome, dict):
        return {}
    genes = chromosome.get("genes")
    if not isinstance(genes, list):
        return {}
    parsed: Dict[Tuple[int, int], GeneValue] = {}
    for phase_index, phase_genes in enumerate(genes):
        if not isinstance(phase_genes, list):
            continue
        for feature_index, gene in enumerate(phase_genes):
            if not isinstance(gene, dict):
                continue
            try:
                parsed[(phase_index, feature_index)] = GeneValue(
                    mask=int(gene.get("mask", 0)),
                    weight=float(gene.get("weight", 0.0)),
                )
            except (TypeError, ValueError):
                continue
    return parsed


def _has_population_telemetry(runs: Sequence[RunRecord]) -> bool:
    for run in runs:
        for summary in run.payload.get("generation_summaries", []):
            if not isinstance(summary, dict):
                continue
            telemetry = summary.get("population_telemetry")
            if (
                isinstance(telemetry, dict)
                and isinstance(telemetry.get("ranked_candidates"), list)
                and telemetry["ranked_candidates"]
            ):
                return True
    return False


def _generation_series(run: RunRecord) -> List[Tuple[int, float, Dict[Tuple[int, int], GeneValue]]]:
    series: List[Tuple[int, float, Dict[Tuple[int, int], GeneValue]]] = []
    for summary in run.payload.get("generation_summaries", []):
        if not isinstance(summary, dict):
            continue
        chromosome = _chromosome_genes(summary.get("best_chromosome"))
        if not chromosome:
            continue
        try:
            generation_number = int(summary.get("generation_number", len(series) + 1))
            fitness = float(summary.get("best_fitness"))
        except (TypeError, ValueError):
            continue
        series.append((generation_number, fitness, chromosome))
    return series


def _run_quality(run: RunRecord) -> Optional[float]:
    value = run.payload.get("validation_fitness")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    value = run.payload.get("best_fitness")
    if isinstance(value, (int, float)) and not isinstance(value, bool):
        return float(value)
    return None


def _dataset_key(reference: object) -> Optional[str]:
    if not isinstance(reference, dict):
        return None
    dataset_id = reference.get("dataset_id")
    checksum = reference.get("content_checksum")
    if dataset_id or checksum:
        return f"{dataset_id}|{checksum}"
    return None


def _phase_name(index: int) -> str:
    return PHASE_NAMES[index] if 0 <= index < len(PHASE_NAMES) else f"phase_{index}"


def _feature_name(index: int) -> str:
    return FEATURE_NAMES[index] if 0 <= index < len(FEATURE_NAMES) else f"feature_{index}"


def _mean(values: Sequence[float]) -> Optional[float]:
    return sum(values) / len(values) if values else None


def _confidence(event_count: int, validation_runs: int, agrees_with_validation: bool) -> str:
    if validation_runs >= 3 and event_count >= 3 and agrees_with_validation:
        return "high"
    if validation_runs >= 1 and (event_count >= 2 or agrees_with_validation):
        return "medium"
    return "low"


def _suggested_delta(signal: float) -> float:
    if signal == 0:
        return 0.0
    magnitude = min(10.0, max(2.0, abs(signal) * 0.25))
    return round(magnitude if signal > 0 else -magnitude, 4)


def _collect_run_final_weights(
    runs: Sequence[RunRecord],
) -> DefaultDict[Tuple[int, int], List[Tuple[float, float, int, str]]]:
    values: DefaultDict[Tuple[int, int], List[Tuple[float, float, int, str]]] = defaultdict(list)
    for run in runs:
        quality = _run_quality(run)
        if quality is None:
            continue
        final = _chromosome_genes(run.payload.get("best_chromosome"))
        if not final:
            series = _generation_series(run)
            final = series[-1][2] if series else {}
        validation_key = _dataset_key(run.payload.get("validation_dataset")) or "no_validation_dataset"
        for key, gene in final.items():
            values[key].append((quality, gene.weight, gene.mask, validation_key))
    return values


def _collect_population_rank_signals(
    runs: Sequence[RunRecord],
) -> DefaultDict[Tuple[int, int], List[float]]:
    signals: DefaultDict[Tuple[int, int], List[float]] = defaultdict(list)
    for run in runs:
        for summary in run.payload.get("generation_summaries", []):
            if not isinstance(summary, dict):
                continue
            telemetry = summary.get("population_telemetry")
            if not isinstance(telemetry, dict):
                continue
            candidates = telemetry.get("ranked_candidates")
            if not isinstance(candidates, list) or len(candidates) < 2:
                continue
            parsed = []
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                try:
                    fitness = float(candidate["fitness"])
                except (KeyError, TypeError, ValueError):
                    continue
                genes = _chromosome_genes(candidate.get("chromosome"))
                if genes:
                    parsed.append((fitness, genes))
            if len(parsed) < 2:
                continue
            parsed.sort(key=lambda item: item[0], reverse=True)
            split = max(1, len(parsed) // 2)
            top = parsed[:split]
            bottom = parsed[split:]
            if not bottom:
                continue
            keys = set.intersection(*(set(genes) for _, genes in parsed))
            for key in keys:
                top_weight = _mean([genes[key].weight for _, genes in top])
                bottom_weight = _mean([genes[key].weight for _, genes in bottom])
                if top_weight is None or bottom_weight is None:
                    continue
                delta = top_weight - bottom_weight
                if abs(delta) >= 1e-9:
                    signals[key].append(delta)
    return signals


def _collect_population_mask_signals(
    runs: Sequence[RunRecord],
) -> DefaultDict[Tuple[int, int], List[float]]:
    signals: DefaultDict[Tuple[int, int], List[float]] = defaultdict(list)
    for run in runs:
        for summary in run.payload.get("generation_summaries", []):
            if not isinstance(summary, dict):
                continue
            telemetry = summary.get("population_telemetry")
            if not isinstance(telemetry, dict):
                continue
            candidates = telemetry.get("ranked_candidates")
            if not isinstance(candidates, list) or len(candidates) < 2:
                continue
            parsed = []
            for candidate in candidates:
                if not isinstance(candidate, dict):
                    continue
                try:
                    fitness = float(candidate["fitness"])
                except (KeyError, TypeError, ValueError):
                    continue
                genes = _chromosome_genes(candidate.get("chromosome"))
                if genes:
                    parsed.append((fitness, genes))
            if len(parsed) < 2:
                continue
            parsed.sort(key=lambda item: item[0], reverse=True)
            split = max(1, len(parsed) // 2)
            top = parsed[:split]
            bottom = parsed[split:]
            if not bottom:
                continue
            keys = set.intersection(*(set(genes) for _, genes in parsed))
            for key in keys:
                top_ratio = _mean([genes[key].mask for _, genes in top])
                bottom_ratio = _mean([genes[key].mask for _, genes in bottom])
                if top_ratio is None or bottom_ratio is None:
                    continue
                delta = top_ratio - bottom_ratio
                if abs(delta) >= 1e-9:
                    signals[key].append(delta)
    return signals


def _analyze_datasets(runs: Sequence[RunRecord]) -> Dict[str, object]:
    training = Counter(
        key for key in (_dataset_key(run.payload.get("training_dataset")) for run in runs) if key
    )
    validation = Counter(
        key for key in (_dataset_key(run.payload.get("validation_dataset")) for run in runs) if key
    )
    validation_count = sum(
        1
        for run in runs
        if isinstance(run.payload.get("validation_fitness"), (int, float))
        and not isinstance(run.payload.get("validation_fitness"), bool)
    )
    warnings: List[str] = []
    if len(validation) > 1:
        warnings.append("Multiple validation dataset checksums are present; compare recommendations cautiously.")
    if validation_count < len(runs):
        warnings.append("Some runs do not include validation_fitness; training fitness is lower-confidence evidence.")
    if not validation_count:
        warnings.append("No validation_fitness values found; recommendations are exploratory only.")
    return {
        "training_groups": [
            {"dataset_key": key, "run_count": count} for key, count in training.most_common()
        ],
        "validation_groups": [
            {"dataset_key": key, "run_count": count} for key, count in validation.most_common()
        ],
        "validated_run_count": validation_count,
        "warnings": warnings,
    }


def _build_phase_recommendations(runs: Sequence[RunRecord]) -> List[Dict[str, object]]:
    improving_deltas: DefaultDict[Tuple[int, int], List[float]] = defaultdict(list)
    flat_or_declining_deltas: DefaultDict[Tuple[int, int], List[float]] = defaultdict(list)
    population_rank_signals = _collect_population_rank_signals(runs)

    for run in runs:
        series = _generation_series(run)
        for previous, current in zip(series, series[1:]):
            _, previous_fitness, previous_genes = previous
            _, current_fitness, current_genes = current
            outcome_delta = current_fitness - previous_fitness
            keys = set(previous_genes) & set(current_genes)
            for key in keys:
                delta = current_genes[key].weight - previous_genes[key].weight
                if abs(delta) < 1e-9:
                    continue
                if outcome_delta > 0:
                    improving_deltas[key].append(delta)
                else:
                    flat_or_declining_deltas[key].append(delta)

    final_weights = _collect_run_final_weights(runs)
    validation_runs = sum(
        1
        for run in runs
        if isinstance(run.payload.get("validation_fitness"), (int, float))
        and not isinstance(run.payload.get("validation_fitness"), bool)
    )
    recommendations: List[Dict[str, object]] = []

    for key in sorted(set(improving_deltas) | set(final_weights) | set(population_rank_signals)):
        phase_index, feature_index = key
        improving_mean = _mean(improving_deltas.get(key, []))
        flat_mean = _mean(flat_or_declining_deltas.get(key, []))
        population_signal = _mean(population_rank_signals.get(key, []))
        validation_signal = 0.0
        observations = final_weights.get(key, [])
        evidence: List[str] = []

        if len(observations) >= 2:
            sorted_obs = sorted(observations, key=lambda item: item[0], reverse=True)
            split = max(1, len(sorted_obs) // 2)
            top_weight = _mean([item[1] for item in sorted_obs[:split]])
            rest_weight = _mean([item[1] for item in sorted_obs[split:]])
            if top_weight is not None and rest_weight is not None:
                validation_signal = top_weight - rest_weight
                evidence.append(
                    f"Top-outcome final weights average {top_weight:.4f} vs {rest_weight:.4f} for lower outcomes."
                )

        signals: List[float] = []
        if improving_mean is not None:
            signals.append(improving_mean)
            evidence.append(f"Improving generation deltas average {improving_mean:.4f}.")
        if population_signal is not None:
            signals.append(population_signal)
            evidence.append(f"Ranked population top-vs-bottom weight signal averages {population_signal:.4f}.")
        if abs(validation_signal) > 1e-9:
            signals.append(validation_signal)
        if not signals:
            continue

        signal = statistics.median(signals)
        if abs(signal) < 1.0:
            decision = "stabilize"
        elif signal > 0:
            decision = "increase"
        else:
            decision = "decrease"
        if flat_mean is not None and abs(flat_mean) > abs(signal) and decision != "stabilize":
            evidence.append(f"Flat/declining deltas average {flat_mean:.4f}; treat direction cautiously.")

        agrees_with_validation = bool(validation_signal and signal * validation_signal > 0)
        event_count = len(improving_deltas.get(key, [])) + len(population_rank_signals.get(key, []))
        confidence = _confidence(event_count, validation_runs, agrees_with_validation)

        recommendations.append(
            {
                "phase": _phase_name(phase_index),
                "phase_index": phase_index,
                "feature_index": feature_index,
                "decision": decision,
                "suggested_delta": _suggested_delta(signal) if decision != "stabilize" else 0.0,
                "confidence": confidence,
                "signal": round(signal, 6),
                "evidence": evidence,
            }
        )

    priority = {"high": 0, "medium": 1, "low": 2}
    return sorted(
        recommendations,
        key=lambda item: (
            priority.get(str(item["confidence"]), 3),
            -abs(float(item["signal"])),
            item["phase_index"],
            item["feature_index"],
        ),
    )


def _build_mask_recommendations(runs: Sequence[RunRecord]) -> List[Dict[str, object]]:
    final_weights = _collect_run_final_weights(runs)
    population_mask_signals = _collect_population_mask_signals(runs)
    recommendations: List[Dict[str, object]] = []
    for phase_index, feature_index in sorted(set(final_weights) | set(population_mask_signals)):
        observations = final_weights.get((phase_index, feature_index), [])
        population_signal = _mean(population_mask_signals.get((phase_index, feature_index), []))
        evidence = []
        confidence = "low"
        diff = 0.0
        if population_signal is not None:
            diff = population_signal
            confidence = "medium" if len(population_mask_signals[(phase_index, feature_index)]) >= 2 else "low"
            evidence.append(
                f"Ranked population top-vs-bottom mask activation signal averages {population_signal:.2f}."
            )
        if len(observations) < 2 and population_signal is None:
            continue
        sorted_obs = sorted(observations, key=lambda item: item[0], reverse=True)
        split = max(1, len(sorted_obs) // 2)
        top_ratio = _mean([item[2] for item in sorted_obs[:split]])
        rest_ratio = _mean([item[2] for item in sorted_obs[split:]])
        if top_ratio is not None and rest_ratio is not None:
            diff = statistics.median([diff, top_ratio - rest_ratio]) if population_signal is not None else top_ratio - rest_ratio
            evidence.append(
                f"Top-outcome mask activation ratio {top_ratio:.2f} vs {rest_ratio:.2f} for lower outcomes."
            )
        if abs(diff) < 0.25:
            continue
        decision = "prefer_enabled" if diff > 0 else "prefer_disabled"
        recommendations.append(
            {
                "phase": _phase_name(phase_index),
                "phase_index": phase_index,
                "feature_index": feature_index,
                "decision": decision,
                "confidence": confidence if population_signal is not None else ("medium" if len(observations) >= 4 else "low"),
                "evidence": evidence,
            }
        )
    priority = {"medium": 0, "low": 1}
    return sorted(
        recommendations,
        key=lambda item: (
            priority.get(str(item["confidence"]), 2),
            item["phase_index"],
            item["feature_index"],
        ),
    )


def _clamp_weight(value: float) -> float:
    return max(-100.0, min(100.0, value))


def _load_active_payload(output_directory: Path) -> Optional[Dict[str, object]]:
    active_path = output_directory / "active_chromosome.json"
    payload = _load_json(active_path)
    if not isinstance(payload, dict):
        return None
    chromosome = payload.get("chromosome")
    if not isinstance(chromosome, dict) or not isinstance(chromosome.get("genes"), list):
        return None
    return payload


def _clone_json_payload(payload: Dict[str, object]) -> Dict[str, object]:
    return json.loads(json.dumps(payload))


def _format_weights_by_phase(genes: object) -> Dict[str, List[Dict[str, object]]]:
    if not isinstance(genes, list):
        return {}
    formatted: Dict[str, List[Dict[str, object]]] = {}
    for phase_index, phase_genes in enumerate(genes):
        if not isinstance(phase_genes, list):
            continue
        rows: List[Dict[str, object]] = []
        for feature_index, gene in enumerate(phase_genes):
            if not isinstance(gene, dict):
                continue
            rows.append(
                {
                    "feature_index": feature_index,
                    "feature_number": feature_index + 1,
                    "feature_name": _feature_name(feature_index),
                    "mask": gene.get("mask"),
                    "weight": gene.get("weight"),
                }
            )
        formatted[_phase_name(phase_index)] = rows
    return formatted


def _training_command(output_directory: Path) -> List[str]:
    return [
        "python3",
        "run_bot.py",
        "train",
        "--non-interactive",
        "--population-size",
        "40",
        "--generations",
        "40",
        "--games-per-genome",
        "20",
        "--mutation-rate",
        "0.10",
        "--elite-ratio",
        "0.10",
        "--tournament-size",
        "4",
        "--inject-ratio",
        "0.15",
        "--variance-penalty",
        "0.15",
        "--workers",
        "8",
        "--seed",
        "20260610",
        "--watchdog-patience",
        "12",
        "--watchdog-min-generations",
        "10",
        "--watchdog-min-delta",
        "0.0",
        "--watchdog-average-recovery",
        "0.0",
        "--training-dataset",
        "training_data/train-10m.json",
        "--validation-dataset",
        "training_data/validation-10m.json",
        "--output-directory",
        str(output_directory),
    ]


def _build_candidate_experiment(
    report: Dict[str, object],
    output_directory: Path,
    analysis_path: Path,
    timestamp: str,
) -> Dict[str, object]:
    """Create a ready-to-run candidate active model from high-confidence deltas."""
    active_payload = _load_active_payload(output_directory)
    experiment_directory = output_directory / f"experiment-adjusted-high-confidence-{timestamp}"
    candidate_path = experiment_directory / "active_chromosome.json"
    command = _training_command(experiment_directory)
    mask_changes: List[Dict[str, object]] = []
    for recommendation in report.get("mask_recommendations", []):
        if recommendation.get("confidence") != "medium":
            continue
        feature_index = int(recommendation["feature_index"])
        mask_changes.append(
            {
                "phase": recommendation["phase"],
                "phase_index": recommendation["phase_index"],
                "feature_index": feature_index,
                "feature_number": feature_index + 1,
                "feature_name": _feature_name(feature_index),
                "decision": recommendation["decision"],
                "confidence": recommendation["confidence"],
            }
        )

    if active_payload is None:
        return {
            "status": "unavailable",
            "reason": f"No active chromosome found at {output_directory / 'active_chromosome.json'}.",
            "policy": {
                "applied_weight_confidences": ["high"],
                "applied_mask_confidences": [],
                "mask_changes_are_advisory": True,
            },
            "candidate_active_model_path": str(candidate_path),
            "training_command": command,
            "training_command_text": shlex.join(command),
            "optional_mask_changes": mask_changes,
        }

    candidate_payload = _clone_json_payload(active_payload)
    chromosome = candidate_payload["chromosome"]
    genes = chromosome["genes"]
    applied_weight_changes: List[Dict[str, object]] = []
    for recommendation in report.get("phase_recommendations", []):
        if recommendation.get("confidence") != "high":
            continue
        suggested_delta = float(recommendation.get("suggested_delta", 0.0))
        if suggested_delta == 0.0:
            continue
        phase_index = int(recommendation["phase_index"])
        feature_index = int(recommendation["feature_index"])
        try:
            gene = genes[phase_index][feature_index]
            old_weight = float(gene.get("weight", 0.0))
        except (IndexError, TypeError, ValueError, AttributeError):
            continue
        new_weight = _clamp_weight(old_weight + suggested_delta)
        gene["weight"] = new_weight
        applied_weight_changes.append(
            {
                "phase": recommendation["phase"],
                "phase_index": phase_index,
                "feature_index": feature_index,
                "feature_number": feature_index + 1,
                "feature_name": _feature_name(feature_index),
                "decision": recommendation["decision"],
                "old_weight": old_weight,
                "suggested_delta": suggested_delta,
                "new_weight": new_weight,
                "confidence": recommendation["confidence"],
            }
        )

    candidate_payload.update(
        {
            "schema_version": 1,
            "synced_at": datetime.now(timezone.utc).isoformat(),
            "source_summary": str(analysis_path),
            "source_run_id": "weight-adjusted-high-confidence-candidate",
        }
    )
    experiment_directory.mkdir(parents=True, exist_ok=True)
    candidate_path.write_text(json.dumps(candidate_payload, indent=2) + "\n", encoding="utf-8")

    return {
        "status": "ready",
        "policy": {
            "applied_weight_confidences": ["high"],
            "applied_mask_confidences": [],
            "mask_changes_are_advisory": True,
            "weight_bounds": [-100.0, 100.0],
        },
        "baseline_active_model_path": str(output_directory / "active_chromosome.json"),
        "candidate_active_model_path": str(candidate_path),
        "output_directory": str(experiment_directory),
        "training_command": command,
        "training_command_text": shlex.join(command),
        "applied_weight_changes": applied_weight_changes,
        "optional_mask_changes": mask_changes,
        "weights_by_phase": _format_weights_by_phase(genes),
    }


def build_report(runs: Sequence[RunRecord], output_directory: Path) -> Dict[str, object]:
    created_at = datetime.now(timezone.utc).isoformat()
    has_population_telemetry = _has_population_telemetry(runs)
    evidence_scope = POPULATION_EVIDENCE_SCOPE if has_population_telemetry else EVIDENCE_SCOPE
    datasets = _analyze_datasets(runs)
    phase_recommendations = _build_phase_recommendations(runs)
    mask_recommendations = _build_mask_recommendations(runs)
    high_or_medium = [
        item for item in phase_recommendations if item.get("confidence") in {"high", "medium"}
    ]
    confidence = "medium" if high_or_medium else "low"
    if not runs:
        confidence = "low"
    caveats = [
        "Recommendations are directional and should be validated with controlled runs.",
    ]
    if has_population_telemetry:
        caveats.append("Population telemetry is available for some summaries; old summaries may still only expose generation-best chromosomes.")
    else:
        caveats.append("MVP only observes generation-best chromosomes, not the full population.")
    caveats.extend(datasets["warnings"])
    action = (
        "run_adjusted_weight_experiment"
        if phase_recommendations
        else "collect_more_validated_training_evidence"
    )
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    analysis_path = output_directory / f"weight-adjustment-recommendation-{timestamp}.json"
    report: Dict[str, object] = {
        "schema_version": 1,
        "report_type": REPORT_TYPE,
        "analysis_mode": "read_only",
        "created_at": created_at,
        "evidence_scope": evidence_scope,
        "runs_analyzed": [
            {
                "path": str(run.path),
                "run_id": run.payload.get("run_id"),
                "status": run.payload.get("status"),
                "stop_reason": run.payload.get("stop_reason"),
                "generation_count": len(run.payload.get("generation_summaries", [])),
                "best_fitness": run.payload.get("best_fitness"),
                "validation_fitness": run.payload.get("validation_fitness"),
            }
            for run in runs
        ],
        "datasets": datasets,
        "global_assessment": {
            "confidence": confidence,
            "summary": (
                f"Analyzed {len(runs)} run(s); "
                f"{len(phase_recommendations)} phase/feature recommendation(s) generated."
            ),
            "caveats": caveats,
        },
        "phase_recommendations": phase_recommendations,
        "mask_recommendations": mask_recommendations,
        "next_training_command_hints": {
            "mutation_rate": 0.10,
            "inject_ratio": 0.15,
            "tournament_size": 4,
        },
        "recommended_next_action": {
            "action": action,
            "requires_explicit_user_request": True,
            "rationale": (
                "Use the highest-confidence directional weight recommendations in a controlled experiment."
                if phase_recommendations
                else "Current logs do not contain enough weight movement evidence."
            ),
        },
    }
    report["analysis_path"] = str(analysis_path)
    report["candidate_experiment"] = _build_candidate_experiment(
        report,
        output_directory,
        analysis_path,
        timestamp,
    )
    output_directory.mkdir(parents=True, exist_ok=True)
    analysis_path.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    return report


def _render_markdown(report: Dict[str, object]) -> str:
    lines = [
        "# Weight Adjustment Recommendation",
        "",
        f"- Runs analyzed: `{len(report['runs_analyzed'])}`",
        f"- Evidence scope: `{report['evidence_scope']}`",
        f"- Confidence: `{report['global_assessment']['confidence']}`",
        f"- Analysis path: `{report['analysis_path']}`",
        "",
        "## Ready-To-Run Candidate",
    ]
    candidate = report.get("candidate_experiment", {})
    if isinstance(candidate, dict) and candidate.get("status") == "ready":
        lines.extend(
            [
                f"- Candidate active model: `{candidate['candidate_active_model_path']}`",
                f"- Output directory: `{candidate['output_directory']}`",
                "- Training command:",
                "",
                "```sh",
                str(candidate["training_command_text"]),
                "```",
                "",
                f"- Applied high-confidence weight changes: `{len(candidate['applied_weight_changes'])}`",
                f"- Advisory mask changes not applied: `{len(candidate['optional_mask_changes'])}`",
                "",
            ]
        )
    elif isinstance(candidate, dict):
        lines.extend(
            [
                f"- Candidate status: `{candidate.get('status', 'unknown')}`",
                f"- Reason: {candidate.get('reason', 'No candidate details available.')}",
                "",
            ]
        )
    lines.extend(
        [
        "## Top Phase Recommendations",
        ]
    )
    for item in report["phase_recommendations"][:10]:
        feature_index = int(item["feature_index"])
        lines.append(
            "- "
            f"{item['phase']} `{_feature_name(feature_index)}` "
            f"(f{feature_index + 1}, index `{feature_index}`): "
            f"`{item['decision']}` by `{item['suggested_delta']}` "
            f"(confidence `{item['confidence']}`, signal `{item['signal']}`)"
        )
    if not report["phase_recommendations"]:
        lines.append("- No directional phase recommendations found.")
    lines.extend(["", "## Caveats"])
    for caveat in report["global_assessment"]["caveats"]:
        lines.append(f"- {caveat}")
    lines.extend(
        [
            "",
            "## Recommended Next Action",
            f"- `{report['recommended_next_action']['action']}`",
            f"- {report['recommended_next_action']['rationale']}",
        ]
    )
    return "\n".join(lines)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--summary", help="Analyze one training summary instead of all train-*.json files.")
    parser.add_argument("--runs-dir", default="training_runs", help="Directory containing training summaries.")
    parser.add_argument("--json", action="store_true", help="Emit machine-readable JSON.")
    args = parser.parse_args(argv)

    runs_dir = Path(args.runs_dir)
    runs = _load_runs(_candidate_paths(args.summary, runs_dir))
    report = build_report(runs, runs_dir)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(_render_markdown(report))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
