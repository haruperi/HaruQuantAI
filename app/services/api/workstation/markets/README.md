# Markets Gateway Orchestration

## Purpose

Owns `FEAT-API-12` request orchestration for market-directory and quote reads.
It resolves configuration fail-closed, delegates evidence reads to Data, and
delegates calculations to Indicators.

## Boundaries

- No broker credentials are embedded or defaulted.
- No market formula is implemented in this feature.
- HTTP endpoints retain `/api/v1/data/markets` and `/api/v1/data/quotes`.
