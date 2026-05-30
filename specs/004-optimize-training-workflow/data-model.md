# Data Model: Optimize Training Workflow

## Entities

### TrainingConfig

Represents one validated offline optimizer configuration.

**Fields**:
- `population_size`: positive integer, default `50`
- `generations`: positive integer, default `100`
- `games_per_genome`: positive integer, default `40`
- `mutation_rate`: number from `0` through `1`, default `0.20`
- `elite_ratio`: number from `0` through `1`, default `0.10`
- `tournament_size`: positive integer, default `5`
- `inject_ratio`: number from `0` through `1`, default `0.10`
- `variance_penalty`: non-negative number, default `0.15`
- `worker_count`: positive integer, default based on locally available CPU capacity
- `reproducibility_seed`: integer
- `training_dataset_path`: path to one seed dataset
- `validation_dataset_path`: optional path to a distinct seed dataset

**Derived fields**:
- `elite_count`: number of top genomes preserved each generation, derived from
  `population_size` and `elite_ratio`
- `inject_count`: number of genomes generated near the best candidate each generation,
  derived from `population_size` and `inject_ratio`

**Validation rules**:
- `tournament_size <= population_size`
- `games_per_genome <= training_dataset.scenario_count`
- `elite_count + inject_count <= population_size`
- Training and validation dataset paths must resolve to valid datasets.

### SeedDataset

Represents one persisted Common Random Numbers dataset.

**Fields**:
- `schema_version`: file format version
- `dataset_id`: human-readable stable identity
- `purpose`: `training` or `validation`
- `master_seed`: integer used to generate scenarios
- `scenario_count`: positive integer
- `turns_per_scenario`: fixed value `27`
- `created_at`: ISO-8601 timestamp
- `content_checksum`: checksum of canonical scenario content
- `scenarios`: ordered list of `GameplayScenario`

**Validation rules**:
- `scenario_count == len(scenarios)`
- `turns_per_scenario == 27`
- Recomputed checksum must equal `content_checksum`.

### GameplayScenario

Represents one deterministic complete-game workload.

**Fields**:
- `scenario_id`: stable index or generated identity within the dataset
- `content_checksum`: checksum used for overlap detection
- `blocks`: ordered list of 27 `Block` values

**Validation rules**:
- Exactly 27 blocks are present.
- Every block contains exactly three integers.
- Every block value is one of `{7, 8, 9, 10}`.

### CandidateEvaluation

Represents one genome's fitness result for one generation.

**Fields**:
- `candidate_index`: stable generation-local index
- `scenario_scores`: ordered final-game scores for the selected training scenarios
- `trimmed_mean_score`: mean after removing the fixed lowest and highest `10%` tails
- `score_stddev`: population standard deviation of all scenario scores
- `variance_penalty`: value copied from `TrainingConfig`
- `fitness`: `trimmed_mean_score - score_stddev * variance_penalty`

**Validation rules**:
- Every configured scenario contributes exactly one completed 27-turn score.
- Score order follows dataset scenario order.
- No synthetic random noise is added to fitness.

### GenerationSummary

Represents the committed result of one fully evaluated generation.

**Fields**:
- `generation_number`: positive integer
- `elapsed_seconds`: non-negative number
- `candidate_count`: number of successful evaluations
- `best_fitness`
- `average_fitness`
- `minimum_fitness`
- `best_chromosome`

**Validation rules**:
- A generation is committed only when `candidate_count == population_size`.
- Worker failure prevents the generation from being marked complete.

### TrainingRun

Represents one auditable offline optimization experiment.

**Fields**:
- `schema_version`
- `run_id`
- `status`: `running`, `completed`, `interrupted`, or `failed`
- `started_at`
- `updated_at`
- `completed_at`: optional
- `stop_reason`: optional
- `config`: validated `TrainingConfig`
- `training_dataset`: dataset identity and checksum
- `validation_dataset`: optional dataset identity and checksum
- `overlap_report`: scenario overlap count and identities
- `generation_summaries`: ordered list of completed `GenerationSummary` records
- `best_chromosome`: best available phase-based genome
- `best_fitness`: best available training fitness
- `validation_fitness`: optional final validation fitness

**Validation rules**:
- Updates are written after each completed generation and on terminal state changes.
- `best_chromosome` and configuration contain enough information to rerun evaluation.

## Relationships

- One `TrainingConfig` selects one training `SeedDataset` and optionally one validation
  `SeedDataset`.
- One `SeedDataset` contains many `GameplayScenario` values.
- One `TrainingRun` owns many `GenerationSummary` records.
- Each committed generation contains one `CandidateEvaluation` per population member.

## State Transitions

### Dataset Generation

1. Developer provides dataset identity, purpose, master seed, and scenario count.
2. Generator creates deterministic scenarios using a local random stream.
3. Generator calculates scenario and dataset checksums.
4. Validator checks structure and allowed values.
5. Dataset is written only after validation passes.

### Training Run

1. UI or CLI collects settings.
2. Configuration and selected datasets are validated.
3. Training and validation datasets are compared for scenario overlap.
4. A `running` summary is written.
5. Workers evaluate all genomes against the same training scenario subset.
6. The generation is committed only after every genome result returns.
7. Evolution creates the next population using configured elite, tournament, mutation,
   and injection settings.
8. Summary is updated after each committed generation.
9. Final validation evaluation runs against the validation dataset when configured.
10. Summary transitions to `completed`, `interrupted`, or `failed`.
