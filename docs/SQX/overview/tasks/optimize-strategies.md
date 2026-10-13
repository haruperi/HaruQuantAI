# Optimize strategies task

> Starts a standard Optimizer that tunes a strategy's parameters — simple, walk-forward, WF matrix or sequential — and stores the results into a target databank.

## What it does

The Optimize strategies task is the engine behind the Optimizer module. Optimization means testing a strategy with different values of its parameters (indicator periods, comparison constants, SL/PT multipliers, etc.) to find the values that gave the best performance in the past. For every parameter you want to optimize you check its line and set **Start**, **Stop** and **Step**; the optimizer iterates from Start to Stop. The **Original** value is kept so the original strategy can be retested for comparison. The number of tests can be capped with **Maximum optimizations / Maximum tests**.

It supports several optimization types:

- **Simple optimization** — tests combinations of the selected parameter values on a single data set and stores each combination (or only the best) into the databank. Powerful but prone to curve-fitting — the values ideal for history may not hold in the future.
- **Walk-Forward Optimization** — splits the data into periods, each with an in-sample optimization part followed by an out-of-sample run part. It simulates periodic reoptimization and tells you whether the strategy is robust and benefits from reoptimization. Configured via **Out of Sample %** and **Walk Forward Runs**; a customizable **Robustness score** decides pass/fail.
- **Walk-Forward Matrix** — runs many Walk-Forward optimizations across a range of run counts and OOS % (Start/Stop/Increment). It doubles as a robustness check (looking for clusters of successful combinations in the 3D score chart) and as a way to find the optimal reoptimization period. Very time-consuming; a faster Simulation mode is available.
- **Sequential optimization** — optimizes parameters one at a time, each step reusing the best value from prior steps, and chooses the value in the middle of a **stable area** rather than the single best fitness. This reduces overfitting; if no stable area is found the original value is kept. Also available as a cross-check.

Every optimization automatically produces an **Optimization Profile** (distribution of results across all runs) and, when enabled, **System Parameter Permutation (SPP)** median statistics — both used to judge whether a strategy has a real edge. These are exposed through the *Opt. Profile / Sys. Param. Permutation* cross-check.

By default only **Recommended parameters** are offered for optimization (indicator periods, entry multiplier, used SL/PT parameters) — keeping the number of optimizable parameters low reduces curve-fitting.

## Settings tabs it uses

- Optimization ranges / parameters — the parameter table (Start/Stop/Step) plus the optimization type and its options (this is the Optimizer's own configuration, not a shared tab)
- [Data](../settings/data.md) — symbols, timeframe, backtest period, IS/OOS split, precision
- [Ranking](../settings/ranking.md) — fitness/ranking criteria and databank storage limits
- [Trading options](../settings/trading-options.md) — sessions, time filters, order types, spreads
- [Money management](../settings/money-management.md) — position sizing
- ATM (Advanced Trade Management) — multiple / scale-out exits (see [settings reference](../settings/README.md))

## How it fits in a workflow

Optimize takes strategies from a **source databank** (or a single loaded strategy) and writes the optimized results into a **target databank**. In a [Custom Project](../custom-projects.md) it typically sits after a Build or Retest step: build strategies, filter the promising ones, then optimize their recommended parameters or run a Walk-Forward Matrix as a robustness check before creating a portfolio.

## Related

- [Optimizer module overview](../optimizer.md)
- [Custom Projects & the task model](../custom-projects.md)
- [Settings tabs reference](../settings/README.md)
- [Results & databank](../results-databank.md)
- [Optimizer developer notes](../../onboard/06-optimizer/README.md)
