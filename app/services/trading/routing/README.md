# Trading Authority Selection and Dispatch

This feature module implements `FEAT-TRD-04`. The authoritative routing,
adapter, timeout, and requirement definitions are in
[`../README.md`](../README.md), Section 4.4.

`capabilities.py` validates normalized provider declarations, `dispatcher.py`
owns the single asynchronous Simulation or Brokers mutation boundary, and
`responses.py` classifies authority results conservatively. External consumers
use only `validate_adapter_capability`, `dispatch_order_intent`, and
`classify_authority_response` through `app.services.trading`.

Unexpected provider exceptions, timeouts, and malformed successes become
redacted reconciliation-required receipts; raw provider objects and exceptions
do not cross the Trading boundary.
