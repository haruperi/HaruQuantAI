# Candlestick Patterns

This module owns `FEAT-INDI-02`: Doji, Engulfing, Pinbar, and Inside Bar
labelling. Each production file implements one official indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#46-candles--doji-engulfing-pinbar-and-inside-bar).
This file does not define a second Feature Registry.

Public consumers import `doji`, `engulfing`, `pinbar`, and `inside_bar` through
`app.services.indicators`. Calculations return
`StandardResponse[IndicatorResult]` and are pure, deterministic, and
persistence-free.
