# Manage Jobs

`FEAT-ORCH-MANAGE_JOBS` owns idempotent job acceptance, optimistic lifecycle transitions, monotonic
progress, and isolated asynchronous progress callbacks. SQLite operations are confined to
`_persistence.py`; `_usage.py` is offline and creates no external effects.

This package closes the former shared progress-model/callback utility gap. The broader feature card
in the domain README remains `Partial`; resource admission, Workspace persistence, attempts,
checkpoint recovery, domain outcomes, and ancestry controls still require their planned features
and full acceptance evidence.
