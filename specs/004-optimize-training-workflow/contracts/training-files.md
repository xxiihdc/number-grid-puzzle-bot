# Contract: Training JSON Files

## Seed Dataset

```json
{
  "schema_version": 1,
  "dataset_id": "train-default",
  "purpose": "training",
  "master_seed": 20260530,
  "scenario_count": 1,
  "turns_per_scenario": 27,
  "created_at": "2026-05-30T12:00:00Z",
  "content_checksum": "sha256:...",
  "scenarios": [
    {
      "scenario_id": "scenario-0001",
      "content_checksum": "sha256:...",
      "blocks": [
        [7, 8, 9]
      ]
    }
  ]
}
```

The abbreviated example shows one block. Persisted scenarios must contain exactly 27
blocks, each with three values from `{7, 8, 9, 10}`.

## Training Run Summary

```json
{
  "schema_version": 1,
  "run_id": "train-20260530T120000Z",
  "status": "running",
  "started_at": "2026-05-30T12:00:00Z",
  "updated_at": "2026-05-30T12:01:00Z",
  "completed_at": null,
  "stop_reason": null,
  "config": {
    "population_size": 50,
    "generations": 100,
    "games_per_genome": 40,
    "mutation_rate": 0.2,
    "elite_ratio": 0.1,
    "elite_count": 5,
    "tournament_size": 5,
    "inject_ratio": 0.1,
    "inject_count": 5,
    "variance_penalty": 0.15,
    "worker_count": 4,
    "reproducibility_seed": 20260530
  },
  "training_dataset": {
    "dataset_id": "train-default",
    "content_checksum": "sha256:..."
  },
  "validation_dataset": {
    "dataset_id": "validation-default",
    "content_checksum": "sha256:..."
  },
  "overlap_report": {
    "scenario_count": 0,
    "scenario_ids": []
  },
  "generation_summaries": [],
  "best_chromosome": null,
  "best_fitness": null,
  "validation_fitness": null
}
```

**Update contract**:
- Write the initial record before worker evaluation starts.
- Append one generation summary only after every population member is evaluated.
- Update the record after every committed generation.
- Preserve the best available chromosome when status becomes `completed`,
  `interrupted`, or `failed`.
