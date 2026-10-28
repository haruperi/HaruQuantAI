# Phase 3: complete indicator-family migration

All indicator implementations now live under `app/include/blocks/indicators/`.
There are no legacy indicator implementations, import shims, facade classes, or
separate parameter classes. The former `app/include/indicators/` Python sources
have been removed, and their runtime consumers and tests use canonical imports.

## Inventory reconciliation

| Family | Canonical indicators |
| --- | ---: |
| Trend | 19 |
| Momentum | 18 |
| Volatility | 15 |
| Volume | 11 |
| Price action | 10 |
| Regime | 3 |
| **Total** | **76** |

The original inventory contained 73 implementation classes. Decomposing the
compound MovingAverage into five indicators adds four classes; consolidating
its duplicate TEMA implementation removes one. The result is 76 distinct
indicators, each in its own file, with a unique stable ID.

The previous migration batch covered eight indicators. This batch migrates all
68 remaining classes. MFI is separated from OBV, and CumulativeVolumeDelta and
AggressiveTradeImbalance each receive independent files and IDs. The original
Phase 0 manifest is retained as historical evidence; the final catalog is in
[phase3-canonical-indicator-manifest.json](fixtures/phase3-canonical-indicator-manifest.json).

The custom package remains an extension destination; the original custom package
contained no user-defined indicator implementations to migrate.

## Shared calculation ownership

Shared moving-average and RSI batch functions now live in the existing
`app/include/calculators/average.py` and `app/include/calculators/rsi.py` modules,
alongside the donor-style streaming calculators. Array conversion belongs to
`calculators/base.py`. The separate numerical package has been removed without
import shims. MACD and Bollinger-specific array composition is private to their
indicator files. All indicator and template imports use these canonical owners.

This is a structural migration: batch formulas, array execution, numerical
signatures, and existing streaming behavior are preserved. Batch/stream seeding
and warmup differences remain explicit; no incremental capability is enabled by
moving these functions.

## Uniform calculation and configuration

Every indicator derives from the canonical BaseIndicator. Parameters are typed
Pydantic fields directly on that class. Configuration is frozen, rejects unknown
fields, validates defaults and domain bounds, rejects non-finite parameters,
and uses strict types. Configuration relationships are checked before execution.

`calculate(bars: BarData)` returns aligned, named IndicatorSeries outputs. The
original formulas and initialization values are preserved. Consumers must respect
the parameter-dependent `required_history()` before using initialized outputs in
rules; existing zero-filled initialization regions remain numerical parity data.
None of these indicators advertises incremental execution.

```python
from app.include.blocks.indicators.volatility.atr import ATR
from app.include.blocks.series import BarData

bars = BarData.from_arrays(high=high, low=low, close=close)
indicator = ATR(period=14)
atr = indicator.calculate(bars)["value"]
history_needed = indicator.required_history()
```

BarData now supports aligned, read-only auxiliary feeds for positioning and
order-flow indicators. Missing feeds are not replaced with unrelated prices.
Optional feeds retain their absent-input behavior, including VWAP without opens
and HighestLowest without a separate low series. Paired buy/sell volumes must be
supplied together. `from_arrays` records which inputs were actually supplied;
unused OHLCV storage slots cannot satisfy a missing-input requirement.

Fibo always declares its optional `custom` output. When no custom level is set,
that output contains NaNs, while all existing standard-level outputs retain
their original values. This explicit output normalization is recorded separately
from the original baseline hashes.

COT and VolumeProfile calculations and domain-specific signal helpers are
colocated in their respective canonical indicator files. Generic COT comparison
wrappers have been replaced by direct shared-comparison calls. There is no
separate indicator-signals package or indicator-specific numerical sidecar.
COT is 997 lines and VolumeProfile is 870 lines, both within the 1,000-line limit.
The former oversized-COT architecture exception is unnecessary.


## Causality and data availability

- ZigZag revises historical pivots and interpolated legs. It remains available
  for chart analysis with `is_causal=False` and generation disabled.
- Ichimoku's backward-shifted Chikou output also changes historical timestamps
  when future data arrives. The complete chart block is marked non-causal and
  excluded from generation. Its causal lines can be separated in a future
  design without misrepresenting the current complete block.
- COT requires actual commercial/speculator positioning feeds. It calculates
  through an explicitly supplied context; OHLCV-only editor history fails with
  a missing-input diagnostic. Automatic generation is disabled for this block
  until the generator has the required external-data capability.

All other migrated blocks pass exact prefix comparisons at 17, 75, 223,
and 319 bars, depending on the existing and family qualification suites.

## Consumer and editor updates

All runtime consumers use canonical indicator classes or shared numerical
helpers. The editor resolver searches the canonical tree exclusively, and its
runner instantiates configuration and calls the common batch contract once.
Generated indicators use the same contract, including a stable ID, validated
period, named outputs, and the selected category. Frontend creation, export,
navigator badges, and browser-test paths use the canonical root.

Package exports are lazy, with a fresh-process regression proving that a broken
exported sibling does not poison unrelated indicator imports. File discovery
publishes the module before resolving postponed type annotations and reads
current source on reload, avoiding stale same-size bytecode cache hits.

## Evidence and verification

- [phase3-family-inputs.npz](fixtures/phase3-family-inputs.npz): deterministic
  320-bar OHLCV and auxiliary inputs, captured before changing the implementations.
- [phase3-family-baselines.json](fixtures/phase3-family-baselines.json): full
  SHA-256 output hashes, default and alternate configurations, initialization
  signatures, and measured prefix-causality classifications for all 68 classes.
  Hashing preserves float64 bytes and normalizes only NaN payloads. The
  `baseline_ms` values measure the original capture operation, including full
  and prefix calculations and signature work; they are not new latency budgets.
- [phase3-canonical-indicator-manifest.json](fixtures/phase3-canonical-indicator-manifest.json):
  final IDs, paths, inputs, output ports, schemas, histories, and capabilities.
- `tests/include/blocks/test_indicator_families.py`: per-class numerical parity,
  multiple prefix boundaries, schema isolation, strict configuration, editor
  execution, auxiliary-feed failures, stable custom outputs, full discovery,
  fresh-process import isolation, and typed same-size source reloads.
- The existing Phase 0 performance and parity gates remain in place at the
  original budgets, including the large-dataset and multi-output cases.

Verification completed on 2026-10-28:

- Python full-suite run: **1,011 passed** in 130.29 seconds.
- Focused family qualification: **149 passed**.
- Mypy: **154 source files**, no issues.
- Frontend: **13 unit tests** and **12 browser regressions** passed; TypeScript
  checking passed.
- Indicator/editor source and test Ruff lint/format checks passed.
- Architecture checks and Git whitespace checks passed.

The consolidation-specific source files pass Ruff lint and formatting. A later
repository-wide check encountered unrelated bar-time files being edited
concurrently; those changes are outside this consolidation.

This completes Phase 3. Phase 4 covers the remaining non-indicator strategy
blocks; the broader schema-driven editor and packaging work remains in Phase 5.
