# Equity Chart — Results tab

> The strategy's equity curve, with subcharts and optional overlay addons for benchmark, drawdown, volatility and volume.

## What it shows

The Equity Chart tab plots the strategy's equity development over the backtest — the main
curve built from the closed trades — together with trade markers, In-Sample / Out-of-Sample
boundaries and year markers. Below or over the main curve it can show additional subcharts and
overlays (drawdown, volatility, traded volume, a benchmark line, a daily equity view), letting
you judge the shape and smoothness of the curve, not just the final profit.

A **stagnation marker** highlights the maximum stagnation period — the longest stretch it took
the strategy to make a new equity high. For a **portfolio**, the tab draws a chart for every
symbol/timeframe tested plus the equity of the complete portfolio. When you use the
**Backtest on additional markets** cross check to test the strategy on more markets, the results
for all those backtests are added to the strategy and you can switch between them or display all
equity curves at once.

Two related curves can be shown: **Balance** is calculated from closed positions only, while
**Equity** is the balance plus the value of open positions. A **Daily equity** view and
**MAE / MFE** lines can also be turned on.

## How it works

The tab is served by `EquityChartPlugin` at `/equitychart/`; the data is fetched via
`/equitychart/getChartData`, which returns a JSON `EquityChart` object consumed by the UI.

The engine lives in `SQAppLib/equitychart/`. `Equity` computes the curves from the
`OrdersList` (daily/cumulative equity, cumulative MAE/MFE). `EquityChart` is the JSON
container the UI renders: `MainChartDataset` (the equity curve), one or more `SubChart`s,
`Marker`/`SampleMarkers`/`YearMarkers` annotations (trades, IS/OOS boundaries, years),
`AreaFill`, benchmark data and zoom state. Large curves are downsampled by `ChartOptimalizer`
so the chart stays responsive.

Overlays are pluggable through the `IEquityChartAddon` interface. The shipped addons
(`Plugins/EquityChart/impl/*`) are **Benchmark**, **EquityChartDrawdown**, **Volatility**,
**EquityChartVolume** and **DailyChart** — each contributes its own dataset/subchart to the
`EquityChart` JSON. Derived comparison metrics come from `BenchmarkTable`, `NormalizedData`,
`Stagnation` and `MaxNewHighDuration`.

Mini versions of the equity chart (used as databank/dashboard thumbnails) are produced
separately by `MiniEquityChartComputer` / `DailyEquity`.

## Options & settings

- **Subcharts** — additional panels shown under the main equity curve.
- **Addons / overlays** — Benchmark, Drawdown, Volatility, Volume and Daily Chart, each
  toggled as an overlay on the equity view.
- **Markers** — trade markers, In-Sample / Out-of-Sample boundary markers and year markers,
  plus the maximum-stagnation marker.
- **Balance vs Equity** — show balance (from closed positions), equity (balance + open
  positions), Daily equity, and MAE / MFE lines.
- **Portfolio / additional markets** — switch between per-market equity curves, or display all
  of them at once, plus the complete portfolio equity.
- **Zoom** — interactive zoom over a segment of the curve.
- **Direction / sample** — like other tabs, the curve reflects the selected result key
  (direction and In-Sample / Out-of-Sample / Full sample).

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [chart.md](chart.md),
  [trade-list.md](trade-list.md), [trade-analysis.md](trade-analysis.md),
  [profile-chart.md](profile-chart.md)
- Related feature: [benchmarking.md](benchmarking.md) (the Benchmark overlay lives in this tab),
  [strategy-correlation.md](strategy-correlation.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/equitychart/` (data via `/equitychart/getChartData`)
