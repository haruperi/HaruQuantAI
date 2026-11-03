# Retest strategies task

> Re-tests strategies from one databank (optionally with cross-checks) and stores the results into another databank — the engine behind the Retester.

## What it does

The Retest strategies task takes the strategies in a given databank and runs them again — optionally applying **cross-checks** (robustness tests) — then stores the results into a target databank. It is the engine behind the standalone Retester module. Retesting is how you verify that a strategy is robust and not just curve-fitted to one data set.

Common cross-checks / robustness tests applied during a retest:

- **Retest on additional markets** — tests the same strategy on other symbols and/or timeframes. A robust strategy should work, at least with some profitability, across multiple markets.
- **Retest with higher precision** — backtests the strategy again on the same data but at a higher tick/precision level. It is common to build fast on Selected-timeframe precision to filter out bad strategies quickly, then confirm the survivors at higher precision; some profitable strategies stop being profitable when tested more exactly.
- **Monte Carlo — trades manipulation** — runs many simulations that shuffle trade order and/or randomly skip trades, then reports results at confidence levels (e.g. at 95% there is only a 5% chance results are worse). Fast, because it works on the existing trade list rather than re-running backtests. Shows how much the equity curve depends on trade order and how missed trades would affect it.
- **What If simulations** — applies scenarios to the existing trade list, such as trading only on certain days/hours or omitting the most profitable trades. Very fast (no re-backtest) and can automatically filter out strategies whose performance falls below a limit (e.g. Net profit must stay at least 80% of the normal backtest).

A related **Automatic retest** task retests each strategy with the settings from its most recent build/retest, but first **updates the data** to include the most recent days — useful for periodic (e.g. weekly) rechecks. Its Full settings let you choose which settings are reused from last time and which you override.

## Settings tabs it uses

- [Cross-checks](../settings/cross-checks.md) — the robustness tests to run (additional markets, higher precision, Monte Carlo, What If, etc.); on Retest these annotate the results
- [Data](../settings/data.md) — symbols, timeframe, backtest period, precision
- [Trading options](../settings/trading-options.md) — sessions, time filters, order types, spreads
- [Money management](../settings/money-management.md) — position sizing
- ATM (Advanced Trade Management) — multiple / scale-out exits (see [settings reference](../settings/README.md))

## How it fits in a workflow

Retest reads from a **source databank** and writes results into a **target databank**. In a [Custom Project](../custom-projects.md) it usually follows a Build or Optimize step: build strategies, then retest the survivors with cross-checks (additional markets, higher precision, Monte Carlo) to weed out the fragile ones before filtering or building a portfolio. The Automatic retest variant is well suited to a scheduled project that refreshes data and rechecks a live set of strategies periodically.

## Related

- [Retester module overview](../retester.md)
- [Custom Projects & the task model](../custom-projects.md)
- [Settings tabs reference](../settings/README.md)
- [Results & databank](../results-databank.md)
- [Retester developer notes](../../onboard/05-retester/README.md)
