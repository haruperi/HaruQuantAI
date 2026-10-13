# Walk-Forward (Optimization / Matrix) — robustness test

> Repeatedly re-optimizes the strategy on past data and tests it forward, checking it survives periodic re-optimization.

## What it does

**Walk-Forward Optimization (WFO)** is a special backtest made of many smaller backtests. The history
is split into a configurable number of periods, each with an *optimization* part and a *run* part.
The strategy is optimized on optimization period 1, and the best parameters are then traded on run
period 1 (which is Out-of-Sample). At the end of run period 1 it re-optimizes on period 2 and trades
period 2, and so on to the end of the data. This simulates how you would actually work with a
strategy live — optimize, trade, periodically re-optimize.

**Walk-Forward Matrix** runs a whole series of WFOs with different numbers of re-optimization periods
(runs) and different Out-of-Sample %, producing a matrix / 3D score surface across all combinations.

## What weakness it exposes

**Fragility under periodic re-optimization and over-optimization.** If the re-optimized strategy
performs *worse* than the original non-optimized version, that is a strong curve-fitting warning. The
Matrix additionally exposes strategies that only work for one specific re-optimization setting: a
robust strategy should keep its profitability across a *range* of re-optimization periods and history
lengths, showing gradual (not abrupt) changes across the score surface.

## How to configure it

- **Optimization values** — pick the parameters to optimize (Start / Stop / Step per parameter);
  the Number of tests shows how many combinations will run.
- **Out of Sample %** — how much of each period is used for the run part vs optimization (e.g. 30%
  run / 70% optimize).
- **Walk-Forward Runs** — how many re-optimization steps. Periods can also be defined by an exact
  number of days.
- **Matrix:** define ranges (Start / Stop / Increment) for both runs and OOS % (e.g. 5–15 runs,
  20–40% OOS). A *Simulation* WF mode can speed computation up 10–100×.
- **Robustness score** — a fully customizable set of score components with boundary values; the
  score threshold sets how many components must pass for a single WF run to count as successful.

## How to read the result

- A single WFO passes if enough Robustness-score components pass its threshold. Blue line = reoptimized
  strategy, gray line = original; reoptimized clearly beating original means the strategy benefits
  from optimization and can adapt to market changes.
- In the Matrix, look for as many successful combinations as possible. A common rule of thumb: at
  least one 3×3 cluster of combinations where a majority pass (e.g. 7 of 9) marks the strategy as
  robust. The center of such a cluster also suggests the optimal re-optimization period.

## Related

- Sibling: [In-Sample / Out-of-Sample](in-sample-out-of-sample.md) · [Multi-Market test](multi-market.md)
- [Cross-checks settings](../settings/cross-checks.md)
- [Retester](../retester.md) · [Retest strategies task](../tasks/retest-strategies.md)
- [Robustness Tests results tab](../results-tabs/robustness-tests.md)
- [Concepts](../concepts.md)
