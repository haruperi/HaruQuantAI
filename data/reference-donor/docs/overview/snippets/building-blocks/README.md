# Building Blocks — Reference Catalog

> Reference enumeration of the "building block" snippets used to compose strategy entry/exit
> rules, price/stop levels, and actions. This is a lookup table; for the strategy-generation
> concepts that consume these blocks see [`../../concepts.md`](../../concepts.md) and
> [`../../builder.md`](../../builder.md).

Parent: [Snippets reference](../README.md) · [Overview index](../../README.md)

Building blocks are the pluggable pieces shown in the strategy tree in the Builder / AlgoWizard
condition and action editors. Each block is a small Java snippet class (`IndicatorBlock`,
`ConditionBlock`, `ValueBlock`, `ActionBlock`, …) annotated with `@BuildingBlock`, which supplies
the human-readable name/template shown in the UI. Blocks are combined into entry/exit rules,
price/stop-loss/profit-target expressions, and strategy actions.

## How the set is assembled

At startup SQX scans the `Blocks/` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/`) and registers every class it
finds there as a building block, keyed by its `@BuildingBlock` annotation. The set is
**extensible** — a user snippet dropped into the same folder structure becomes a new block
available in the UI, exactly like the stock set documented here.

Key annotations on a block class:

- `@BuildingBlock(name="(ABBR) Human name", display="...", returnType=...)` — the display name and
  the template string (with `#Param#` / `@Chart@` placeholders) rendered wherever the block is
  used. Some derived blocks omit `name` and rely on `display` alone.
- `@Help("...")` — one-line description shown as a tooltip (not all blocks have one).
- `@Indicator(oscillator=..., min=..., max=..., step=...)` — chart/scale hints for indicator
  blocks (oscillator vs. price-overlay, default axis range).
- `@Parameter(name=..., defaultValue=..., minValue=..., maxValue=..., step=...)` fields — the
  configurable settings exposed in the block's settings dialog.
- `@ParameterSet(set="Period=14")` — preset parameter combinations offered by the generator.
- `@Output(name=..., color=...)` — named output series an indicator exposes (e.g. `Value`,
  `Signal`).

## Categories

| Category | Count | Purpose | Page |
|----------|------:|---------|------|
| **Indicators** | 400 | Technical indicators (52 families) — base calculation plus derived signal blocks (crosses, rising/falling, level comparisons) | [indicators.md](indicators.md) |
| **Price** | 30 | Raw price/volume series: OHLC, Heiken Ashi, session levels, Ask/Bid, Spread, Volume, D/W/M variants | [price.md](price.md) |
| **BarAndTime** | 37 | Bar/time conditions: day/hour/minute/month checks, current vs. bar time, week-of-month, trading-day flags | [bar-and-time.md](bar-and-time.md) |
| **Comparisons** | 27 | Logical/comparison operators: AND/OR/Not, CrossesAbove/Below, IsGreater/Lower, IndicatorAboveMA, percentile/count variants | [comparisons.md](comparisons.md) |
| **StrategyControl** | 25 | Account/position state: balance, equity, market position, open/closed P/L, order SL/PT, bars since, pending orders | [strategy-control.md](strategy-control.md) |
| **Functions** | 18 | Math/utility functions: Abs, arithmetic, Min/Max, Round, pip conversion, indicator highest/lowest | [functions.md](functions.md) |
| **Order** | 12 | Trade actions: EnterAtMarket/Stop/Limit, Close*, SetStopLoss/ProfitTarget | [order-actions.md](order-actions.md) |
| **OtherActions** | 8 | Misc actions: AssignVariable, Custom code, Draw, Log, SendEmail | [order-actions.md](order-actions.md) |
| **CandlePatterns** | 7 | Candlestick pattern recognizers: engulfing, doji, hammer, etc. | [candle-patterns.md](candle-patterns.md) |
| **Other** | 5 | Variable/constant blocks: Boolean, BooleanVariable, DoubleVariable, IntVariable, Number | [variables.md](variables.md) |

569 block classes in total.

## Related

- Strategy-generation concepts: [`../../concepts.md`](../../concepts.md)
- Builder (what generates strategies out of these blocks): [`../../builder.md`](../../builder.md)
- Stats metrics reference (Databank columns, a separate snippet type): [`../../stats-metrics.md`](../../stats-metrics.md)
- Trade Analysis charts reference: [`../../results-tabs/trade-analysis-charts.md`](../../results-tabs/trade-analysis-charts.md)
