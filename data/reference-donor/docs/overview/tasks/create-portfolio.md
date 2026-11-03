# Create portfolio task

> Merges strategies from a source databank into a single simulated portfolio.

## What it does

The Create portfolio task takes the strategies in a source databank and merges them into one **simulated portfolio** — combining their trades so you can see how the group performs together (combined equity, drawdown and other portfolio-level statistics) rather than one strategy at a time.

It is the pipeline counterpart of the two interactive portfolio modules in StrategyQuant X:

- **Portfolio Master** (Automatic Portfolio Builder) — builds an "optimal" portfolio composition from source strategies using a brute-force or genetic approach, combining strategies and ranking the resulting portfolios. It selects *which* strategies to include.
- **Portfolio Composer** — goes further and also decides *how much weight* (money) to assign each strategy, recomputing each strategy's position size from its weight (100% = original money management, 200% = double, 50% = half). It accounts for the portfolio's account balance, leverage and, importantly, free margin — skipping orders on days when free margin is insufficient. Created with stock strategies in mind but usable for other assets.

The Create portfolio task automates the merge step so portfolio building can run unattended inside a project.

## Settings tabs it uses

- **Portfolio settings** — the source databank to merge from, the target databank for the resulting portfolio, and portfolio-level parameters such as account balance and leverage.
- **Composition / weighting** (where applicable) — which strategies to combine and, for weighted portfolios, the weight applied to each (which recomputes its position size).

This task does not re-generate strategies; it combines already-tested strategies into a portfolio simulation.

## How it fits in a workflow

Create portfolio reads from a **source databank** of finished, vetted strategies and writes the resulting portfolio into a **target databank**. In a [Custom Project](../custom-projects.md) it is typically the final step: build, optimize, retest and filter strategies down to a robust set, then merge that set into a portfolio to evaluate combined performance.

## Related

- [Portfolio Master overview](../portfolio-master.md)
- [Portfolio Composer overview](../portfolio-composer.md)
- [Custom Projects & the task model](../custom-projects.md)
- [Results & databank](../results-databank.md)
- [Settings tabs reference](../settings/README.md)
- [Portfolio developer notes](../../onboard/09-portfolio/README.md)
