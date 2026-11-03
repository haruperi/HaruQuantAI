# Build strategies task

> Starts a standard Builder that generates new trading strategies from your configuration and stores the best ones into a target databank.

## What it does

The Build strategies task is the engine behind the Builder module — the "core" of StrategyQuant X, where new trading strategies are created. It generates candidate strategies, backtests them, and continually stores the top candidates (by your ranking criteria) into a **target databank** you specify.

There are two build modes:

- **Random Generation** — StrategyQuant continually generates and tests new random strategies, one after another, until stopped. It is faster and simpler than genetic evolution, can run for days to evaluate millions of strategies, and is less prone to overfitting because a generated strategy is not further optimized. Its downside is that a strategy, once generated, is not further evolved.
- **Genetic Evolution** — StrategyQuant first generates an initial population of random candidates (using Random Generation), then evolves the population over generations to produce better candidates. The process ends after a set number of generations or when there is no further improvement. It can improve on the best random candidates but is slower, can hit dead ends, is bounded by the population size, and is more prone to overfitting (it is essentially an optimization process).

A generated strategy from Random Generation can be reused as the initial population for a later genetic build.

## Settings tabs it uses

- [What to build](../settings/what-to-build.md) — strategy type, style, direction, complexity, SL/PT
- [Building blocks](../settings/building-blocks.md) — which indicators, signals and operators the generator may use
- [Data](../settings/data.md) — symbols, timeframes, backtest period, IS/OOS split, precision
- [Genetic options](../settings/genetic-options.md) — population, generations, islands (genetic mode)
- [Ranking](../settings/ranking.md) — fitness/selection criteria and databank storage limits
- [Trading options](../settings/trading-options.md) — sessions, time filters, order types, spreads, SL/PT caps
- [Money management](../settings/money-management.md) — position sizing
- ATM (Advanced Trade Management) — multiple / scale-out exits (see [settings reference](../settings/README.md))
- [Cross-checks](../settings/cross-checks.md) — robustness tests applied as filters during generation

## How it fits in a workflow

A Build task has no source databank — it creates strategies from scratch and writes the survivors into its **target databank**. In a [Custom Project](../custom-projects.md) pipeline it is usually the first step: build into a databank, then feed that databank to downstream Retest, Optimize, Filter or Create-portfolio tasks. You can also chain builds — for example run a Random Generation build, then a Genetic Evolution build that uses the first build's output as its initial population.

## Related

- [Builder module overview](../builder.md)
- [Custom Projects & the task model](../custom-projects.md)
- [Settings tabs reference](../settings/README.md)
- [Results & databank](../results-databank.md)
- [Builder developer notes](../../onboard/04-builder/README.md)
