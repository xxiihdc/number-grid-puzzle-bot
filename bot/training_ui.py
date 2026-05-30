"""Interactive terminal configuration for offline training."""

from typing import Callable, Optional

from training_config import TrainingConfig, TrainingConfigError
from training_data import DatasetValidationError, list_datasets, load_dataset


FIELDS = (
    ("population_size", "Population size", int),
    ("generations", "Generations", int),
    ("games_per_genome", "Games evaluated per genome", int),
    ("mutation_rate", "Mutation rate", float),
    ("elite_ratio", "Elite ratio", float),
    ("tournament_size", "Tournament size", int),
    ("inject_ratio", "Random injection ratio", float),
    ("variance_penalty", "Variance penalty", float),
    ("worker_count", "Worker count", int),
    ("reproducibility_seed", "Reproducibility seed", int),
)


def collect_training_config(defaults: Optional[TrainingConfig] = None,
                            input_fn: Callable[[str], str] = input,
                            output_fn: Callable[[str], None] = print,
                            dataset_directory: str = "training_data") -> Optional[TrainingConfig]:
    """Prompt until a valid configuration is confirmed, or return None on cancel."""
    config = defaults or TrainingConfig()
    while True:
        available = list_datasets(dataset_directory)
        if available:
            output_fn("Available datasets:")
            for dataset in available:
                output_fn(f"  {dataset.dataset_id}: {dataset.purpose}, {dataset.scenario_count} scenarios")
        values = config.to_dict()
        values.pop("elite_count", None)
        values.pop("inject_count", None)
        try:
            for field_name, label, converter in FIELDS:
                raw = input_fn(f"{label} [{values[field_name]}]: ").strip()
                if raw:
                    values[field_name] = converter(raw)
            training_path = input_fn(f"Training dataset path [{values['training_dataset_path']}]: ").strip()
            if training_path:
                values["training_dataset_path"] = training_path
            validation_path = input_fn(
                f"Validation dataset path [{values['validation_dataset_path'] or ''}]: "
            ).strip()
            if validation_path:
                values["validation_dataset_path"] = validation_path
            candidate = TrainingConfig(**values)
            training_dataset = load_dataset(candidate.training_dataset_path)
            if candidate.validation_dataset_path:
                load_dataset(candidate.validation_dataset_path)
            candidate.validate(training_dataset.scenario_count)
        except (DatasetValidationError, OSError, TrainingConfigError, ValueError) as error:
            output_fn(f"Invalid configuration: {error}")
            config = TrainingConfig(**values)
            continue
        output_fn(f"Derived elite count: {candidate.elite_count}")
        output_fn(f"Derived injection count: {candidate.inject_count}")
        answer = input_fn("Start training? [y/N]: ").strip().lower()
        return candidate if answer in {"y", "yes"} else None
