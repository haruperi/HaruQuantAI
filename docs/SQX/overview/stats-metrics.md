# Stats metrics — full catalog (Databank columns)

> Reference enumeration of the built-in performance metrics SQX computes for every strategy result.
> This is a lookup table; read it only when you need the exact set. For where these values surface
> in the UI see the [Overview tab](results-tabs/overview.md) and
> [Results & Databank overview](results-databank.md).

## How the set is assembled

Each metric is a snippet class extending `DatabankColumn`, registered via
`StatsComputer.registerDatabankColumn()` and loaded from the `Columns/Databanks` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Columns/Databanks/`). The set is
**extensible** — a user snippet dropped in becomes a new databank column / stats value.

A column's constructor declares its display name, display format (money, %, pips, integer, text…),
and its **optimization goal** — whether a higher value is better (`Maximize`), a lower value is
better (`Minimize`), a target is aimed for (`Approximate`), or the column is descriptive text (—).
`StatsComputer` resolves dependencies between columns (via `setDependencies`) and computes them per
result, direction (Long/Short/Both), sample (IS/OOS/full), and P/L type. Some columns restrict
themselves to one P/L type or direction (e.g. Sharpe Ratio only for Money + Both).

The stock set shipped with SQX is below, grouped by theme. "Goal" is the optimization direction.

## Profit & return

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| Net profit | `NetProfit` | Max | Sum of P/L of all trades (excludes balance/deposit orders). |
| Net profit in % | `NetProfitInPct` | Max | Net profit as a percentage of the initial deposit. |
| Net profit in pips | `NetProfitInPips` | Max | Net profit expressed in pips. |
| Gross profit | `GrossProfit` | Max | Sum of all winning trades. |
| Gross loss | `GrossLoss` | Min | Sum of all losing trades. |
| Annual % Return | `AnnualPctReturn` | Max | Annual percentage return. |
| CAGR | `CAGR` | Max | Compound Annual Growth Rate. |
| AHPR | `AHPR` | Min | Arithmetic Holding Period Return. |
| Avg. Profit Per Day | `AvgProfitPerDay` | Max | Average profit per trading day. |
| Avg. Profit Per Month | `AvgProfitPerMonth` | Max | Average profit per trading month. |
| Avg. Profit Per Year | `AvgProfitPerYear` | Max | Average profit per trading year. |
| Avg. % Profit Per Year | `AvgPctProfitPerYear` | Max | Average percentage profit per year. |
| Worst Year Profit | `WorstYearProfit` | Min | Profit of the worst calendar year. |
| Max Profit | `MaxProfit` | Max | Largest single winning trade. |
| Max Loss | `MaxLoss` | Min | Largest single losing trade. |

## Drawdown & risk

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| Drawdown | `Drawdown` | Min | Max drawdown in money. |
| Max DD % | `DrawdownPct` | Min | Max drawdown in %. |
| Max DD pips | `DrawdownPips` | Min | Max drawdown in pips. |
| Avg. Drawdown | `AvgDrawdown` | Min | Average drawdown in money. |
| Avg. % Drawdown | `AvgPctDrawdown` | Min | Average drawdown in %. |
| Max Drawdown Duration | `MaxNewHighDuration` | Min | Longest time spent in drawdown (days). |
| Max Intraday Drawdown | `MaxIntradayDrawdown` | Min | Max drawdown measured intraday. |
| Max TS Intraday Drawdown | `MaxTSIntradayDrawdown` | Max | Max intraday drawdown, TradeStation-style. |
| Open Drawdown | `OpenDrawdown` | Min | Drawdown from open balance + MAE. |
| Open Drawdown % | `OpenDrawdownPct` | Min | Max % drawdown computed from MAE. |
| Actual Drawdown | `ActualDD` | Min | Current/actual drawdown. |
| Actual Drawdown / Max DD | `ActualDrawdownPct` | Min | Actual drawdown relative to max drawdown. |
| Ulcer Index % | `UlcerIndex` | Min | Depth and duration of drawdowns (Ulcer Index). |
| StandardDev | `StandardDev` | Min | Standard deviation of trades. |

## Ratios & quality scores

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| Profit factor | `ProfitFactor` | Max | Ratio of gross profit to gross loss. |
| Ret/DD Ratio | `ReturnDDRatio` | Max | Return / drawdown ratio. |
| Ret/OpenDD Ratio | `ReturnOpenDDRatio` | Max | Return / open-drawdown ratio. |
| CAGR/Max DD % | `AnnualPctReturnDDRatio` | Max | CAGR vs. drawdown ratio. |
| Sharpe Ratio | `SharpeRatio` | Max | Annualized Sharpe ratio. |
| CalmarRatio | `CalmarRatio` | Max | CAGR / max drawdown (Calmar). |
| SQN | `SQN` | Max | Strategy Quality Number. |
| SQN Score | `SQNScore` | Max | Normalized SQN score. |
| RecoveryFactor | `RecoveryFactor` | Max | Net profit / max drawdown. |
| Payout ratio | `PayoutRatio` | Max | Average win / average loss. |
| Win/Loss ratio | `WinLossRatio` | Max | Ratio of winning to losing trades. |
| TS Win/Loss ratio | `TSWinLossRatio` | Max | Win/loss ratio, TradeStation-style. |
| Expectancy | `Expectancy` | Max | Expected P/L per trade. |
| R Expectancy | `RExpectancy` | Max | Expectancy expressed in R (risk units). |
| R Expectancy Score | `RExpectancyScore` | Max | Normalized R-expectancy score. |
| Kelly formula | `KellyFormula` | Max | Kelly-criterion optimal position fraction. |
| Ulcer Performance Index | `UlcerPerformanceIndex` | Max | Annualized return over Ulcer Index. |
| TS Index | `TSIndex` | Max | TradeStation index. |
| Fitness | `Fitness` | Max | Fitness rank used by the ranking engine. |
| Exit quality | `ExitQuality` | Max | Total profit / total MFE. |
| Efficiency | `Efficiency` | — | How efficiently trades capture available move. |
| Edge Ratio | `EdgeRatioInPips` | Max | Edge ratio (MFE vs. MAE) in pips. |

## Trade statistics

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| # of trades | `NumberOfTrades` | Approx | Number of trades. |
| # of profits | `NumberOfProfits` | Max | Number of winning trades. |
| # of losses | `NumberOfLosses` | Min | Number of losing trades. |
| # of canceled | `NumberOfCanceled` | Approx | Number of canceled trades. |
| Winning Percent | `WinningPct` | Max | Percentage of winning trades. |
| Avg. Trade | `AvgTrade` | Max | Average P/L per trade. |
| Avg. Abs Trade | `AvgAbsTrade` | Max | Average absolute trade (including losers). |
| Avg. Win | `AvgWin` | Max | Average winning trade. |
| Avg. Loss | `AvgLoss` | Min | Average losing trade. |
| Max Consec. Wins | `MaxConsecWins` | Max | Maximum consecutive wins. |
| Max Consec. Losses | `MaxConsecLosses` | Min | Maximum consecutive losses. |
| Avg Consec. Wins | `AvgConsecWins` | Max | Average consecutive wins. |
| Avg Consec. Losses | `AvgConsecLosses` | Min | Average consecutive losses. |
| Avg. Trades Per Day | `AvgTradesPerDay` | Min | Average number of trades per day. |
| Avg. Trades Per Month | `AvgTradesPerMonth` | Min | Average number of trades per month. |
| Avg. Trades Per Year | `AvgTradesPerYear` | Min | Average number of trades per year. |
| Longest trade (days) | `LongestTrade` | Min | Duration of the longest trade in days. |
| Avg. Bars in Trade | `AvgBarsInTrade` | Min | Average bars a trade stays open. |
| Avg. Bars Win | `AvgBarsWin` | Max | Average bars in winning trades. |
| Avg. Bars Loss | `AvgBarsLoss` | Min | Average bars in losing trades. |
| Ambiguous Trades | `AmbiguousTrades` | Min | Trades that open and close on the same bar. |
| Ambiguous Trades % | `AmbiguousTradesPct` | Min | Percentage of ambiguous trades. |
| Biggest MAE | `BiggestMAE` | Max | Worst Maximum Adverse Excursion of all trades. |
| Total MFE | `TotalMFE` | Min | Sum of Maximum Favorable Excursion of all trades. |
| Exposure | `Exposure` | Min | Bars in positions / total bars in sample. |
| Exposure Position | `ExposurePosition` | Min | Exposure variant for the Stockpicker engine. |

## Consistency & robustness

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| Stability | `Stability` | Max | How straight and steep the equity curve is. |
| Stability SQ3 | `StabilitySQ3` | Max | Stability, SQ3 formula. |
| RSquared | `RSquared` | Max | How straight the equity curve is (R²). |
| EquityAngle | `EquityAngle` | Max | Angle of the equity curve. |
| EquitySlope | `EquitySlope` | Max | Straightness × angle of the equity curve. |
| Symmetry | `Symmetry` | Max | How symmetrical profit is between long and short. |
| NSymmetry | `NSymmetry` | Max | Symmetry that penalizes one side being in loss (−1). |
| Trades Symmetry | `TradesSymmetry` | Max | How symmetrical trade count is between long and short. |
| Profitable Months | `ProfitableMonths` | Max | Number of profitable months. |
| % Profitable Months | `ProfitableMonthsPct` | Max | Percentage of profitable months. |
| Stagnation | `Stagnation` | Min | Longest stagnation period in days. |
| % Stagnation | `StagnationPct` | Min | Stagnation as % of total days. |
| ZScore | `ZScore` | Max | Z-score of the trade sequence. |
| ZProbability | `ZProbability` | Max | Probability associated with the Z-score. |
| Avg. Parameters Stability | `AvgParametersStability` | Max | Average parameter stability across WF results. |
| Worst Parameters Stability | `WorstParametersStability` | Max | Worst parameter stability across WF results. |
| Best WF | `BestWF` | Max | Best walk-forward result marker. |
| Degrees of freedom | `DegreesOfFreedom` | Min | Degrees of freedom of the strategy. |
| Complexity | `Complexity` | Min | Structural complexity of the strategy. |

## Time, data & cost

| Metric | Class | Goal | Description |
|--------|-------|------|-------------|
| Total Trading Days | `TotalTradingDays` | Min | Days with at least one trade. |
| Total Trading Months | `TotalTradingMonths` | Min | Months with trading activity. |
| Total Trading Years | `TotalTradingYears` | Min | Years with trading activity. |
| Total Data Days | `TotalDataDays` | Min | Days of data covered by the backtest. |
| Total Data Months | `TotalDataMonths` | Min | Months of data covered. |
| Total Data Years | `TotalDataYears` | Min | Years of data covered. |
| Backtest Duration (s) | `BacktestDuration` | Min | Backtest computation time in seconds. |
| Initial deposit | `InitialDeposit` | Max | Starting account balance. |
| Commission/Swap ($) | `Commission` | Min | Total commission and swap costs. |
| Slippage ($) | `SlippageInMoney` | Max | Total modeled slippage in money. |

## Descriptive / meta columns

Text or informational columns (no optimization goal).

| Metric | Class | Description |
|--------|-------|-------------|
| Symbol | `Symbol` | Symbol the test was made on. |
| TimeFrame | `TimeFrame` | Timeframe the test was made on. |
| Magic number | `MagicNumber` | Strategy magic number / identifier. |
| Results Name | `ResultsName` | Name of the result. |
| Note | `Note` | Free-text note. |
| Date generated | `DateGenerated` | When the strategy was generated. |
| Date last modified | `DateLastModified` | When the result was last modified. |
| Parameters | `Parameters` | Strategy parameters. |
| Entry indicators | `EntryIndicators` | Indicators used in entry conditions. |
| Exit indicators | `ExitIndicators` | Indicators used in exit conditions. |
| Price indicators | `PriceIndicators` | Indicators used in entry price levels (stop/limit). |
| Filters result | `FiltersResult` | Outcome of the databank filters. |
| Mini equity chart | `MiniEquityChart` | Thumbnail equity curve rendered in the column. |
| Outlier | `Outlier2` | Outlier-trade detection marker. |

## Related

- Overview tab (where these surface): [`results-tabs/overview.md`](results-tabs/overview.md)
- Results & Databank overview: [`results-databank.md`](results-databank.md)
- Trade Analysis charts reference: [`results-tabs/trade-analysis-charts.md`](results-tabs/trade-analysis-charts.md)
- Computed by `StatsComputer` (`projects/libs/SQAppLib/.../results/stats/StatsComputer.java`).
