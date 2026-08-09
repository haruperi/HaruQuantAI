# Trading State and Deterministic Projections

This feature module implements `FEAT-TRD-02`. The authoritative state,
persistence-port, and requirement definitions are in
[`../README.md`](../README.md), Section 4.2.

`events.py` defines immutable state evidence, `stores.py` defines the injected
persistence port, `idempotency.py` owns canonical reservation policy,
`projections.py` applies ordered optimistic durable events,
`execution_positions.py` owns the process-local nine-state execution-position
machine, and `migrations.py`
declares additive Trading-owned schema metadata without opening a database.
`factories.py` exposes construction and schema-version functions; state classes
and constants remain internal. External consumers use documented functions
through `app.services.trading`.

Data owns connection and migration execution infrastructure; this feature owns
only Trading records and schema declarations. `runtime.py` coordinates the
durable state port while every runtime-record create, read, and update operation
is implemented behind the private `app/services/trading/persistence` boundary.
Idempotency and projection updates remain compare-and-swap guarded, and events
remain append-only. Trading currently owns no runtime-record delete operation.

Current execution positions are never database records and are excluded from
serialized `TradingProjection` values. Restart or incomplete authority evidence
therefore produces an explicit `UNKNOWN` process-local state until reconciliation
succeeds. Exposure cannot increase from `UNKNOWN`. Only fully closed, reconciled
trade evidence is appended to the `trading_positions` ledger.
