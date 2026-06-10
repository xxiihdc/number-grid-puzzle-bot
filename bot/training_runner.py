"""Deterministic completed-game fitness evaluation for offline training."""

from concurrent.futures import ProcessPoolExecutor
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import statistics
import tempfile
import time
from typing import Dict, Iterable, List, Optional, Sequence, Tuple

from features import FeaturePool
from game_state import GameState
from genetics import Chromosome
from scoring import evaluate_board
from training_config import TrainingConfig
from training_data import GameplayScenario, compare_dataset_overlap, load_dataset
from training_weights import load_active_chromosome, sync_latest_weights


@dataclass(frozen=True)
class CandidateEvaluation:
    candidate_index: int
    scenario_scores: Tuple[int, ...]
    trimmed_mean_score: float
    score_stddev: float
    variance_penalty: float
    fitness: float

    def to_dict(self) -> Dict[str, object]:
        return asdict(self)


_WORKER_SCENARIOS: Tuple[GameplayScenario, ...] = ()
_WORKER_VARIANCE_PENALTY = 0.0


class TrainingInterrupted(KeyboardInterrupt):
    """Carries the preserved summary path for an interrupted training run."""

    def __init__(self, summary_path: Path):
        self.summary_path = summary_path
        super().__init__(str(summary_path))


@dataclass(frozen=True)
class WatchdogDecision:
    should_stop: bool
    reason: str
    details: Dict[str, object]


def select_training_slot(state: GameState, block: Sequence[int],
                         chromosome: Chromosome,
                         feature_pool: Optional[FeaturePool] = None) -> Tuple[int, int]:
    """Select one slot deterministically using immediate score plus leaf heuristic."""
    pool = feature_pool or FeaturePool()
    best_slot = None
    best_value = -float("inf")
    for x, y in state.get_valid_slots():
        score = state.place_block(x, y, block)
        try:
            value = score + chromosome.get_fitness(state, pool)
        finally:
            state._undo_block(x, y, score)
        if value > best_value:
            best_value = value
            best_slot = (x, y)
    if best_slot is None:
        raise ValueError("No valid training slot available")
    return best_slot


def simulate_scenario(chromosome: Chromosome, scenario: GameplayScenario) -> int:
    """Play all 27 deterministic blocks and return the final board score."""
    scenario.validate()
    state = GameState()
    pool = FeaturePool()
    for block in scenario.blocks:
        slot = select_training_slot(state, block, chromosome, pool)
        state.make_move(slot, block)
    if not state.is_game_over() or state.get_valid_slots():
        raise RuntimeError("Training simulation did not complete exactly 27 turns")
    return int(evaluate_board(state.get_grid_2d(), is_final=True))


def calculate_candidate_evaluation(candidate_index: int, chromosome: Chromosome,
                                   scenarios: Sequence[GameplayScenario],
                                   variance_penalty: float) -> CandidateEvaluation:
    """Aggregate completed-game scores into one deterministic fitness value."""
    if not scenarios:
        raise ValueError("At least one scenario is required")
    scores = tuple(simulate_scenario(chromosome, scenario) for scenario in scenarios)
    sorted_scores = sorted(scores)
    trim = int(len(sorted_scores) * 0.10)
    trimmed = sorted_scores[trim:-trim] if trim and len(sorted_scores) > 2 * trim else sorted_scores
    mean_score = sum(trimmed) / len(trimmed)
    stddev = statistics.pstdev(scores)
    fitness = mean_score - stddev * variance_penalty
    return CandidateEvaluation(
        candidate_index=candidate_index,
        scenario_scores=scores,
        trimmed_mean_score=mean_score,
        score_stddev=stddev,
        variance_penalty=variance_penalty,
        fitness=fitness,
    )


def _initialize_worker(scenarios: Sequence[GameplayScenario],
                       variance_penalty: float) -> None:
    global _WORKER_SCENARIOS, _WORKER_VARIANCE_PENALTY
    _WORKER_SCENARIOS = tuple(scenarios)
    _WORKER_VARIANCE_PENALTY = variance_penalty


def _evaluate_payload(task: Tuple[int, Dict[str, object]]) -> CandidateEvaluation:
    candidate_index, payload = task
    chromosome = Chromosome.from_payload(payload)
    return calculate_candidate_evaluation(
        candidate_index, chromosome, _WORKER_SCENARIOS, _WORKER_VARIANCE_PENALTY
    )


def evaluate_generation(chromosomes: Sequence[Chromosome],
                        scenarios: Sequence[GameplayScenario],
                        variance_penalty: float,
                        worker_count: int = 1) -> List[CandidateEvaluation]:
    """Evaluate every chromosome and reject incomplete worker results."""
    if worker_count <= 0:
        raise ValueError("worker_count must be positive")
    immutable_scenarios = tuple(scenarios)
    tasks = [(index, chromosome.to_payload()) for index, chromosome in enumerate(chromosomes)]
    if worker_count == 1:
        results = [
            calculate_candidate_evaluation(index, chromosome, immutable_scenarios, variance_penalty)
            for index, chromosome in enumerate(chromosomes)
        ]
    else:
        with ProcessPoolExecutor(
            max_workers=worker_count,
            initializer=_initialize_worker,
            initargs=(immutable_scenarios, variance_penalty),
        ) as executor:
            results = list(executor.map(_evaluate_payload, tasks))
    if len(results) != len(chromosomes):
        raise RuntimeError("Incomplete generation evaluation")
    return sorted(results, key=lambda result: result.candidate_index)


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _dataset_reference(dataset) -> Optional[Dict[str, object]]:
    if dataset is None:
        return None
    return {"dataset_id": dataset.dataset_id, "content_checksum": dataset.content_checksum}


