# Brokers Migrations (Support Directory)

> **Status:** Documented non-feature support directory — immutable schema definitions only.

Brokers currently retains one temporary operational table: `broker_health_history`.
Canonical and provider symbol ownership has moved to Catalogue; environment and
runtime admission has moved to Workspace and Composition; event checkpoints and
stream reconciliation have moved to Data and Trading.

Immutable migration `001_broker_symbol_map_v1` remains byte-for-byte in the
manifest so applied ledgers stay verifiable. Additive migration
`003_retire_broker_symbol_map` drops that historical table only after a strict
zero-row guard succeeds. Additive migration
`004_retire_broker_environment_permissions` drops legacy
`broker_environment_permissions` after verifying zero rows. Additive migration
`005_retire_broker_event_and_route_recovery` drops legacy
`broker_event_checkpoints` and `broker_route_recovery` after verifying zero rows.
A non-empty table fails and rolls back unchanged. The migration never fabricates
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
