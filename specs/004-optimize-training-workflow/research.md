# Research Findings: Optimize Training Workflow

## Decision: Parallelize by Genome with Local Process Workers

**Chosen**: Evaluate one genome per process-pool task. Initialize each worker with the
selected scenario subset and immutable evaluation settings once, then send only genome
payloads for each generation.

**Rationale**: Genomes are independent within a generation, making them the natural
parallel unit. Passing the full dataset with every genome, as the legacy trainer does,
adds avoidable serialization overhead. Process workers bypass interpreter-level CPU
contention for CPU-heavy simulation and allow a worker count of one as a baseline.

**Alternatives considered**:
- Parallelize individual games: produces more tasks and repeats genome serialization.
- Use threads: simpler, but CPU-bound Python feature extraction does not reliably scale.
- Add remote workers: outside the local offline scope.

## Decision: Use Persisted Versioned JSON Seed Datasets

**Chosen**: Generate datasets from a master seed with a local random generator. Store
metadata and scenarios in versioned JSON, including a content checksum. Validate all
content before training and compare scenario checksums across training and validation
datasets to report overlap.

**Rationale**: JSON is inspectable, portable, and safer to load than arbitrary serialized
objects. A master seed makes generation reproducible, while a content checksum detects
accidental edits and gives run summaries a stable dataset reference.

**Alternatives considered**:
- Reuse pickle files from `ref/`: compact but opaque and unsafe to load from untrusted
  locations.
- Store only integer seeds: smaller, but less explicit when validating the exact
  scenarios used by historical experiments.
- Regenerate scenarios on every run: reproducible in principle, but weakens auditability.

## Decision: Use Deterministic Full-Game Fitness with One-Ply Selection

**Chosen**: For each scenario, simulate all 27 turns. At each turn, rank every valid
aligned slot using immediate score plus the candidate chromosome's heuristic leaf value,
then place the strongest slot with a stable tie-break order. Fitness is the trimmed mean
final score minus the configured population-standard-deviation penalty.

**Rationale**: The current `bot/genetics.py` evaluates an empty board and adds synthetic
noise, so it cannot optimize gameplay. A deterministic one-ply policy exercises the
heuristic throughout complete games while keeping the default workload tractable.
Wall-clock deadlines must not participate in offline evaluation because scheduling
differences would make multi-worker and single-worker results diverge.

**Alternatives considered**:
- Reuse runtime Expectimax deadlines: representative of game mode, but timing introduces
  nondeterministic fitness noise.
- Run unbounded phase-depth Expectimax for every training move: deterministic but too
  expensive for the default `50 x 40 x 27` evaluation workload.
- Evaluate partial boards: faster but does not measure completed-game outcomes.

## Decision: Keep Runtime Search and Training Policy Separate

**Chosen**: Reuse `GameState`, `FeaturePool`, chromosome evaluation, aligned-slot rules,
and local score calculation. Implement the deterministic training move selector in the
offline runner rather than changing runtime `ExpectimaxSearch`.

**Rationale**: Game mode has a strict move deadline and iterative deepening behavior.
Training has a reproducibility requirement. Sharing state mechanics but separating move
selection policies avoids weakening either contract.

**Alternatives considered**:
- Add a training mode flag inside runtime search: couples incompatible timing and
  reproducibility concerns.
- Duplicate game mechanics: creates scoring drift risk.

## Decision: Provide a Terminal UI with CLI Overrides

**Chosen**: Add an interactive terminal form for local use and CLI flags for scripted
runs. Both paths construct the same validated training configuration. Defaults mirror
the advanced legacy trainer: population `50`, generations `100`, games per genome `40`,
mutation rate `0.20`, elite ratio `0.10`, tournament size `5`, injection ratio `0.10`,
and variance penalty `0.15`.

**Rationale**: The repository is a local CLI bot and has no web stack. A terminal UI
meets the requirement to configure experiments without source edits while CLI overrides
make tests, benchmarks, and repeated experiments automatable.

**Alternatives considered**:
- Browser UI: adds a server and frontend stack without user value for local experiments.
- Configuration file only: scriptable, but does not satisfy the interactive workflow.
- Hard-coded constants: repeats the current usability problem.

## Decision: Record JSON Run Summaries Incrementally

**Chosen**: Create a run summary when training starts and update it after every completed
generation, on successful completion, and on interruption. Record configuration,
dataset identities and checksums, derived elite and injection counts, progress metrics,
best chromosome, and stop reason.

**Rationale**: Incremental summaries preserve useful results when training is interrupted
and provide the inputs required to rerun the evaluated workload.

**Alternatives considered**:
- Console logs only: difficult to validate and replay programmatically.
- Write only at successful completion: loses information on interrupted runs.
