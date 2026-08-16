# Deterministic Execution Scheduler

`FEAT-SIM-15` owns Simulation's only simulated clock and event pump. Events
use the total-order key `(scheduled_at, priority, canonical_symbol,
source_sequence, scheduler_sequence)`. Runtime callbacks and futures are never
serialized; restore requires an explicit handler registry.

Phase 20 binds concern-specific realism streams into checkpoint state and admits
only complete canonical calibrated samples as `match_evaluation` or
`response_delivery` events. Restore preserves stream counters and pending-event
order exactly.

Public consumers use the function-only `app.services.simulator` boundary.
