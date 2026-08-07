# Brokers Persistence (Support Directory)

> **Status:** Documented non-feature support directory — CRUD statement construction only.

Canonical five-file layout for the one Brokers-owned table, `broker_symbol_map`
(the Brokers README database specification):

- `create.py` — insert one bitemporal mapping (`max_rows=1`).
- `read.py` — forward, reverse, and as-of bounded reads (`max_rows=1`).
- `update.py` — close or disable a mapping; history is never rewritten.
- `delete.py` — empty verb with an explicit empty `__all__`; a mapping that no
  longer applies is closed with an `effective_to` or disabled, never removed,
  so a backtest over an earlier period still resolves the instrument it
  actually traded.

Every statement executes exclusively through `app.services.data`'s
`execute_transaction` with a caller-supplied `request_id`; authorization,
validation, policy, and orchestration stay in the owning feature modules. This
directory is excluded from Feature Registry reconciliation: it is not a
feature module and exposes nothing through the Brokers public API.
