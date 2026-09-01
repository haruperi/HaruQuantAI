# Brokers Migrations (Support Directory)

> **Status:** Documented non-feature support directory — immutable schema definitions only.

Brokers currently retains three temporary operational tables:
`broker_health_history`, `broker_route_recovery`, and
`broker_event_checkpoints`. Canonical and
provider symbol ownership has moved to Catalogue; environment and runtime
admission has moved to Workspace and Composition.

Immutable migration `001_broker_symbol_map_v1` remains byte-for-byte in the
manifest so applied ledgers stay verifiable. Additive migration
`003_retire_broker_symbol_map` drops that historical table only after a strict
zero-row guard succeeds. Additive migration
`004_retire_broker_environment_permissions` drops legacy
`broker_environment_permissions` after verifying zero rows. A non-empty table
fails and rolls back unchanged. The migration never fabricates
identities absent from legacy rows.

- `definitions.py` owns the immutable additive migration steps with stable
  ordered-statement SHA-256 checksums and the authoritative manifest runner.
- `public.py` exposes `run_broker_migrations` lazily through the package root;
  API startup invokes it before readiness and fails closed on an unsuccessful
  result.
- Execution is delegated exclusively to Data's migration infrastructure;
  Brokers owns no database connections, transaction handles, or migration
  ledger.
- This directory is excluded from Feature Registry reconciliation: it is
  documented migration infrastructure, not a feature module.
