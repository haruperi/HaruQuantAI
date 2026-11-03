# Trade Analysis — full chart catalog

> Reference enumeration of every built-in chart on the **Trade Analysis** results tab. This is a
> lookup table; for what the tab is and how it works see
> [`trade-analysis.md`](trade-analysis.md).

## How the set is assembled

Each chart is a snippet class extending `TradeAnalysisChart`
(`projects/libs/SQAppLib/.../TradeAnalysisChart.java`). At startup `TradeAnalysisChartsList` loads
every class found in the `TradeAnalysis` snippet directory
(`work_directory/StrategyQuant/internal/extend/Snippets/SQ/TradeAnalysis/`), so **the set is
extensible** — a user can drop in a new snippet and it appears in the picker. The list below is
the stock set shipped with SQX.

The `TradeAnalysisServlet` exposes all of them via `getTypes()` **except** `PLbyYearChart`, which
it always renders separately as the fixed chart at the top of the tab (`response.fixedChart`). Each
chart's `draw()` receives the filtered `OrdersList`, the P/L type (Money), and the selected trading
period, and returns an `AbstractChart` (`BarChart`, `PieChart`, or `TimeSeriesScatterChart`).

## Fixed chart (always shown)

Rendered above the configurable grid; not part of the selectable list.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| P/L by year | `PLbyYearChart` | Bar | Net profit/loss aggregated per calendar year. |

## Profit/Loss distribution

Winning vs. losing share of the strategy, as pie charts.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| Profit/Loss | `PLChart` | Pie | Share of total gross profit vs. total gross loss across all trades. |
| Long Profit/Loss | `PLLongChart` | Pie | Same split, restricted to long trades. |
| Short Profit/Loss | `PLShortChart` | Pie | Same split, restricted to short trades. |

## Long vs. Short

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| Long vs Short trades | `LongShortTradesChart` | Pie | Number of long trades vs. number of short trades. |
| Long vs Short P/L | `LongShortProfitLossChart` | Bar | Profit contributed by the long side vs. the short side. |

## P/L by period

Profit/loss summed into buckets of the chosen time dimension.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| P/L by month | `PLbyMonthChart` | Bar | P/L grouped by month of year (Jan–Dec). |
| P/L by weekday | `PLbyWeekdayChart` | Bar | P/L grouped by day of week (Sun–Sat). |
| P/L by day | `PLbyDayChart` | Bar | P/L grouped by day of month (1–31). |
| P/L by hour | `PLbyHourChart` | Bar | P/L grouped by hour of day (0–23). |
| P/L by trade duration | `PLbyTradeDurationChart` | Bar | P/L grouped by how long trades stayed open (auto-scaled duration buckets). |
| P/L Growth by duration | `PLGrowthByDurationChart` | Time-series scatter | Cumulative P/L growth plotted against trade duration. |

## Trade count by period

Number of trades falling into each bucket.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| Trades by year | `TradesByYearChart` | Bar | Number of trades per calendar year. |
| Trades by month | `TradesByMonthChart` | Bar | Number of trades per month of year. |
| Trades by weekday | `TradesByWeekdayChart` | Bar | Number of trades per day of week. |
| Trades by day | `TradesByDayChart` | Bar | Number of trades per day of month. |
| Trades by hour | `TradesByHourChart` | Bar | Number of trades per hour of day. |
| Trades by duration | `TradesByDurationChart` | Bar | Number of trades per duration bucket. |
| Trades by Close Type | `TradesByCloseTypeChart` | Bar | Number of trades grouped by how they closed (e.g. stop-loss, take-profit, exit signal). |

## Wins/Losses count by period

Winning vs. losing trade counts, split per bucket.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| Wins/Losses by month | `WinLossCountByMonthChart` | Bar | Count of winners vs. losers per month of year. |
| Wins/Losses by weekday | `WinLossCountByWeekdayChart` | Bar | Count of winners vs. losers per day of week. |
| Wins/Losses by day | `WinLossCountByDayChart` | Bar | Count of winners vs. losers per day of month. |
| Wins/Losses by hour | `WinLossCountByHourChart` | Bar | Count of winners vs. losers per hour of day. |

## Wins/Losses profit by period

Profit from winners vs. loss from losers, split per bucket.

| Display name | Snippet class | Chart type | What it shows |
|--------------|---------------|------------|---------------|
| Wins/Losses Profit by month | `WinLossPLByMonthChart` | Bar | Profit of winners vs. loss of losers per month of year. |
| Wins/Losses Profit by weekday | `WinLossPLByWeekdayChart` | Bar | Same, per day of week. |
| Wins/Losses Profit by day | `WinLossPLByDayChart` | Bar | Same, per day of month. |
| Wins/Losses Profit by hour | `WinLossPLByHourChart` | Bar | Same, per hour of day. |

## Default grid

When no saved selection exists (`TradeAnalysisCharts` setting), the tab shows these 12 charts:

`P/L by hour`, `P/L by weekday`, `Trades by weekday`, `Long vs Short P/L`, `Wins/Losses by
weekday`, `Wins/Losses Profit by month`, `Long vs Short trades`, `P/L Growth by duration`, `Trades
by hour`, `Long Profit/Loss`, `Short Profit/Loss`, `Trades by duration`.

## Related

- Tab overview: [`trade-analysis.md`](trade-analysis.md)
- Stats metrics reference: [`../stats-metrics.md`](../stats-metrics.md)
- Servlet: `TradeAnalysisServlet` · endpoint `/tradeanalysis/`
