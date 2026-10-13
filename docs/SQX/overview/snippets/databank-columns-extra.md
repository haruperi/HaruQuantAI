# Trade List & Walk-Forward columns — full catalog

> Reference enumeration of the built-in extra table columns for the **Trade List** (per-order
> detail) and **Walk-Forward** (per-strategy WF summary) tables. This complements
> [`../stats-metrics.md`](../stats-metrics.md), which covers the main Databank columns.

## How the set is assembled

**Trade list columns** are snippet classes extending `com.strategyquant.tradinglib.TradelistColumn`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Columns/Trades/`). Their constructor
declares a display name and a display format (`super(name, format[, fontBold])`), and they
implement `getValue(Order order)` — pulling one field straight off an individual `Order` — plus
optionally `getFormattedValue(Object)` for custom rendering. `fontBold=true` is used on the P/L
columns to make them visually stand out. Trade-list columns describe a single order, so there is
**no optimization goal** (goal is "—" for all of them); `setWidth(px)` sets the default column
width in the Trade List UI.

**Walk-Forward columns** are snippet classes extending
`com.strategyquant.tradinglib.WalkForwardColumn`
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/Columns/WalkForward/`). Their
constructor declares an internal stats key, a display name, a `DatabankColumn` display format, and
an optimization **goal** (`ValueTypes.Maximize` / `Minimize`), just like a regular Databank column.
They implement `compute(WalkForwardResult wfResult)`, aggregating a `StatsKey` value across the
strategy's `wfResult.wfPeriods` (one value per out-of-sample run).

## Trades columns

| Display name | Class | Format | Description |
|---|---|---|---|
| Balance | `Balance` | Money | Account balance after the trade (`order.AccountBalance`). |
| BarsInTrade | `BarsInTrade` | Integer | Number of bars the trade stayed open (`order.BarsInTrade`). |
| Close price | `ClosePrice` | Text | Trade's close price, formatted to the symbol's decimal precision; blank for pending orders. |
| Close time | `CloseTime` | Time | Trade's close timestamp, formatted as full date + minute. |
| Close type | `CloseType` | Text | How the trade closed (e.g. stop-loss/take-profit/exit signal), via `ATMExit.toString` (ATM exits) or `OrderCloseTypes.toString`. |
| Comment | `Comment` | Text | Free-text order comment (`order.Comment`). |
| Comm/Swap | `CommSwap` | Money | Commission + swap cost for the trade; blank for pending orders. |
| Drawdown | `Drawdown` | Money | Drawdown attributable to this trade (`order.DD`); blank for pending orders. |
| MAE ($) | `MAE` | Money | Maximum Adverse Excursion in money, sign-flipped to be shown as a negative/loss value; blank for pending orders. |
| MAE (pips) | `MAEPips` | Decimal | Maximum Adverse Excursion in pips (`order.PipsMAE`); blank for pending orders. |
| MFE ($) | `MFE` | Money | Maximum Favorable Excursion in money (`order.MFE`); blank for pending orders. |
| MFE (pips) | `MFEPips` | Decimal | Maximum Favorable Excursion in pips (`order.PipsMFE`); blank for pending orders. |
| Line Number | `NumberOfTrade` | Integer | Sequential order/line number (`order.Order`). |
| Open price | `OpenPrice` | Text | Trade's open price, formatted to the symbol's decimal precision. |
| Open time | `OpenTime` | Time | Trade's open timestamp, formatted as full date + minute. |
| Orig. Open price | `OriginalOpenPrice` | Text | Original (pre-fill) open price for pending-type orders (`order.OriginalPrice`). |
| Orig. Open time | `OriginalOpenTime` | Time | Original submission time for pending order types (limit/stop/stop-limit); blank for market orders. |
| % Drawdown | `PctDrawdown` | Percent | Drawdown attributable to this trade, in % (`order.PctDD`); blank for pending orders. |
| Profit/Loss | `ProfitLoss` | Money (bold) | Trade P/L in money (`order.PL`); blank for pending orders. |
| Profit/Loss Pct | `ProfitLossPct` | Percent (bold) | Trade P/L in % (`order.PctPL`); blank for pending orders. |
| Profit/Loss Pips | `ProfitLossPips` | Decimal (bold) | Trade P/L in pips (`order.PipsPL`); blank for pending orders. |
| Profit Target price level | `PTLevel` | Decimal (5dp) | Take-profit price level (`order.TakeProfit`). |
| Result name | `ResultName` | Text | Name of the result/setup the trade belongs to (`order.SetupName`). |
| Sample type | `SampleType` | Text | IS / OOS / other sample classification of the trade (`order.SampleType`, via `SampleTypes.typeToString`). |
| Size | `Size` | Text | Trade size / lot size (`order.Size`). |
| Slippage ($) | `SlippageInMoney` | Money | Modeled slippage in money (`order.SlippageInMoney`); only populated for TradeStation/MultiCharts engines — always 0 for MetaTrader/JForex, where slippage is applied in pips; blank for pending orders. |
| Stop Loss price level | `SLLevel` | Decimal (5dp) | Stop-loss price level (`order.StopLoss`). |
| Symbol | `Symbol` | Text | Symbol the trade was made on (`order.Symbol`). |
| Ticket | `Ticket` | Integer | Order ticket number (`order.Ticket`). |
| Time in trade | `TimeInTrade` | Text | Duration the trade stayed open, formatted as date/time (`order.Duration`). |
| Type | `Type` | Text | Order type (Buy, Sell, BuyLimit, BuyStop, SellLimit, SellStop, Balance, Deposit, Withdrawal, …). |

## Walk-Forward columns

| Display name | Class | Goal | Format | `StatsKey` aggregated | Description |
|---|---|---|---|---|---|
| Max Drawdown in one run | `WFMaxDDbyRun` | Min | Money | `DRAWDOWN` | Largest per-run drawdown (money) across all WF periods. |
| Max % Drawdown in one run | `WFMaxPctDDbyRun` | Min | Percent | `PCT_DRAWDOWN` | Largest per-run drawdown (%) across all WF periods. |
| Max profit in one run | `WFMaxProfitByRun` | Max | Money | `NET_PROFIT` | Largest single-run net profit across all WF periods. |
| Max profit in one run as % of total | `WFMaxProfitByRunInPct` | Max | Percent | `NET_PROFIT` | The best single run's net profit as a % of the strategy's total net profit across all runs (100% if the best run is positive but the total is negative). |
| Max Stagnation in % | `WFMaxStagnationInPct` | Min | Percent | `STAGNATION_PERIOD_PCT` | Largest per-run stagnation percentage across all WF periods. |
| Min trades in one run | `WFMinTradesInRun` | Max | Integer | `NUMBER_OF_TRADES` | Smallest per-run trade count across all WF periods (goal is Maximize — you want the *worst* run to still have enough trades). |
| Percentage of profitable runs | `WFPctOfProfitableRuns` | Max | Percent | `NET_PROFIT` | Share of WF runs (excluding the last period) with positive net profit. |
| WF Score | `WFScore` | Max | Percent | `wfResult.scorePerc` (precomputed) | Overall walk-forward score percentage assigned to the strategy. |

## Related

- Main Databank columns / stats metrics reference: [`../stats-metrics.md`](../stats-metrics.md)
- Trade List tab: [`../results-tabs/trade-list.md`](../results-tabs/trade-list.md)
- Walk-Forward tab: [`../results-tabs/walk-forward.md`](../results-tabs/walk-forward.md)
- Snippets hub: [`README.md`](README.md)
- Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Columns/Trades/`, `.../SQ/Columns/WalkForward/`
