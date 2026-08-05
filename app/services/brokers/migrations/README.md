# Brokers Migrations (Support Directory)

> **Status:** Documented non-feature support directory — immutable schema definitions only.

Brokers persists exactly one table: the bitemporal `broker_symbol_map`
provider-to-canonical symbol reference data (the `docs/PROJECT.md` §5
persisted-state ownership table and `docs/schema` decision D10). A
mis-mapped symbol routes an order to the wrong instrument, so this reference
data must be stable, versioned, and identical across restarts.

- `definitions.py` owns the single additive migration step with a stable
  ordered-statement SHA-256 checksum. Applied steps are immutable.
- Execution is delegated exclusively to Data's migration infrastructure;
  Brokers owns no database connections, transaction handles, or migration
  ledger.
- This directory is excluded from Feature Registry reconciliation: it is not a
  feature module and hosts no public behavior.
