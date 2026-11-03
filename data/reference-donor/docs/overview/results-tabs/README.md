# Results Tabs — Detailed Reference

When a strategy is opened from the Databank, its **Results** view shows a set of tabs, each a
separate plugin (`IResultPlugin`). This folder has one leaf page per tab: **what it shows**, **how
it works**, and **what options/settings** it exposes.

Parent: [Results & Databank overview](../results-databank.md) · [Overview index](../README.md)
Front-end embedding and the new **RESULTS2** app:
[`results-integration/`](../../results-integration/README.md)

| Tab | Shows | Page |
|-----|-------|------|
| **Overview** | Summary performance statistics for the strategy | [overview.md](overview.md) |
| **Equity Chart** | Main equity curve + subcharts and overlay addons | [equity-chart.md](equity-chart.md) |
| **Chart** | Trades drawn on the price chart | [chart.md](chart.md) |
| **Trade List** | Table of individual trades (+ configurable views) | [trade-list.md](trade-list.md) |
| **Trade Analysis** | Per-trade and yearly breakdown analyses | [trade-analysis.md](trade-analysis.md) · [full chart catalog](trade-analysis-charts.md) |
| **Source Code** | Generated strategy code for the target platform | [source-code.md](source-code.md) |
| **Strategy Config** | Current config vs. the strategy's backtest config | [strategy-config.md](strategy-config.md) |
| **Strategy Correlation** | Correlation matrix across merged/portfolio results | [strategy-correlation.md](strategy-correlation.md) |
| **Benchmarking** | Compare the strategy vs. an S&P 500 benchmark | [benchmarking.md](benchmarking.md) |
| **Custom Analysis** | Custom snippet-based metrics/filters on strategies/databanks | [custom-analysis.md](custom-analysis.md) |
| **Walk-Forward** | Walk-forward periods, matrix, and parameter stability | [walk-forward.md](walk-forward.md) |
| **Optimization Profile** | 2D/3D/scatter charts of the optimization space | [optimization-profile.md](optimization-profile.md) |
| **Robustness Tests** | Monte Carlo results: confidence levels, risk of ruin | [robustness-tests.md](robustness-tests.md) |
| **Profile Chart** | Profile charts of a strategy | [profile-chart.md](profile-chart.md) |
| **Stockpicker Overview** | Multi-symbol stockpicker stats/treemap/top list | [stockpicker-overview.md](stockpicker-overview.md) |
| **Portfolio Composer Chart** | Combined portfolio equity | [portfolio-composer-chart.md](portfolio-composer-chart.md) |
| **Dashboard / User plugins** | Live top-N panels; user-authored iframe tabs | [dashboard-and-user-plugins.md](dashboard-and-user-plugins.md) |

> Each tab is backed by a servlet endpoint (e.g. `/overview/`, `/equitychart/`, `/tradelist/`) that
> pulls the strategy's `ResultsGroup` via an `IResultsGroupProvider`. Developer detail:
> [../../onboard/08-results/](../../onboard/08-results/README.md).
