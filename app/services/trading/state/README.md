# Trading State and Deterministic Projections

This feature module implements `FEAT-TRD-02`. The authoritative state,
persistence-port, and requirement definitions are in
[`../README.md`](../README.md), Section 4.2.

`events.py` defines immutable state evidence, `stores.py` defines the injected
persistence port, `idempotency.py` owns canonical reservation policy,
`projections.py` applies ordered optimistic events, and `migrations.py`
declares additive Trading-owned schema metadata without opening a database.
External consumers use documented exports through `app.services.trading`.

Data owns connection and migration execution infrastructure; this feature owns
only Trading records and schema declarations.
