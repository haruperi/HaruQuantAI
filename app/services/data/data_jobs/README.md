# Data Jobs — FEAT-DATA-11

Owns bounded backfill chunks, update-job lifecycle, status, explicit recovery, and
the weekly Economic Calendar dispatch boundary.
Public contracts and operations are imported from `app.services.data`.

- Production files: `backfill.py`, `contracts.py`, `job.py`, `recovery.py`.
- Requirements: FR-DATA-041–045 and FR-DATA-084.
- Usage evidence: `tests/data/usage/features/13_data_jobs.py`.
- Additional scheduling requirement: `FR-DATA-174`.
- Side effects: delegates job/checkpoint CRUD to `data.persistence` and performs
  approved source reads only; final checkpoint/job changes remain atomic.
- Economic Calendar jobs are exclusive, exactly weekly, persist one explicit approved
  non-production environment, and dispatch only to the official current-week sync.