def _write_json_atomic(path: Path, payload: Dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent),
                                     delete=False) as output:
        json.dump(payload, output, indent=2)
        output.write("\n")
        temporary_path = Path(output.name)
    temporary_path.replace(path)


def _update_record(path: Path, record: Dict[str, object], **updates) -> None:
    record.update(updates)
    record["updated_at"] = _now()
    _write_json_atomic(path, record)


def _build_population_telemetry(evaluated: Sequence[Tuple[Chromosome, float]]) -> Dict[str, object]:
    """Capture ranked population weights for downstream tuning analysis."""
    ranked_candidates = [
        {
            "rank": rank,
            "fitness": fitness,
            "chromosome": chromosome.to_payload(),
        }
        for rank, (chromosome, fitness) in enumerate(evaluated, start=1)
    ]
    if not evaluated:
        return {
            "schema_version": 1,
            "candidate_count": 0,
            "ranked_candidates": [],
            "gene_statistics": [],
        }

    first = evaluated[0][0]
    gene_statistics = []
    for phase_index in range(first.num_phases):
        for feature_index in range(first.num_features):
            weights = [
                chromosome.genes[phase_index][feature_index].weight
                for chromosome, _ in evaluated
            ]
            masks = [
                chromosome.genes[phase_index][feature_index].mask
                for chromosome, _ in evaluated
            ]
            gene_statistics.append({
                "phase_index": phase_index,
                "feature_index": feature_index,
                "weight_min": min(weights),
                "weight_mean": sum(weights) / len(weights),
                "weight_max": max(weights),
                "weight_stddev": statistics.pstdev(weights),
                "mask_activation_ratio": sum(masks) / len(masks),
            })

    return {
        "schema_version": 1,
        "candidate_count": len(evaluated),
        "ranked_candidates": ranked_candidates,
        "gene_statistics": gene_statistics,
    }


def evaluate_training_watchdog(config: TrainingConfig,
                               generation_summaries: Sequence[Dict[str, object]]) -> WatchdogDecision:
    """Decide whether a completed training generation indicates an ineffective run."""
    completed_generations = len(generation_summaries)
    details: Dict[str, object] = {"completed_generations": completed_generations}
    if not config.watchdog_enabled:
        return WatchdogDecision(False, "disabled", details)
    if completed_generations < config.watchdog_min_generations:
        return WatchdogDecision(False, "minimum_generations", details)

    best_so_far: Optional[float] = None
    no_improvement = 0
    for summary in generation_summaries:
        current_best = float(summary["best_fitness"])
        if best_so_far is None:
            best_so_far = current_best
            no_improvement = 0
            continue
        improvement = current_best - best_so_far
        meaningful_improvement = (
            improvement > 0
            if config.watchdog_min_delta == 0
            else improvement >= config.watchdog_min_delta
        )
        if meaningful_improvement:
            best_so_far = current_best
            no_improvement = 0
        else:
            no_improvement += 1
    details["no_improvement_generations"] = no_improvement
    if no_improvement < config.watchdog_patience:
        return WatchdogDecision(False, "patience", details)

    previous_summaries = generation_summaries[:-1]
    mutation_pulse_seen = any(
        bool(summary.get("plateau_diagnostics", {}).get("adaptive_mutation_surge"))
        for summary in previous_summaries
    )
    details["mutation_pulse_seen"] = mutation_pulse_seen
    if not mutation_pulse_seen:
        return WatchdogDecision(False, "awaiting_mutation_pulse", details)

    window = generation_summaries[-config.watchdog_patience:]
    average_values = [float(summary["average_fitness"]) for summary in window]
    average_recovery = average_values[-1] - min(average_values)
    details["average_recovery"] = average_recovery
    if (
        config.watchdog_average_recovery > 0
        and average_recovery >= config.watchdog_average_recovery
    ):
        return WatchdogDecision(False, "average_recovered", details)

    return WatchdogDecision(True, "watchdog_plateau", details)


