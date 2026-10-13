# Robustness Tests / Cross-checks — Detailed Reference

The **cross-checks** (robustness tests) StrategyQuant X can apply to a strategy to prove it is
resilient and not curve-fit. Each test has its own leaf page: **what it does**, **what weakness it
exposes**, and **how to configure it**.

These tests run in two places (same tests, different intent):
- In the **Builder** (Settings → [Cross-checks](../settings/cross-checks.md)) they act as **filters** —
  a strategy that fails is dropped during generation.
- In the **Retester** they run on demand to **annotate** existing strategies with extra results (or
  still filter). See [retester.md](../retester.md) and [tasks/retest-strategies.md](../tasks/retest-strategies.md).

Parent: [Retester](../retester.md) · [Cross-checks settings tab](../settings/cross-checks.md) · [Overview index](../README.md)

## Available tests

| Test | Exposes | Speed | Page |
|------|---------|-------|------|
| **In-Sample / Out-of-Sample (IS/OOS)** | Overfitting — does it work on unseen data? | fast | [in-sample-out-of-sample.md](in-sample-out-of-sample.md) |
| **OOS/IS Ratios** | How much performance decays out-of-sample | fast | [oos-is-ratios.md](oos-is-ratios.md) |
| **Monte Carlo — trade manipulation** | Luck vs. edge; drawdown variability (reuses existing trades) | fast | [monte-carlo-trade-manipulation.md](monte-carlo-trade-manipulation.md) |
| **Monte Carlo — retest methods** | Sensitivity to parameters, data, and start bar (full re-backtests) | slow | [monte-carlo-retest-methods.md](monte-carlo-retest-methods.md) |
| **Multi-Market test (additional markets)** | Curve-fitting to one instrument | medium | [multi-market.md](multi-market.md) |
| **Retest with higher precision** | Whether the fast backtest was reliable | slow | [higher-precision.md](higher-precision.md) |
| **Walk-Forward Optimization / Matrix** | Robustness under periodic re-optimization | slow | [walk-forward.md](walk-forward.md) |
| **What If simulations** | Effect of changed assumptions (spread, slippage, etc.) | fast | [what-if.md](what-if.md) |

## The robustness funnel

Cross-checks are usually applied in increasing cost order (Basic → Standard → Extensive): cheap
filters first to discard most strategies, then heavier full-backtest tests only on survivors. See
[cross-checks settings](../settings/cross-checks.md) and [../concepts.md](../concepts.md).

> Note: Monte Carlo retest methods only report at fixed confidence levels
> (50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100). Results appear in the
> [Robustness Tests results tab](../results-tabs/robustness-tests.md).
