# Trading Operational and Budget Evidence

This feature module implements `FEAT-TRD-06`. The authoritative monitoring,
budget-authority, incident, and requirement definitions are in
[`../README.md`](../README.md), Section 4.6.

`budgets.py` validates exact Risk-owned allocation and execution-budget
authority without calculating budgets. `events.py` owns bounded redacted
operational evidence and injected publication, including critical
`BROKER_STATE_UNKNOWN` events. `factories.py` constructs event evidence and
`validate_budget_authority` delegates to the internal budget gate. External
consumers use documented functions through `app.services.trading`.

Publication failures are surfaced and never rewrite execution or reconciliation
truth.
