# Brokers Persistence (Support Directory)

> **Status:** Documented non-feature support directory — CRUD statement construction only.

This is the runtime-CRUD half of the single Brokers persistence concern. Its
sibling `migrations/` package owns immutable schema evolution, while this exact
five-file package owns statement construction for all five Brokers tables.

- `create.py` — insert symbol mappings, immutable health history, and explicit
  environment/account permissions.
- `read.py` — bounded symbol, permission, route-recovery, and event-checkpoint
  reads.
- `update.py` — close/disable symbol mappings and atomically advance route or
  event checkpoints.
- `delete.py` — empty verb with an explicit empty `__all__`; a mapping that no
  longer applies is closed with an `effective_to` or disabled, never removed,
  so a backtest over an earlier period still resolves the instrument it
  actually traded.

Every statement executes exclusively through `app.services.data`'s
`execute_transaction` with a caller-supplied `request_id`; authorization,
validation, policy, and orchestration stay in the owning feature modules. The
package root exposes only validated standalone operations; persistence
modules remain private. This directory is excluded from Feature Registry
reconciliation because it is documented CRUD infrastructure, not a feature
module.
