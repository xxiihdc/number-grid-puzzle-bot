"""Validated configuration for offline genetic-algorithm training."""

from dataclasses import asdict, dataclass
import os
from typing import Dict, List, Optional


class TrainingConfigError(ValueError):
    """Raised when one or more training configuration fields are invalid."""

    def __init__(self, errors: List[str]):
        self.errors = errors
        super().__init__("; ".join(errors))


@dataclass(frozen=True)
class TrainingConfig:
    """Configuration shared by terminal, CLI, and offline runner entry points."""

    population_size: int = 50
    generations: int = 100
    games_per_genome: int = 40
    mutation_rate: float = 0.20
    elite_ratio: float = 0.10
    tournament_size: int = 5
    inject_ratio: float = 0.10
    variance_penalty: float = 0.15
    worker_count: int = max(1, os.cpu_count() or 1)
    reproducibility_seed: int = 20260530
    training_dataset_path: str = ""
    validation_dataset_path: Optional[str] = None

    @property
    def elite_count(self) -> int:
        return int(self.population_size * self.elite_ratio)

    @property
    def inject_count(self) -> int:
        return int(self.population_size * self.inject_ratio)

    def validate(self, training_scenario_count: Optional[int] = None) -> None:
        """Raise a field-oriented error if configuration cannot run."""
        errors = []
        positive_integers = (
            ("population_size", self.population_size),
            ("generations", self.generations),
            ("games_per_genome", self.games_per_genome),
            ("tournament_size", self.tournament_size),
            ("worker_count", self.worker_count),
        )
        for field_name, value in positive_integers:
            if not isinstance(value, int) or isinstance(value, bool) or value <= 0:
                errors.append(f"{field_name} must be a positive integer")

        for field_name, value in (
            ("mutation_rate", self.mutation_rate),
            ("elite_ratio", self.elite_ratio),
            ("inject_ratio", self.inject_ratio),
        ):
            if not isinstance(value, (int, float)) or isinstance(value, bool) or not 0 <= value <= 1:
                errors.append(f"{field_name} must be between 0 and 1")

        if (
            not isinstance(self.variance_penalty, (int, float))
            or isinstance(self.variance_penalty, bool)
            or self.variance_penalty < 0
        ):
            errors.append("variance_penalty must be non-negative")

        if (
            isinstance(self.tournament_size, int)
            and isinstance(self.population_size, int)
            and self.tournament_size > self.population_size
        ):
            errors.append("tournament_size must not exceed population_size")

        if (
            isinstance(self.population_size, int)
            and self.elite_count + self.inject_count > self.population_size
        ):
            errors.append("elite_count plus inject_count must not exceed population_size")

        if (
            training_scenario_count is not None
            and isinstance(self.games_per_genome, int)
            and self.games_per_genome > training_scenario_count
        ):
            errors.append("games_per_genome must not exceed available training scenarios")

        if not self.training_dataset_path:
            errors.append("training_dataset_path is required")

        if errors:
            raise TrainingConfigError(errors)

    def to_dict(self) -> Dict[str, object]:
        payload = asdict(self)
        payload["elite_count"] = self.elite_count
        payload["inject_count"] = self.inject_count
        return payload
