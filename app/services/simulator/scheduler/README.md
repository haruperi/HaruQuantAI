# Deterministic Execution Scheduler

`FEAT-SIM-15` owns Simulation's only simulated clock and event pump. Events
use the total-order key `(scheduled_at, priority, canonical_symbol,
source_sequence, scheduler_sequence)`. Runtime callbacks and futures are never
serialized; restore requires an explicit handler registry.

Public consumers use the function-only `app.services.simulator` boundary.
