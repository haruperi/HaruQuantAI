# Data Jobs — FEAT-DATA-13

Owns bounded backfill chunks, update-job lifecycle, status, and explicit recovery.
Public contracts and operations are imported from `app.services.data`.

- Production files: `backfill.py`, `contracts.py`, `job.py`, `recovery.py`.
- Requirements: FR-DATA-041–045 and FR-DATA-084.
- Usage evidence: `tests/data/usage/13_data_jobs.py`.
- Side effects: explicit persistence and approved source reads only.
