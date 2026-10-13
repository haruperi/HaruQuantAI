# Portfolio Master fitness functions — full catalog

> Reference enumeration of the built-in **fitness functions** Portfolio Master can optimize for
> when searching for the best combination of strategies into a portfolio.

## How the set is assembled

Each fitness function is a snippet class extending
`com.strategyquant.tradinglib.portfolioMaster.PortfolioMasterFitness`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/PortfolioMasterFitness/`). Its
constructor calls `super(name, valueType, target, avgMin, avgMax)`:

- `name` — display name shown in the fitness-function picker.
- `valueType` — optimization goal (`ValueTypes.Maximize` or `ValueTypes.Minimize`).
- `target` — target value used when the function is combined as an "Approximate"-style goal (all
  three built-ins currently pass `0`).
- `avgMin` / `avgMax` — the expected value range used to normalize/scale the fitness for
  cross-strategy comparison and UI display.

Each function implements `compute(ResultsGroup result, byte sampleType)`, which pulls a single
stat out of the portfolio's combined `Both`-direction, `Money`-P/L-type stats
(`result.portfolio().stats(Directions.Both, PlTypes.Money, sampleType)`) via a `StatsKey`, and
`print(double value)` to format it for display.

## The 3 fitness functions

| Display name | Class | Goal | Target | Avg range | `StatsKey` used | Description |
|---|---|---|---|---|---|---|
| Net Profit (Return) | `NetProfit` | Maximize | 0 | −10000 … 10000 | `NET_PROFIT` | Portfolio's total net profit (money). Formatted via `PlTypes.printPL(value, PlTypes.Money)`. |
| % Stagnation | `PctStagnation` | Minimize | 0 | 0 … 100 | `STAGNATION_PERIOD_PCT` | Portfolio's stagnation period as a percentage of total time. Formatted via `PlTypes.printPL(value, PlTypes.Percent)`. |
| Return / Drawdown ratio | `ReturnDD` | Maximize | 0 | −20 … 20 | `RETURN_DD_RATIO` | Portfolio's return-to-drawdown ratio. |

## Related

- Portfolio Master overview: [`../portfolio-master.md`](../portfolio-master.md)
- Correlation series used alongside fitness during selection: [`correlation-of.md`](correlation-of.md)
- Stats metrics reference (same `StatsKey` universe): [`../stats-metrics.md`](../stats-metrics.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/PortfolioMasterFitness/`
