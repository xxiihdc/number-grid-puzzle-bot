# Data Model: Training Watchdog

## Training Watchdog Configuration

- `watchdog_enabled`: Whether automatic early stopping is active.
- `watchdog_patience`: Consecutive no-improvement generations required before stop eligibility.
- `watchdog_min_delta`: Minimum global-best improvement that resets plateau tracking.
- `watchdog_min_generations`: Minimum completed generations before the watchdog can stop.
- `watchdog_average_recovery`: Minimum recent average-fitness recovery required to continue.

## Watchdog Decision

- `should_stop`: Boolean decision after a completed generation.
- `reason`: Machine-readable reason for stopping or continuing.
- `details`: Generation number, no-improvement count, mutation-pulse evidence, and recent average movement.

## Training Run Summary

Existing JSON summary fields remain unchanged. Watchdog settings are recorded inside `config`; watchdog termination uses `status = "completed"` and `stop_reason = "watchdog_plateau"`.
