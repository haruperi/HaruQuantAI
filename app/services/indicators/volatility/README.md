# Volatility Indicators

feature programme extends this feature with `measure_market_speed` and
`measure_volatility_envelope`. Both consume explicit causal measurements and
thresholds, perform no I/O, and publish no Risk regime or trading decision.

This module owns `FEAT-INDI-04`: ATR, ADR, rolling return volatility, and
rolling price standard deviation. Each production file implements one official
indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#43-volatility--atr-adr-rolling-volatility-and-standard-deviation).
This file does not define a second Feature Registry.

Public consumers import `atr`, `adr`, `rolling_volatility`, and
`standard_deviation` through `app.services.indicators`. Calculations return
`StandardResponse[IndicatorResult]` and are pure, deterministic, and
persistence-free.
