# Cross-library donor verification report: warmup, rounding, shifts, and boundaries

Date: 2026-10-28.

## Scope

This report qualifies the behavioral parity of the canonical Strategy Blocks
package (`app/include/blocks/`) against donor StrategyQuant (SQX) behavior for:
1. Warmup periods and lookback history requirements across indicator families.
2. Output rounding and comparison precision rules.
3. Shift causality and historical indexing.
4. Boundary, extreme, and exceptional inputs (zero range, zero volume, single-bar data).

## 1. Warmup periods and initial lookback

In SQX Java implementations, indicators require an initial warmup window before
producing valid values:

- **Wilder RSI**: $N$ periods warmup; initial $N-1$ bars produce `NaN` without
  raising exceptions or leaking future values.
- **MACD**: Requires `slow + smooth - 1` bars (e.g. $26 + 9 - 1 = 34$ bars) before
  the signal line is valid; the main line is valid after `slow` bars.
- **Bollinger Bands**: Requires $N$ bars (e.g. 20) before moving averages and
  standard deviations become finite.
- **Stochastic**: Requires $K + \text{slowing} + D - 2$ bars (e.g. $14 + 3 + 3 - 2 = 18$
  bars) before slow $D$ becomes finite.
- **ATR**: Requires $N$ bars before true range moving average settles.

Across all families, shorter series return properly aligned `NaN` arrays of
the requested length rather than raising `IndexError` or crashing.

## 2. Output rounding and comparison precision

Donor SQX evaluates indicator comparisons via `.getRounded(shift)`, which rounds
indicator series to 6 decimal places (`1e-6` precision) before evaluating predicates.
Raw market levels (open, high, low, close) are compared unrounded.

- **Canonical parity**: The composition runtime (`composition_runtime.py`) applies
  explicit digit rounding (e.g., 6 digits) on indicator outputs while preserving
  exact floating-point values on raw market reads.
- **Touch vs Strict Cross**: Micro-differences within `1e-6` round to equal levels,
  preventing spurious crosses on floating-point precision noise.

## 3. Shift causality and subset invariance

In SQX, `Shift=0` designates the current evaluation bar, `Shift=1` designates the
preceding completed bar, and `Shift=k` accesses $k$ bars back:

- **Subset invariance**: An evaluation on a $M$-bar slice at `shift=0` is
  strictly identical to an evaluation on a $(M+k)$-bar dataset at `shift=k`.
- **Out of bounds**: Shifts beyond available history return `False` safely for
  condition blocks, eliminating index wrap-around risks.

## 4. Boundary and exceptional conditions

Donor edge-case handling is qualified across all families:

- **Flat price series** ($\text{High} == \text{Low} == \text{Open} == \text{Close}$):
  - ATR returns `0.0`.
  - Bollinger Bands bandwidth is `0.0`, with $\text{Upper} == \text{Lower} == \text{Middle}$.
  - RSI returns neutral `50.0` without `ZeroDivisionError`.
  - Stochastic returns neutral `50.0` without `ZeroDivisionError`.
  - CCI returns `0.0` without `ZeroDivisionError`.
- **Single-bar input**: Single-bar datasets calculate cleanly, producing single-element
  arrays with appropriate initial or `NaN` values.
- **Zero volume**: Indicators such as VWAP, OBV, and VolumeProfile process zero volume
  safely without zero division or NaN contamination.

## 5. Verification status

All cross-library verification tests in `tests/include/blocks/test_donor_cross_library_verification.py`
pass deterministically.
