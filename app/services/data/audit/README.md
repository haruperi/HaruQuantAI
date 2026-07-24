# Audit Evidence — FEAT-DATA-15

Owns authorized persistence and bounded querying of redacted `AuditEvent v1`
evidence. Public contracts and operations are imported from `app.services.data`.

- Production files: `authorization.py`, `contracts.py`, `query.py`, `store.py`.
- Requirements: FR-DATA-021 and FR-DATA-077.
- Usage evidence: `tests/data/usage/15_audit.py`.
- Side effects: explicit SQLite persistence only; imports perform no I/O.
