# Trading Immutable Execution Evidence

This feature module implements `FEAT-TRD-09`. The authoritative report
contract, query boundary, and requirement definitions are in
[`../README.md`](../README.md), Section 4.9.

`evidence.py` loads exact stored facts once and packages the registered
`ExecutionEvidenceReport v1`. External consumers use `build_trading_report`
through `app.services.trading`; the returned report class remains internal.

This feature is read-only and does not calculate performance, TCA, or other
Analytics-owned metrics.
