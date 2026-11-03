# Comparisons — Building Block Catalog

> Reference enumeration of the `Comparisons` building-block snippets (logical operators,
> value comparisons, crosses, and count/percentile variants). This is a lookup table; for the
> general building-block model see [README.md](README.md).

## How this file is organized

Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/Comparisons/` (27 files).
Every concrete class here extends `SQ.Internal.ComparisonBlock` and implements
`OnEvaluateComparison()`, returning a boolean used in entry/exit condition trees. Blocks are
grouped below by what they compare. A handful of classes end in `Abstract` — they hold shared
`@Parameter` fields and helper methods for their concrete siblings and carry no `@BuildingBlock`
annotation themselves, so they never appear in the UI; they're listed once at the bottom.

## Logical operators

| Display name | Class | Description | Parameters |
|---|---|---|---|
| AND | `AND` | True only if every child condition in `Children[]` evaluates true (no `@BuildingBlock` annotation found in source — name derived from the class). | `Children` — array of child condition blocks. |
| OR | `OR` | True if any child condition in `Children[]` evaluates true (no `@BuildingBlock` annotation found in source — name derived from the class). | `Children` — array of child condition blocks. |
| Not | `Not` | Inverts a single condition (`Not #Value#`). | `Value` — condition block to invert. |

## Equality and magnitude comparisons

Two-operand comparisons; all extend `LeftRightComparisonBlockAbstract` (`Left`, `Right` value blocks,
compared after rounding to 6 decimal places).

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (=) Equals | `Equals` | True if `Left` equals `Right`. | `Left`, `Right`. |
| (<>) Not equals | `NotEquals` | True if `Left` differs from `Right`. | `Left`, `Right`. |
| (>) Is greater | `IsGreater` | True if `Left` > `Right`. | `Left`, `Right`. |
| (<) Is lower | `IsLower` | True if `Left` < `Right`. | `Left`, `Right`. |
| (>=) Is greater or equal | `IsGreaterOrEqual` | True if `Left` >= `Right`. | `Left`, `Right`. |
| (<=) Is lower or equal | `IsLowerOrEqual` | True if `Left` <= `Right`. | `Left`, `Right`. |

## Crosses

Also extend `LeftRightComparisonBlockAbstract`; compare the current bar against the previous bar
(shift 0 vs. shift 1) to detect a crossover.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Crosses Above | `CrossesAbove` | True on the bar where `Left` moves from below to above `Right`. | `Left`, `Right`. |
| Crosses Below | `CrossesBelow` | True on the bar where `Left` moves from above to below `Right`. | `Left`, `Right`. |

## Rising / falling

Extend `IsOneComparisonBlockAbstract` (`Indicator`, `Shift`); check a single indicator's own trend
over a lookback window.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Is rising | `IsRising` | True if `Indicator` has been rising over the last `Bars` bars (at least once). | `Bars` — bars to check, default 2, min 2, max 100 (builder max 50). `NotStrict` — bool, default false; if true, equal consecutive values are allowed. |
| Is falling | `IsFalling` | True if `Indicator` has been falling over the last `Bars` bars (at least once). | Same as `IsRising`. |

## Indicator vs. Moving Average

Extend `IndicatorMAComparisonBlockAbstract`, which computes an on-the-fly MA (Simple/Exponential/
Weighted/Hull) of the indicator's own values.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (I > MA) Indicator Above MA | `IndicatorAboveMA` | True if `Indicator` is above its own `Period`-bar moving average. | `Period` — default 14, min 2, max 250. `MA Type` — Simple=1, Exponential=2, Weighted=3, Hull=4, default 1. `Shift`. |
| (I < MA) Indicator Below MA | `IndicatorBelowMA` | True if `Indicator` is below its own moving average. | Same as above. |
| (I ↗ MA) Indicator Crosses Above MA | `IndicatorCrossesAboveMA` | True on the bar `Indicator` crosses above its moving average. | Same as above. |
| (I ↘ MA) Indicator Crosses Below MA | `IndicatorCrossesBelowMA` | True on the bar `Indicator` crosses below its moving average. | Same as above. |

## Count-based ("X out of N bars")

Extend `CountComparisonBlockAbstract` (`IndicatorLeft`, `IndicatorRight`, `Bars`, `NotStrict`,
`Shift`); true only if the comparison held for every one of the last `Bars` bars.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (> X) Is greater for X bars | `IsGreaterCount` | True if `IndicatorLeft` > `IndicatorRight` on every one of the last `Bars` bars. | `Bars` — default 2, min 2, max 500 (builder max 10). `NotStrict` — bool, default false. `Shift`. |
| (< X) Is lower for X bars | `IsLowerCount` | True if `IndicatorLeft` < `IndicatorRight` on every one of the last `Bars` bars. | Same as above. |

## Percentile / percent-rank

Extend `IsOneComparisonBlockAbstractPercentil` (`Indicator`, `Bars`, `Shift`, `Percentile`);
compute what percentage of the last `Bars` values the current value beats.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (> % Rank) Is Greater or Equal Percent Rank | `IsGreaterPercentil` | True if `Indicator`'s current value ranks above `Percentile`% of its values over the last `Bars` bars. | `Bars` — default 10, min 2, max 1000. `Percentile` — default 50, min 0.1, max 99.9, step 0.1. `Shift`. |
| (< % Rank) Is Lower or Equal Percent Rank | `IsLowerPercentil` | True if `Indicator`'s current value ranks below `Percentile`% of its values over the last `Bars` bars. | Same as above. |

## Internal / abstract base classes (not user-facing)

Not annotated with `@BuildingBlock`, so they never appear as a selectable block; they only supply
shared parameters/helpers to the concrete classes above.

| Class | Supplies | Used by |
|---|---|---|
| `LeftRightComparisonBlockAbstract` | `Left`, `Right` | Equals, NotEquals, IsGreater, IsLower, IsGreaterOrEqual, IsLowerOrEqual, CrossesAbove, CrossesBelow |
| `IndicatorMAComparisonBlockAbstract` | `Indicator`, `Period`, `MAType`, `Shift`, MA calculation helpers | IndicatorAboveMA, IndicatorBelowMA, IndicatorCrossesAboveMA, IndicatorCrossesBelowMA |
| `CountComparisonBlockAbstract` | `Bars`, `NotStrict`, `Shift`, `IndicatorLeft`, `IndicatorRight` | IsGreaterCount, IsLowerCount |
| `IsOneComparisonBlockAbstract` | `Indicator`, `Shift` | IsRising, IsFalling |
| `IsOneComparisonBlockAbstractPercentil` | `Indicator`, `Bars`, `Shift`, `Percentile` | IsGreaterPercentil, IsLowerPercentil |
| `CountComparisonBlockAbstractPercentile` | `Bars`, `Shift`, `IndicatorLeft`, `IndicatorRight` | No concrete subclass found in this folder — appears unused/orphaned. |

## Related

- Building blocks hub: [README.md](README.md)
- Indicators (the values most comparisons wrap — crosses, MA comparisons, rising/falling all operate on indicator/price series): [`indicators.md`](indicators.md)
- Functions (arithmetic used to build the `Left`/`Right`/`Value` operands): [`functions.md`](functions.md)
- Strategy control (position/order-state blocks often compared against these): [`strategy-control.md`](strategy-control.md)
