# Functions — Building Block Catalog

> Reference enumeration of the `Functions` building-block snippets (arithmetic, math functions,
> pip conversion, date/time constructors, indicator highest/lowest). This is a lookup table; for
> the general building-block model see [README.md](README.md).

## How this file is organized

Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/Functions/` (18 files).
Every block extends `SQ.Internal.ValueBlock` and implements `OnBlockEvaluate(int relativeShift)`,
returning a numeric value that can be plugged into any other block's value parameter (price levels,
comparisons, formulas, ...). All are annotated `@IgnoreInBuilder`. There are no abstract/internal
base classes in this folder — every file maps to exactly one selectable block.

## Arithmetic

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (+) Plus | `Plus` | `Left + Right`. | `Left`, `Right`. |
| (-) Minus | `Minus` | `Left - Right`. | `Left`, `Right`. |
| (*) Multiplication | `Multiplication` | `Left * Right`. | `Left`, `Right`. |
| (/) Division | `Division` | `Left / Right`; returns `Double.MAX_VALUE` if `Right` evaluates to 0. | `Left`, `Right`. |

## Math functions

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (ABS) Absolute value | `Abs` | Absolute value of `Value`. | `Value`. |
| (SQRT) Sqrt | `SquareRoot` | Square root of `Value`. | `Value`. |
| (EXP) Exponential | `Exponential` | `e^Value`. | `Value`. |
| (LOG) Log | `Logarithm` | Natural logarithm of `Value`. | `Value`. |
| (MAX) Maximum | `Maximum` | Larger of `Value1`, `Value2`. | `Value1`, `Value2`. |
| (MIN) Minimum | `Minimum` | Smaller of `Value1`, `Value2`. | `Value1`, `Value2`. |
| (RND) Round | `Round` | `Value` rounded to `Decimals` decimal places. | `Decimals` — default 5, min 0, max 8, step 1. |

## Pip conversion

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (2PIP) ConvertPriceToPips | `ConvertToPips` | Converts a raw price delta (e.g. 0.002) to pips (e.g. 20), for use in stop-loss/profit-target expressions. | `Symbol` — default "Current". `Value`. |
| (2RPIP) ConvertPipsToPrice | `ConvertToRealPips` | Converts pips (e.g. 20) to a raw price delta (e.g. 0.002); opposite of `ConvertToPips`. | `Symbol` — default "Current". `Value`. |

## Indicator highest / lowest

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (IH) Indicator Highest Value | `IndicatorHighest` | Nth-highest value of `Indicator` over the last `Period` bars. | `Period` — default 5, min 2, max 999. `Nth highest value` (`NthValue`) — default 0, min 0 (0 = highest). |
| (IL) Indicator Lowest Value | `IndicatorLowest` | Nth-lowest value of `Indicator` over the last `Period` bars. | `Period` — default 5, min 2, max 999. `Nth lowest value` (`NthValue`) — default 0, min 0 (0 = lowest). |

## Date / time constructors

Return a `YYYMMDD` or `HHMMNN`-style number comparable against bar time / current time values.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (DATE) GetDate | `GetDate` | Builds a date number from `Day`/`Month`/`Year`. | `Day` — 1-31, default 1. `Month` — 1-12, default 1. `Year` — 1900-2100, default 2016. |
| (TIME) GetTime | `GetTime` | Builds a time number from `Hour`/`Minute`/`Second`. | `Hour` — 0-23, default 0. `Minute` — 0-59, default 0. `Second` — 0-59, default 0. |

## Custom

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (CUST) Custom function | `CustomFunction` | Placeholder for calling a user-defined platform function (MQL command or `/user/extend/Code/{Platform}/CustomFunctions` function); throws `TradingException` if evaluated directly in StrategyQuant. | `Function` — free-text editbox. |

## Related

- Building blocks hub: [README.md](README.md)
- Comparisons (consume these values as `Left`/`Right`/`Indicator` operands): [`comparisons.md`](comparisons.md)
- Strategy control (account/order values these functions often transform): [`strategy-control.md`](strategy-control.md)
- Indicators (the raw series `IndicatorHighest`/`IndicatorLowest` scan over): [`indicators.md`](indicators.md)
