# Momentum Indicators

This module owns `FEAT-INDI-03`: RSI and Williams %R calculations. Each
production file implements one official indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#44-momentum--rsi-and-williams-r).
This file does not define a second Feature Registry.

Public consumers import `rsi` and `williams_r` through
`app.services.indicators`. Calculations return `StandardResponse[IndicatorResult]`
and are pure, deterministic, and persistence-free.
