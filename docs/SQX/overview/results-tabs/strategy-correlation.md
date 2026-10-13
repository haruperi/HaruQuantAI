# Strategy Correlation — Results tab

> A correlation matrix across the results merged into one strategy or portfolio.

## What it shows

The Strategy Correlation tab (also called **Portfolio correlation**) is visible only when the
strategy backtest contains multiple results. That happens when you either:

- used the **Merge** function (in the databank) to merge multiple strategies into a portfolio, or
- used the **Backtest on additional markets** cross check to test the strategy on more markets.

The tab presents a correlation matrix computed across those results. When multiple backtests are
merged into one strategy, you can also see the equity curves for all of them together in the
[Equity Chart](equity-chart.md) tab.

## How it works

The tab is served by the `PortfolioCorrelation` plugin at `/portfoliocorrelation/`. It obtains
the strategy's locked `ResultsGroup` through an `IResultsGroupProvider`, then computes the matrix
with `PortfolioCorrelationComputer` (and `OverlappingTradesComputer` for overlapping trades). The
computation runs as an asynchronous task and streams progress/results back to the UI over a
WebSocket sender, since the matrix has to be computed on demand.

## Options & settings

- **Correlation period** — compute correlation by hour, day, week, or month.
- **Correlation basis** — correlate by Profit/Loss or by trade counts.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [equity-chart.md](equity-chart.md), [overview.md](overview.md),
  [portfolio-composer-chart.md](portfolio-composer-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/portfoliocorrelation/`
