# Markets Gateway Orchestration

## Purpose

Owns `FEAT-API-12` request orchestration for market-directory and quote reads.
It resolves configuration fail-closed, delegates evidence reads to Data, and
delegates calculations to Indicators.

## Boundaries

- No broker credentials are embedded or defaulted.
- No market formula is implemented in this feature.
- HTTP endpoints retain `/api/v1/data/markets` and `/api/v1/data/quotes`.
- ADR and change-in-pips prefer an explicit Data `pip_size` or exact
  `MT5_PIP_SIZES` entry such as `EURUSD=0.0001,XAUUSD=0.1`, then use ten genuine
  MT5 symbol points per pip from canonical `price_step` (or raw `point`). Digits
  and asset-class rules are never used.
