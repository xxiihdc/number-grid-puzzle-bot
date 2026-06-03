# Research: Training Watchdog

## Decision: Run Watchdog Inside `run_training`

**Rationale**: The runner already appends and atomically writes generation summaries after each completed generation. Running the watchdog there avoids process killing, preserves the summary, and keeps the best chromosome available.

**Alternatives considered**: External file watcher that kills a process. Rejected because it can interrupt atomic writes and cannot update final status reliably.

## Decision: Conservative Plateau Stop Policy

**Rationale**: Stop when the global best has not improved for a configured patience window, minimum generations have elapsed, at least one adaptive mutation pulse has occurred, and the recent average has not recovered by the configured threshold. This matches existing whitepaper guidance to wait through mutation pulses and observe average fitness.

**Alternatives considered**: Stop on no-improvement streak alone. Rejected because GA plateaus can recover after adaptive mutation.

## Decision: Completed Status With `watchdog_plateau`

**Rationale**: A watchdog stop is intentional and preserves a usable candidate. It should be distinct from `interrupted` and `failed` while remaining auditable through `stop_reason`.

**Alternatives considered**: Add a new top-level status. Rejected to keep replay and existing status readers simple.
