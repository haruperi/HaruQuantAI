# Volume Indicators

This module owns `FEAT-INDI-06`: CMF, OBV, MFI, and rolling price-volume point
of control. Each production file implements one official indicator.

The canonical status, requirements, formulas, public signatures, and usage
evidence remain in the package
[`README.md`](../README.md#45-volume--cmf-obv-mfi-and-price-volume-distribution).
This file does not define a second Feature Registry.

Public consumers import `cmf`, `obv`, `mfi`, and
`price_volume_distribution` through `app.services.indicators`. Calculations are
pure, deterministic, and persistence-free.
