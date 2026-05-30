"""Synchronize the newest trained chromosome into one active local model."""

from datetime import datetime, timezone
import json
from pathlib import Path
import tempfile
from typing import Optional

ACTIVE_MODEL_PATH = Path("training_runs/active_chromosome.json")


def _write_json_atomic(path: Path, payload) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=str(path.parent),
                                     delete=False) as output:
        json.dump(payload, output, indent=2)
        output.write("\n")
        temporary_path = Path(output.name)
    temporary_path.replace(path)


def sync_latest_weights(summary_directory: str = "training_runs",
                        active_model_path: str = None) -> Optional[Path]:
    """Promote the newest run summary that contains a best chromosome."""
    root = Path(summary_directory)
    active_path = Path(active_model_path) if active_model_path else ACTIVE_MODEL_PATH
    candidates = []
    if root.exists():
        for path in sorted(root.glob("train-*.json")):
            try:
                payload = json.loads(path.read_text(encoding="utf-8"))
            except (OSError, json.JSONDecodeError):
                continue
            if payload.get("best_chromosome"):
                candidates.append((str(payload.get("updated_at", "")), path, payload))
    if not candidates:
        return active_path if active_path.exists() else None

    _, source_path, latest = max(candidates, key=lambda candidate: (candidate[0], str(candidate[1])))
    active_payload = {
        "schema_version": 1,
        "synced_at": datetime.now(timezone.utc).isoformat(),
        "source_summary": str(source_path),
        "source_run_id": latest.get("run_id"),
        "best_fitness": latest.get("best_fitness"),
        "validation_fitness": latest.get("validation_fitness"),
        "chromosome": latest["best_chromosome"],
    }
    _write_json_atomic(active_path, active_payload)
    return active_path


def load_active_chromosome(active_model_path: str = None):
    """Load the promoted chromosome, or return None when no training result exists."""
    path = Path(active_model_path) if active_model_path else ACTIVE_MODEL_PATH
    if not path.exists():
        return None
    from genetics import Chromosome

    payload = json.loads(path.read_text(encoding="utf-8"))
    return Chromosome.from_payload(payload["chromosome"])
