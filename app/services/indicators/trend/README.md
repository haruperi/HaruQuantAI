# Trend Indicators

consolidated capability programme extends this feature with `measure_trend_strength` and
`project_structural_levels`. They project strategy-independent causal evidence;
Risk remains the authoritative regime-policy owner.

This module owns `FEAT-INDI-03`: EMA, SMA, WMA, Hull MA, Bollinger Bands, ADX,
and causal confirmed-pivot ZigZag calculations. Each production file implements
one official indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#42-trend--ema-sma-wma-hull-ma-bollinger-bands-adx-and-zigzag).
This file does not define a second Feature Registry.

Public consumers import `ema`, `sma`, `wma`, `hull_ma`, `bollinger_bands`,
`adx`, and `zigzag` through `app.services.indicators`. Calculations consume one
normalized Data-owned `MarketDataset v1`, return `IndicatorResult`, and perform
no persistence or external I/O. ZigZag publishes each unique alternating pivot
only on its causal confirmation row, never retrospectively on the center row.
