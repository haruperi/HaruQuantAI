# Trading Validation, Readiness, and Plans

This feature module implements `FEAT-TRD-03`. The authoritative validation,
configuration, and requirement definitions are in
[`../README.md`](../README.md), Section 4.3.

`orders.py` validates requests, `snapshots.py` normalizes route evidence,
`readiness.py` aggregates freshness and gate evidence, `plans.py` builds
side-effect-free intents, `authority.py` validates exact Risk policy, decision,
and kill-switch authority, and `factories.py` constructs readiness/snapshot
evidence without exporting their classes. External consumers use documented
functions through `app.services.trading`.

Validation is deterministic and fails closed before allocation, persistence,
or external mutation.
