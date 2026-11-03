# Overview — Results tab

> The headline summary of a strategy: its key performance metrics and a period-by-period profit table.

## What it shows

The Overview tab is the default view when you open a strategy from the databank. It presents
the strategy's computed statistics from the backtest in a compact, at-a-glance layout: net
profit, drawdown, profit factor, number of trades, win percentage, and the full set of
performance metrics (CAGR, Sharpe Ratio, Return/DD ratio, R Expectancy, SQN, Stability, and
so on). Alongside the metric blocks it typically renders a monthly / yearly performance table
so you can see how profit was distributed over time.

The values reflect the currently selected result "key" — you can view statistics for the
Portfolio result, a single direction (Long / Short / Both), and a chosen sample
(In-Sample / Out-of-Sample / Full).

## How it works

The tab is served by `OverviewServletPlugin` at `/overview/`. When it loads, it POSTs to
`/overview/getOverviewContent` with the result context (`projectName`, `databankName`,
`strategyName`, `resultKey`, `direction`, `sampleType`, `template`).

The servlet asks its `IResultsGroupProvider` (a `DatabankResultsGroupProvider`) for the
locked `ResultsGroup`, then looks up the requested template in the `OverviewTemplates`
registry — the templates are runtime snippets registered under `SQ/Stats/Overview` (for
example `SQDefaultWithPortfolio`). The chosen `OverviewTemplate.drawValues(rg, resultKey,
StatsTypeCombination(direction, PlTypes.Money, sampleType))` renders the HTML by reading
computed metric values out of `SQStats` via the `StatsComputer` (which lazily computes each
`DatabankColumn` metric through its dependency graph). The servlet returns the rendered HTML
and releases the lock.

Because the Overview is template-driven, new overview layouts can be added without Java code —
by writing a new `OverviewTemplate` snippet.

## Options & settings

- **Overview template** — the layout/snippet used to render the metrics (e.g. a default
  template vs. one that includes the portfolio breakdown).
- **Direction** — Long / Short / Both, selecting which `Result` is displayed.
- **Sample type** — In-Sample / Out-of-Sample / Full backtest sample.
- **Result key** — the specific result within the group (Portfolio or a per-symbol/direction
  result), determined by what the strategy contains.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [equity-chart.md](equity-chart.md), [chart.md](chart.md),
  [trade-list.md](trade-list.md), [trade-analysis.md](trade-analysis.md),
  [profile-chart.md](profile-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/overview/` (content via `/overview/getOverviewContent`)
