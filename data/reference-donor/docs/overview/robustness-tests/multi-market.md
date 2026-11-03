# Multi-Market test (additional markets) — robustness test

> Tests the same strategy on other instruments and/or timeframes to see if the edge is real or fitted to one market.

## What it does

Multi-market testing runs the strategy on **additional markets** — different symbols and/or
timeframes — beyond the one it was built on. StrategyQuant X lets you select multiple instruments
(stocks, currency pairs, commodities, indices, ...) and backtests the strategy on each, so you can
compare performance across markets and identify strategies that behave consistently.

## What weakness it exposes

**Curve-fitting to a single instrument.** A strategy that only works on one symbol/timeframe has
likely been over-adapted to that market's specific characteristics. A concept that holds up across
several markets is far more likely to reflect a genuine, transferable edge rather than chance or
over-fitting.

## How to configure it

- Select one or more **additional markets** (symbols and/or timeframes) to retest on.
- Each selected market is backtested with the same strategy settings.
- As a cross-check it can **filter** in the Builder (drop strategies unprofitable on other markets)
  or **annotate** results in the Retester.

## How to read the result

- Because every market has its own volatility and characteristics, do not expect identical, perfect
  performance everywhere. A strategy that stays at least mildly profitable — or only slightly losing
  — on the extra markets can be considered acceptable.
- Consistent performance across markets is a strong robustness signal and also supports building a
  diversified portfolio. Good performance on one market but clearly bad performance on another (e.g.
  fine on EURUSD but poor on GBPUSD) indicates the strategy is probably not robust enough.

## Related

- Sibling: [In-Sample / Out-of-Sample](in-sample-out-of-sample.md) · [Walk-Forward](walk-forward.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
