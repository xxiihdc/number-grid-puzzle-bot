"""Reproducible JSON datasets for offline Common Random Numbers evaluation."""

from dataclasses import dataclass
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import random
from typing import Dict, Sequence, Tuple

from game_state import GameState

SCHEMA_VERSION = 1
Block = Tuple[int, int, int]


class DatasetValidationError(ValueError):
    """Raised when a persisted seed dataset is malformed."""


def _checksum(value: object) -> str:
    encoded = json.dumps(value, separators=(",", ":"), sort_keys=True).encode("utf-8")
    return f"sha256:{hashlib.sha256(encoded).hexdigest()}"


@dataclass(frozen=True)
class GameplayScenario:
    scenario_id: str
    content_checksum: str
    blocks: Tuple[Block, ...]

    @classmethod
    def from_blocks(cls, scenario_id: str, blocks: Sequence[Sequence[int]]) -> "GameplayScenario":
        normalized = tuple(tuple(int(value) for value in block) for block in blocks)
        scenario = cls(scenario_id, _checksum(normalized), normalized)
        scenario.validate()
        return scenario

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "GameplayScenario":
        blocks = tuple(tuple(block) for block in payload.get("blocks", []))
        scenario = cls(
            scenario_id=str(payload.get("scenario_id", "")),
            content_checksum=str(payload.get("content_checksum", "")),
            blocks=blocks,
        )
        scenario.validate()
        return scenario

    def validate(self) -> None:
        if not self.scenario_id:
            raise DatasetValidationError("scenario_id is required")
        if len(self.blocks) != GameState.TOTAL_TURNS:
            raise DatasetValidationError("scenario must contain exactly 27 blocks")
        for block in self.blocks:
            if len(block) != GameState.BLOCK_HEIGHT:
                raise DatasetValidationError("each block must contain exactly three values")
            if any(not isinstance(value, int) or value not in GameState.VALID_NUMBERS for value in block):
                raise DatasetValidationError("block values must be integers in {7, 8, 9, 10}")
        if self.content_checksum != _checksum(self.blocks):
            raise DatasetValidationError(f"scenario checksum mismatch: {self.scenario_id}")

    def to_dict(self) -> Dict[str, object]:
        return {
            "scenario_id": self.scenario_id,
            "content_checksum": self.content_checksum,
            "blocks": [list(block) for block in self.blocks],
        }


@dataclass(frozen=True)
class SeedDataset:
    schema_version: int
    dataset_id: str
    purpose: str
    master_seed: int
    scenario_count: int
    turns_per_scenario: int
    created_at: str
    content_checksum: str
    scenarios: Tuple[GameplayScenario, ...]

    @classmethod
    def from_dict(cls, payload: Dict[str, object]) -> "SeedDataset":
        scenarios = tuple(
            GameplayScenario.from_dict(scenario)
            for scenario in payload.get("scenarios", [])
        )
        dataset = cls(
            schema_version=payload.get("schema_version"),
            dataset_id=str(payload.get("dataset_id", "")),
            purpose=str(payload.get("purpose", "")),
            master_seed=payload.get("master_seed"),
            scenario_count=payload.get("scenario_count"),
            turns_per_scenario=payload.get("turns_per_scenario"),
            created_at=str(payload.get("created_at", "")),
            content_checksum=str(payload.get("content_checksum", "")),
            scenarios=scenarios,
        )
        dataset.validate()
        return dataset

    def validate(self) -> None:
        if self.schema_version != SCHEMA_VERSION:
            raise DatasetValidationError(f"unsupported schema_version: {self.schema_version}")
        if not self.dataset_id:
            raise DatasetValidationError("dataset_id is required")
        if self.purpose not in {"training", "validation"}:
            raise DatasetValidationError("purpose must be training or validation")
        if not isinstance(self.master_seed, int):
            raise DatasetValidationError("master_seed must be an integer")
        if not isinstance(self.scenario_count, int) or self.scenario_count <= 0:
            raise DatasetValidationError("scenario_count must be a positive integer")
        if self.scenario_count != len(self.scenarios):
            raise DatasetValidationError("scenario_count does not match scenarios")
        if self.turns_per_scenario != GameState.TOTAL_TURNS:
            raise DatasetValidationError("turns_per_scenario must equal 27")
        if not self.created_at:
            raise DatasetValidationError("created_at is required")
        for scenario in self.scenarios:
            scenario.validate()
        if self.content_checksum != _checksum([scenario.to_dict() for scenario in self.scenarios]):
            raise DatasetValidationError("dataset checksum mismatch")

    def to_dict(self) -> Dict[str, object]:
        return {
            "schema_version": self.schema_version,
            "dataset_id": self.dataset_id,
            "purpose": self.purpose,
            "master_seed": self.master_seed,
            "scenario_count": self.scenario_count,
            "turns_per_scenario": self.turns_per_scenario,
            "created_at": self.created_at,
            "content_checksum": self.content_checksum,
            "scenarios": [scenario.to_dict() for scenario in self.scenarios],
        }


def generate_dataset(dataset_id: str, purpose: str, master_seed: int,
                     scenario_count: int, created_at: str = None) -> SeedDataset:
    if purpose not in {"training", "validation"}:
        raise DatasetValidationError("purpose must be training or validation")
    if not isinstance(scenario_count, int) or scenario_count <= 0:
        raise DatasetValidationError("scenario_count must be a positive integer")
    rng = random.Random(master_seed)
    scenarios = []
    for index in range(1, scenario_count + 1):
        blocks = [
            tuple(rng.choice(GameState.VALID_NUMBER_SEQUENCE) for _ in range(GameState.BLOCK_HEIGHT))
            for _ in range(GameState.TOTAL_TURNS)
        ]
        scenarios.append(GameplayScenario.from_blocks(f"scenario-{index:04d}", blocks))
    scenarios_tuple = tuple(scenarios)
    dataset = SeedDataset(
        schema_version=SCHEMA_VERSION,
        dataset_id=dataset_id,
        purpose=purpose,
        master_seed=master_seed,
        scenario_count=scenario_count,
        turns_per_scenario=GameState.TOTAL_TURNS,
        created_at=created_at or datetime.now(timezone.utc).isoformat(),
        content_checksum=_checksum([scenario.to_dict() for scenario in scenarios_tuple]),
        scenarios=scenarios_tuple,
    )
    dataset.validate()
    return dataset


def save_dataset(dataset: SeedDataset, path: str, overwrite: bool = False) -> Path:
    dataset.validate()
    output = Path(path)
    if output.exists() and not overwrite:
        raise FileExistsError(f"dataset already exists: {output}")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(dataset.to_dict(), indent=2) + "\n", encoding="utf-8")
    return output


def load_dataset(path: str) -> SeedDataset:
    payload = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(payload, dict):
        raise DatasetValidationError("dataset root must be an object")
    return SeedDataset.from_dict(payload)


def compare_dataset_overlap(training: SeedDataset, validation: SeedDataset) -> Dict[str, object]:
    validation_checksums = {
        scenario.content_checksum: scenario.scenario_id
        for scenario in validation.scenarios
    }
    overlapping = [
        scenario.scenario_id
        for scenario in training.scenarios
        if scenario.content_checksum in validation_checksums
    ]
    return {"scenario_count": len(overlapping), "scenario_ids": overlapping}


def list_datasets(directory: str = "training_data") -> Tuple[SeedDataset, ...]:
    """Load valid datasets from one directory in stable filename order."""
    root = Path(directory)
    if not root.exists():
        return ()
    return tuple(load_dataset(str(path)) for path in sorted(root.glob("*.json")))
