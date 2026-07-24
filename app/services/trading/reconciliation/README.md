# Trading Reconciliation and Retry Guard

This feature module implements `FEAT-TRD-05`. The authoritative authority,
comparison, transition, and requirement definitions are in
[`../README.md`](../README.md), Section 4.5.

`snapshots.py` defines normalized authority evidence, `compare.py` performs
deterministic comparison, and `authority.py` persists retry-lock or approved
resolution transitions. External consumers use documented exports through
`app.services.trading`.

Unknown mutations remain retry-locked until persisted route-authority evidence
proves an allowed transition.
