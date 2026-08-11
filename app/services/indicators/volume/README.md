# Volume Indicators

feature programme extends this feature with `measure_order_flow` and the
validated JSON-safe `indicators.liquidity_snapshot.v1` build/parse boundary.
Unavailable fill probability remains null and is never inferred.

This module owns `FEAT-INDI-05`: CMF, OBV, MFI, and rolling price-volume point
of control. Each production file implements one official indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#45-volume--cmf-obv-mfi-and-price-volume-distribution).
This file does not define a second Feature Registry.

Public consumers import `cmf`, `obv`, `mfi`, and
`price_volume_distribution` through `app.services.indicators`. Calculations
return `StandardResponse[IndicatorResult]` and are pure, deterministic, and
persistence-free.
