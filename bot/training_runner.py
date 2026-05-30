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
    optimizer = GeneticOptimizer(
        FeaturePool(), ExpectimaxSearch(FeaturePool()), config=config, scenarios=scenarios
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
            if generation_number < config.generations:
                optimizer.evolve_from_evaluated(evaluated)

        if validation_dataset and optimizer.best_chromosome:
            validation = calculate_candidate_evaluation(
                0, optimizer.best_chromosome, validation_dataset.scenarios,
                config.variance_penalty
            )
            record["validation_fitness"] = validation.fitness
        _update_record(path, record, status="completed", completed_at=_now(),
                       stop_reason="max_generations")
    except KeyboardInterrupt:
        _update_record(path, record, status="interrupted", completed_at=_now(),
                       stop_reason="keyboard_interrupt")
        raise TrainingInterrupted(path)
    except Exception as error:
        _update_record(path, record, status="failed", completed_at=_now(),
                       stop_reason=str(error))
        raise
    return path


def replay_run(summary_path: str) -> CandidateEvaluation:
    """Reevaluate the recorded best chromosome against its training scenarios."""
    record = json.loads(Path(summary_path).read_text(encoding="utf-8"))
    if not record.get("best_chromosome"):
        raise ValueError("Run summary does not contain a best chromosome")
    config_payload = record["config"]
    dataset_path = config_payload["training_dataset_path"]
    dataset = load_dataset(dataset_path)
    chromosome = Chromosome.from_payload(record["best_chromosome"])
    scenarios = dataset.scenarios[:config_payload["games_per_genome"]]
    return calculate_candidate_evaluation(
        0, chromosome, scenarios, config_payload["variance_penalty"]
    )
