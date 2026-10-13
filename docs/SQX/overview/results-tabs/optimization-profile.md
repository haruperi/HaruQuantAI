# Optimization Profile — Results tab

> Visualizes the whole optimization space — every parameter combination the Optimizer tested — as 2D, 3D, and scatter charts so you can spot robust regions instead of single lucky peaks.

## What it shows

The Optimization Profile tab is shown for results that carry an optimization profile on their `ResultsGroup` (`ResultsGroup.optimizationProfile`). It presents the full set of variants the Optimizer produced when it iterated a parameter (or parameters) from Start to Stop by Step:

- A **variant table** — one row per tested parameter combination, with the performance metrics computed for that combination.
- **Charts of the optimization space** — the same data plotted so you can see how a metric responds as the parameters change:
  - **2D charts** — one metric against one optimized parameter.
  - **3D charts** — one metric against two optimized parameters (a surface/landscape).
  - **Scatter charts** — metric-vs-metric clouds across all variants.

## How it works

An optimization tries different values of input parameters to find the ones that gave the best past performance (highest profit, best Return/DD, etc.). Looking only at the single best variant is dangerous — it is easily a curve-fit peak. The Optimization Profile plots the metric across the whole range of tested values so you can judge the *shape* of the response: a robust strategy sits on a broad plateau where neighbouring parameter values also perform well, rather than on a sharp isolated spike surrounded by poor results.

The tab reads the optimization variants stored on the result and renders them through its own views and chart types (`/optimprof/*` endpoints). Because each variant already has its metrics computed by `StatsComputer`, you can re-plot any available metric on the axes without recomputation.

## Options & settings

- **Chart type** — switch between 2D, 3D, and scatter representations of the same variant set.
- **Axis / metric selection** — choose which optimized parameter(s) form the axes and which metric (Net Profit, Drawdown, Profit Factor, Stability, etc.) is plotted.
- **Views** — configurable column/metric views over the variant table.
- **Export** — export the variant table (XLSX) for external analysis.

## Related

- Tab endpoint: `/optimprof/`
- Optimizer module overview: [../optimizer.md](../optimizer.md)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Sibling tab: [Walk-Forward](walk-forward.md) · [Profile Chart](profile-chart.md) · [Robustness Tests](robustness-tests.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
