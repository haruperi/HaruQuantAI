# Brokers Persistence (Support Directory)

> **Status:** Documented non-feature support directory — CRUD statement construction only.

This is the temporary runtime-CRUD half of the remaining legacy Brokers
persistence concern. Canonical/provider symbol ownership has moved to Catalogue;
this exact five-file package now constructs statements only for the four
operational tables assigned to later ownership Tasks.

- `create.py` — insert immutable health history and explicit
  environment/account permissions.
- `read.py` — bounded permission, route-recovery, and event-checkpoint reads.
- `update.py` — atomically advance route or event checkpoints.
- `delete.py` — empty verb with an explicit empty `__all__`.

Every statement executes exclusively through `app.services.data`'s
`execute_transaction` with a caller-supplied `request_id`; authorization,
validation, policy, and orchestration stay in the owning feature modules. The
package root exposes only validated standalone operations; persistence
modules remain private. This directory is excluded from Feature Registry
reconciliation because it is documented CRUD infrastructure, not a feature
module.

Provider-symbol mappings are managed through `catalogue.map-providers@1`.
Callers select an exact mapping and pass its provider-native symbol unchanged to
the addressed Broker provider.
