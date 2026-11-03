# Correlation-of series — full catalog

> Reference enumeration of the built-in **series types** that strategy/portfolio correlation
> computations (Strategy Correlation tab, Portfolio Composer, Portfolio Master) can be run on.

## How the set is assembled

Each series is a snippet class extending `com.strategyquant.tradinglib.CorrelationType`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/CorrelationOf/`). Its constructor sets
a display `name` and a `dataType` — `DATA_TYPE_TRADES` (a trade/position count) or `DATA_TYPE_PL`
(a money value) — and it implements `computePeriods(OrdersList orders, int period, TimePeriods
periods)`, which buckets each closed order's contribution into fixed time periods
(`CorrelationLib.getCorrectPeriod`). `CorrelationLib` then correlates two strategies' per-period
series against each other. Series have no `@Parameter`-style user settings; the user picks one
from a dropdown as the basis for the correlation calculation.

## The 6 correlation series

| Display name | Class | Data type | What it accumulates per period |
|---|---|---|---|
| Loss | `Loss` | P/L | Sum of `order.PL` across all non-canceled trades closing in the period (despite the name, sums signed P/L like Profit/Loss). `shouldSkipPeriod()` skips periods where **both** compared strategies had no loss (both values ≥ 0). |
| Number of closed positions | `NumberOfClosedPositions` | Trades | Net position count closing in the period: `+1` per closed long, `-1` per closed short. |
| Number of closed trades | `NumberOfClosedTrades` | Trades | Count of all non-canceled trades closing in the period (long and short both `+1`). |
| Number of open positions | `NumberOfOpenPositions` | Trades | For every period, net count of positions that overlap it (`period.from < order.CloseTime && period.to >= order.OpenTime`): `+1` per overlapping long, `-1` per overlapping short. |
| Number of open trades | `NumberOfOpenTrades` | Trades | Same overlap test as above, but counts every overlapping trade as `+1` regardless of direction. |
| Profit/Loss | `ProfitLoss` | P/L | Sum of `order.PL` across all non-canceled trades closing in the period. |

## Related

- Strategy Correlation tab: [`../results-tabs/strategy-correlation.md`](../results-tabs/strategy-correlation.md)
- Portfolio Composer: [`../portfolio-composer.md`](../portfolio-composer.md)
- Portfolio Master fitness functions: [`portfolio-master-fitness.md`](portfolio-master-fitness.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/CorrelationOf/`
