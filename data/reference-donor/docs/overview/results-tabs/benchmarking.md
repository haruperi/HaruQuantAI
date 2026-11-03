# Benchmarking — Results feature

> Compare your strategy against a standard benchmark (S&P 500 / SPY) inside the equity chart.

## What it shows

Benchmarking (added in Build 139) is a visual feature that lets you compare your strategy with a
standard benchmark — the S&P 500 index. It lives inside the [Equity Chart](equity-chart.md) tab.
When enabled, the equity chart gains two new elements:

1. a **yellow line** displaying the benchmark equity, and
2. a **table** showing the most important metrics for both your strategy and the benchmark.

The benchmark is computed by investing your defined initial capital — for example $10,000 —
into the S&P index (SPY ETF) and holding it for the whole time your strategy trades. This makes
it easy to see at a glance whether your strategy outperforms buy-and-hold, and — via the metrics
table — whether it does so at higher or lower risk (drawdown).

## How it works

Benchmarking is provided by the **Benchmark** equity-chart addon (`IEquityChartAddon`,
`Plugins/EquityChart/impl/Benchmark`). It contributes its benchmark dataset to the `EquityChart`
JSON served by the Equity Chart plugin at `/equitychart/`. The comparison figures come from
`BenchmarkTable` and `NormalizedData` in the equity-chart engine. Because it renders as an
overlay on the equity curve, the chart's **X axis must be set to Time**.

## Options & settings

Turn the benchmark on from the **Benchmark** menu in the equity chart. Because a strategy can
have more gains but also more risk than buy-and-hold, benchmarking offers **normalization** — a
recomputation of the initial capital used for the buy-and-hold benchmark so that one chosen
metric matches your strategy:

- **Normalize by $ drawdown** — initial capital so the benchmark's Max Drawdown equals the
  strategy's.
- **Normalize by % drawdown** — initial capital so the benchmark's Max % Drawdown equals the
  strategy's (the most commonly used option).
- **Normalize by Money management** — initial capital derived from the MM set by the strategy.
- **Normalize by exposure** — initial capital so the benchmark's exposure (% of time in trade)
  matches the strategy's. Useful for seasonal strategies that trade only occasionally.

An **alternative table** shows a simplified verdict — a thumbs up or down comparing the
strategy's Net profit ($) against the same risk (Drawdown %). This is a rough estimation only.

## Related

- Parent overview: [../results-databank.md](../results-databank.md)
- Host tab: [equity-chart.md](equity-chart.md)
- Sibling tabs: [overview.md](overview.md), [strategy-correlation.md](strategy-correlation.md)
- Developer detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
- Servlet endpoint (host tab): `/equitychart/`
