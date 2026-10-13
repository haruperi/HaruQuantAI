# Checker & Calculator snippets — full catalog

> Reference enumeration of the built-in **Checker** (Builder-time block-combination validators)
> and **Calculator** (runtime rolling-window math helpers) snippet classes.

## How the set is assembled

**Checkers** are snippet classes extending `com.strategyquant.tradinglib.Checker`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Checker/`). Each implements
`check(Element elBlock)`, inspecting a candidate block's **XML representation** (its own
parameters and, for `ComparisonChecker`, its children) before the Builder accepts it into a
generated strategy. Returning `false` rejects the combination and the Builder discards/regenerates
it. Checkers carry no `@Parameter`/`@ClassConfig` annotations — they are plain rule classes, always
active, with no user-configurable settings.

**Calculators** are plain (non-block) helper classes extending `SQ.Calculators.AbstractCalculator`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Calculators/`) that indicator/formula
code instantiates directly to maintain a rolling buffer over a `Period` and compute an incremental
statistic bar-by-bar via `onBarUpdate(newValue, currentBar)`. They are not building blocks and
carry no `@Parameter` annotations — their "settings" are plain constructor arguments.

## Checkers

| Class | Applies to | What it rejects |
|---|---|---|
| `ComparisonChecker` | Boolean comparison blocks (`<`, `>`, `<=`, `>=`, `=`, `<>`, crosses, and `Not`) with `#Left#`/`#Right#` operands | Left and Right being textually identical; comparing two different number-returning indicators (unless the same indicator); comparing a number-indicator against a non-`Number` block; mixing bar-time blocks (`Hour`/`Minute`/`DayOfWeek`) with anything but a `Number` in a sane range (0–23 / 0–59 / 0–6), or using a "crosses" comparison with a bar-time block; invalid `HH:MM`-style time values inside `HighestInRange`/`LowestInRange`. |
| `IndicatorFastSlowChecker` | Any block (and nested `Item` blocks) with an `int` `#Fast#`/`#Slow#` or `#MinPeriod#`/`#MaxPeriod#` parameter pair | Fast period ≥ Slow period, or Min period ≥ Max period (non-numeric/variable values are allowed through). |
| `PropertyChecker` | `IsRising` / `IsFalling` boolean property blocks | The wrapped `Indicator` parameter not exposing a `#Shift#` field, or the indicator being an `Hour`/`Minute`/`DayOfWeek` block. |

## Calculators

Constructor-configured rolling calculators; `Period` is the only shared "parameter" (all
constructors validate `Period > 0`, defaulting to `2` otherwise with a debug log).

| Class | Constructor | What it computes |
|---|---|---|
| `AbstractCalculator` | `AbstractCalculator(int Period)` | Base class: maintains a circular buffer of the last `Period` values via `onBarUpdate()`, handling same-bar updates vs. new-bar shifts. Subclasses implement `calculate(newValue, isSameBar)`. |
| `AverageCalculator` | `AverageCalculator(int Type, int Period)` or `(int Type, int Period, int AveragePrecision)` | Moving average over the buffer; `Type` selects `SMA` (0), `EMA` (1), `SMMA` (2), or `LWMA` (3). Optional `AveragePrecision` (0–100) periodically re-syncs the SMA sum from the raw buffer to bound floating-point drift. |
| `HighestCalculator` | `HighestCalculator(int Period)` | Highest value in the trailing `Period`-bar window; exposes `getHighestValue()` / `getHighestIndex()`. |
| `LowestCalculator` | `LowestCalculator(int Period)` | Lowest value in the trailing `Period`-bar window; exposes `getLowestValue()` / `getLowestIndex()`. |
| `RSICalculator` | `RSICalculator(int Period)` | Wilder-style RSI: tracks smoothed average up-move / down-move via two internal `AverageCalculator`s (SMA warm-up, then Wilder smoothing), returns `getValue()` in 0–100. |
| `StdDevCalculator` | `StdDevCalculator(int Period)` | Rolling population standard deviation over the trailing `Period`-bar window. |
| `SumCalculator` | `SumCalculator(int Period)` | Rolling sum over the trailing `Period`-bar window (adds new value, subtracts the value falling out of the window). |

## Related

- Stats metrics reference: [`../stats-metrics.md`](../stats-metrics.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Checker/`, `.../SQ/Calculators/`
