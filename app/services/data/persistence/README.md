# Data Persistence — FEAT-DATA-06

Owns bounded SQLite transactions, migrations, locks, dataset/cache storage,
external import, backup, restore, retention, and approved path validation.

- Production files: backup, cache, contracts, writer, import, locking,
  migrations, paths, and transaction modules.
- Requirements: FR-DATA-014–016, 018–020, 105–106, and 108–110.
- Usage evidence: `tests/data/usage/06_persistence.py`.
- Side effects: explicit approved-root and configured SQLite writes only.
