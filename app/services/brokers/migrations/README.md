# Brokers Migrations (Support Directory)

> **Status:** Documented non-feature support directory — immutable schema definitions only.

Brokers persists five tables: `broker_symbol_map`, `broker_health_history`,
`broker_route_recovery`, `broker_environment_permissions`, and
`broker_event_checkpoints`. This directory is the immutable-schema half of the
single Brokers persistence concern; runtime CRUD remains in the sibling
`persistence/` support package.

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