def run_training(config: TrainingConfig, output_directory: str = "training_runs") -> Path:
    """Execute one auditable optimizer run and persist progress incrementally."""
    from expectimax import ExpectimaxSearch
    from genetics import GeneticOptimizer

    training_dataset = load_dataset(config.training_dataset_path)
    validation_dataset = (
        load_dataset(config.validation_dataset_path)
        if config.validation_dataset_path else None
    )
    if training_dataset.purpose != "training":
        raise ValueError("training_dataset_path must reference a training dataset")
    if validation_dataset and validation_dataset.purpose != "validation":
        raise ValueError("validation_dataset_path must reference a validation dataset")
    config.validate(training_dataset.scenario_count)
    overlap = (
        compare_dataset_overlap(training_dataset, validation_dataset)
        if validation_dataset else {"scenario_count": 0, "scenario_ids": []}
    )
    started_at = _now()
    run_id = "train-" + datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S.%fZ")
    path = Path(output_directory) / f"{run_id}.json"
    record = {
        "schema_version": 1,
        "run_id": run_id,
        "status": "running",
        "started_at": started_at,
        "updated_at": started_at,
        "completed_at": None,
        "stop_reason": None,
        "config": config.to_dict(),
        "training_dataset": _dataset_reference(training_dataset),
        "validation_dataset": _dataset_reference(validation_dataset),
        "overlap_report": overlap,
        "generation_summaries": [],
        "best_chromosome": None,
        "best_fitness": None,
        "validation_fitness": None,
    }
    _write_json_atomic(path, record)
    scenarios = training_dataset.scenarios[:config.games_per_genome]
    active_model_path = str(Path(output_directory) / "active_chromosome.json")
    sync_latest_weights(output_directory, active_model_path)
    initial_chromosome = load_active_chromosome(active_model_path)
    optimizer = GeneticOptimizer(
        FeaturePool(), ExpectimaxSearch(FeaturePool()), config=config, scenarios=scenarios,
        initial_chromosome=initial_chromosome,
    )
    try:
        for generation_number in range(1, config.generations + 1):
            started = time.perf_counter()
            evaluated = optimizer._evaluate_population()
            elapsed = time.perf_counter() - started
            best_fitness = evaluated[0][1]
            summary = {
                "generation_number": generation_number,
                "elapsed_seconds": elapsed,
                "candidate_count": len(evaluated),
                "best_fitness": best_fitness,
                "average_fitness": sum(fitness for _, fitness in evaluated) / len(evaluated),
                "minimum_fitness": evaluated[-1][1],
                "best_chromosome": evaluated[0][0].to_payload(),
                "plateau_diagnostics": optimizer.get_plateau_diagnostics(),
                "population_telemetry": _build_population_telemetry(evaluated),
            }
            if len(evaluated) != config.population_size:
                raise RuntimeError("Incomplete generation cannot be committed")
            record["generation_summaries"].append(summary)
            record["best_chromosome"] = optimizer.best_chromosome.to_payload()
            record["best_fitness"] = optimizer.best_fitness
            _update_record(path, record)
            print(
                f"Generation {generation_number}/{config.generations}: "
                f"best={summary['best_fitness']:.2f} "
                f"avg={summary['average_fitness']:.2f} elapsed={elapsed:.2f}s"
            )
            watchdog_decision = evaluate_training_watchdog(
                config, record["generation_summaries"]
            )
            if watchdog_decision.should_stop:
                record["watchdog_decision"] = {
                    "reason": watchdog_decision.reason,
                    "details": watchdog_decision.details,
                }
                break
            if generation_number < config.generations:
                optimizer.evolve_from_evaluated(evaluated)

        if validation_dataset and optimizer.best_chromosome:
            validation = calculate_candidate_evaluation(
                0, optimizer.best_chromosome, validation_dataset.scenarios,
                config.variance_penalty
            )
            record["validation_fitness"] = validation.fitness
        stop_reason = (
            "watchdog_plateau"
            if record.get("watchdog_decision", {}).get("reason") == "watchdog_plateau"
            else "max_generations"
        )
        _update_record(path, record, status="completed", completed_at=_now(),
                       stop_reason=stop_reason)
        sync_latest_weights(output_directory, active_model_path)
    except KeyboardInterrupt:
        _update_record(path, record, status="interrupted", completed_at=_now(),
                       stop_reason="keyboard_interrupt")
        raise TrainingInterrupted(path)
    except Exception as error:
        _update_record(path, record, status="failed", completed_at=_now(),
                       stop_reason=str(error))
        raise
    return path


def replay_run(summary_path: str, dataset_purpose: str = "training") -> CandidateEvaluation:
    """Reevaluate the recorded best chromosome against a recorded dataset."""
    record = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if not record.get("best_chromosome"):
        raise ValueError("Run summary does not contain a best chromosome")
    config_payload = record["config"]
    if dataset_purpose == "training":
        dataset_path = config_payload["training_dataset_path"]
    elif dataset_purpose == "validation":
        dataset_path = config_payload.get("validation_dataset_path")
        if not dataset_path:
            raise ValueError("Run summary does not reference a validation dataset")
    else:
        raise ValueError("dataset_purpose must be training or validation")
    dataset = load_dataset(dataset_path)
    chromosome = Chromosome.from_payload(record["best_chromosome"])
    scenarios = (
        dataset.scenarios[:config_payload["games_per_genome"]]
        if dataset_purpose == "training"
        else dataset.scenarios
    )
    return calculate_candidate_evaluation(
        0, chromosome, scenarios, config_payload["variance_penalty"]
    )
