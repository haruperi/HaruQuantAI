# Stockpicker Overview — Results tab

> Summarizes a stock-picking strategy across all the symbols it traded — aggregate statistics, a treemap of per-symbol contribution, a top chart, and a ranked symbol list.

## What it shows

The Stockpicker Overview tab is the multi-symbol summary for results from the Stockpicker engine (a strategy that trades across many instruments). Where the plain Overview reports one strategy's headline metrics, this tab breaks the result down *by symbol*:

- **Aggregate statistics** — combined performance across the whole basket of symbols the strategy traded.
- **Treemap** — a per-symbol tile map where tile size/color reflects each symbol's contribution (for example profit or number of trades), making dominant and weak symbols easy to spot at a glance.
- **Top chart** — a chart of the leading symbols by the chosen metric.
- **Top list** — a ranked table of symbols with their individual statistics.

## How it works

A stockpicker result carries per-symbol data on its `ResultsGroup` (via the `symbolsMap`/per-symbol results), computed by `StatsComputer`. The tab reads that per-symbol breakdown and renders it three ways — treemap, top chart, and ranked list — plus the rolled-up aggregate stats. This lets you judge whether the overall result is broad-based (many symbols contributing) or driven by only a few instruments, which matters for robustness and diversification.

The Stockpicker Overview is the aggregate companion to the per-symbol Stockpicker tab (`/stockpicker/`), which exposes the individual stock-picking engine results.

## Options & settings

- **Metric selection** — choose which metric drives the treemap tiles, the top chart, and the ranking of the top list.
- **Views/columns** — configure the columns shown in the per-symbol list.
- **Drill-down** — select a symbol to focus on its individual contribution and statistics.

## Related

- Tab endpoint: `/spoverview/` (per-symbol engine results: `/stockpicker/`)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Portfolio Composer module overview: [../portfolio-composer.md](../portfolio-composer.md)
- Sibling tab: [Portfolio Composer Chart](portfolio-composer-chart.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
