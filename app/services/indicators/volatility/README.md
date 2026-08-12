# Volatility Indicators

feature programme extends this feature with `measure_market_speed` and
`measure_volatility_envelope`. Both consume explicit causal measurements and
thresholds, perform no I/O, and publish no Risk regime or trading decision.

This module owns `FEAT-INDI-04`: ATR, ADR, rolling return volatility, rolling
price standard deviation, and the deterministic market-row projection consumed
by API orchestration. Each production file implements one focused calculation.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#43-volatility--atr-adr-rolling-volatility-and-standard-deviation).
This file does not define a second Feature Registry.

Public consumers import `atr`, `adr`, `rolling_volatility`,
`standard_deviation`, and `project_market_overlay` through
`app.services.indicators`. Calculations are pure, deterministic, and
persistence-free.
