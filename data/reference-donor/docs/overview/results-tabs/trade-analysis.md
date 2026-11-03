# Trade Analysis — Results tab

> Deeper per-trade analyses and a year-by-year breakdown of the strategy's performance.

## What it shows

The Trade Analysis tab goes beyond the flat trade list to summarize the strategy's behaviour.
It displays the strategy's **yearly performance** plus a **configurable grid of charts** of
various backtest metrics — profit/loss and trade counts broken down by hour, weekday, day of
month, month, year, trade duration, close type, and trade direction. The yearly view groups
statistics by year so you can see how profit, number of trades, and other measures changed from
one year to the next, and whether performance was consistent over the whole backtest period
rather than driven by a single good year.

## Available charts

Charts are pluggable snippets (each a `TradeAnalysisChart` subclass) loaded at runtime from the
`TradeAnalysis` snippet directory, so the exact set can be extended. SQX ships **26 selectable
charts** plus one fixed **P/L by year** chart always drawn at the top; by default the grid shows
12 of them, and the chosen set is remembered under the `TradeAnalysisCharts` setting. They cover
profit/loss, trade counts, and win/loss counts broken down by hour, weekday, day, month, year,
trade duration, and close type, plus long-vs-short splits.

> **Full catalog:** the complete list — every chart's display name, snippet class, and chart type —
> lives in [`trade-analysis-charts.md`](trade-analysis-charts.md).
> Read that only when you need the exact enumeration.

## How it works

The tab is served by the `TradeAnalysis` plugin at `/tradeanalysis/`. It obtains the strategy's
locked `ResultsGroup` through an `IResultsGroupProvider` and computes its analyses from the
`OrdersList` and the strategy's `SQStats`.

The yearly breakdown is produced by `AnnualStatsComputer`, which aggregates trades into
per-year buckets and computes the statistics for each year. Period breakdown helpers such as
`TradingPeriodTypes` and the `StatsComputer` metric registry back the computed values. As with
all Results tabs, the servlet holds the lock while computing and releases it when finished.

## Options & settings

- **Yearly breakdown** — per-year statistics computed by `AnnualStatsComputer`.
- **Configurable charts** — charts of backtest metrics grouped by period, such as trades per
  hour, day of week, and day of month.
- **Per-trade analyses** — analyses derived from the individual trades in the `OrdersList`.
- **Direction / sample** — the analysis follows the selected result key (Long / Short / Both,
  In-Sample / Out-of-Sample / Full).

> The exact set of analyses depends on the plugin; this page describes the tab at the level the
> source material supports.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [equity-chart.md](equity-chart.md),
  [chart.md](chart.md), [trade-list.md](trade-list.md),
  [profile-chart.md](profile-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/tradeanalysis/`
