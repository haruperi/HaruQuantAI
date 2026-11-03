# Profile Chart — Results tab

> Profile charts of the strategy — its performance summarized across a chosen dimension.

## What it shows

The Profile Chart tab displays profile charts for the strategy: aggregated views that profile
the strategy's results across a dimension (for example a distribution or a per-category
breakdown of trade performance), helping you understand the shape of the strategy's behaviour
rather than a single time series.

## How it works

The tab is served by the `ProfileChart` plugin at `/profilechart/`. Like the other Results
tabs it obtains the strategy's `ResultsGroup` through an `IResultsGroupProvider` (a
`DatabankResultsGroupProvider`), computes the chart data from the result's trades and `SQStats`
using the shared statistics/charting engine, and releases the lock when done. The chart is
returned as data the RESULTS web app renders.

## Options & settings

- **Profile dimension** — the axis/category the chart profiles the results over.
- **Direction / sample** — the chart follows the selected result key (Long / Short / Both,
  In-Sample / Out-of-Sample / Full).

> This tab exposes a small set of controls; the specifics depend on the plugin and are
> described here at the level the source material supports.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Sibling tabs: [overview.md](overview.md), [equity-chart.md](equity-chart.md),
  [chart.md](chart.md), [trade-list.md](trade-list.md),
  [trade-analysis.md](trade-analysis.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint: `/profilechart/`
