# FEAT-SIM-16 Effective-Dated Calculation Model

This feature performs exact Decimal MT5 `FOREX` profit and netting/hedging
margin calculations over Data-provided half-open provider-specification
revisions and Data-owned FX conversion evidence. It admits no provider IO,
database reads, raw metadata interpretation, or unsupported calculation mode.

Currency results use the specification's explicit digits and rounding rule.
Missing, ambiguous, gapped, stale, or mismatched evidence fails closed. Offline
conformance artifacts bind exact expected/actual values to the stable model hash.
