# Data Persistence — FEAT-DATA-06

Owns the private Data CRUD boundary plus bounded SQLite transactions, migrations,
locks, dataset/cache storage, external import, backup, restore, retention, and
approved path validation.

- CRUD files: `create.py`, `read.py`, `update.py`, and `delete.py`. Every Data-owned
  record statement lives here; compound source/audit, backfill/job, and runtime
  state/event changes remain one transaction.
- Infrastructure files: backup, cache orchestration, contracts, writer, import,
  locking, migrations, paths, and transactions.
- Requirements: FR-DATA-014–016, 018–020, 105–106, and 108–110.
- Usage evidence: `tests/data/usage/06_persistence.py`.
- Side effects: explicit approved-root and configured SQLite writes only.
