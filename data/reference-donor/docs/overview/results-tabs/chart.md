# Chart — Results tab

> The strategy's trades drawn on the price chart, so you can see exactly where each order opened and closed.

## What it shows

The Chart tab renders the traded instrument as an OHLC (candlestick/bar) price chart and
overlays the strategy's orders on it — entry and exit points, direction, and the price levels
at which trades happened. Technical indicators can be drawn on the same chart, so you can
visually inspect how the strategy's entries and exits line up with price action and with the
indicators it uses. It shows the complete chart data for the backtest — the full history chart
with all the indicators used and all orders drawn on it — so you can review how the strategy is
trading.

This tab is available **only** if you explicitly configure SQ to save chart data, via
**Settings → Trading options → Store chart data**. Without that option enabled, the backtest does
not retain the data needed to render the chart.

## How it works

The tab is served by the `Chart` plugin at `/resultsCharts/`. The price chart is built by the
stock-chart engine in `SQAppLib/equitychart/stockchart/` — `StockChartData` plus the
`StockLoader*` loaders assemble the OHLC series, and `Indicator*` classes add indicator
series. The strategy's orders are read from the `ResultsGroup`'s `OrdersList` and drawn as
markers on the price series, so the chart shows the actual fills of the backtest.

As with every Results tab, the servlet obtains the strategy's `ResultsGroup` through an
`IResultsGroupProvider` (a `DatabankResultsGroupProvider`), holds the lock while it builds the
chart data, and releases it afterwards.

## Options & settings

- **Symbol** — the traded instrument whose OHLC data is charted.
- **Indicators** — technical indicators drawn on the price chart.
- **Order markers** — entry/exit points of the strategy's trades overlaid on price.
- **Zoom / pan** — navigate across the price history.
- **Availability** — requires **Settings → Trading options → Store chart data** to be enabled
  when the backtest is run.

> The controls exposed depend on the chart engine; this page describes the tab at the level the
> source material supports.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [equity-chart.md](equity-chart.md),
  [trade-list.md](trade-list.md), [trade-analysis.md](trade-analysis.md),
  [profile-chart.md](profile-chart.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/resultsCharts/`
