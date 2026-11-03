# Cross-checks — settings tab
> Optional robustness tests run on each strategy as it is generated, so fragile or curve-fitted candidates are automatically rejected before they reach the databank.

**Applies to:** Build & Retest — act as filters during Build; run for information (no filtering) in the Retester.

## What it configures

Cross-checks are optional, additional robustness tests applied to every strategy **after** it
is generated and passes the first (global) filters. Their purpose is to fight overfitting
(curve-fitting) — a strategy that looks great on the data it was built on but falls apart on
anything else. Each cross-check can act as a filter: if a strategy fails, it is dismissed and
never enters the databank. You choose which checks to enable and how strict each filter is.
The same cross-checks exist in the [Retester](../retester.md), where they can be run for
information without filtering — so you don't have to run every check during the (slower) build.

## Main options

Checks are grouped into **Basic**, **Standard** and **Extensive** tiers by how time-consuming
they are, and applied cheapest-first: a strategy dropped by an early check is never run
through a later one. This forms a **funnel** where survivors are scrutinized by progressively
heavier methods.

- **Retest with higher precision** — re-run the backtest at a more accurate precision
  (1-minute or real-tick) to confirm the fast-precision result during generation was reliable.
- **Monte Carlo — trade manipulation** — very fast (no re-backtest); reshuffles and randomly
  skips existing trades to see how much the equity curve depends on trade order and on not
  missing trades:
  - **Randomize trades order** — shuffle trade order (net profit unchanged) to study the range
    of possible drawdowns.
  - **Skip trades randomly** — randomly omit trades to model missed trades in real trading.
- **Retest on additional markets (multi-market)** — test the strategy on other symbols and/or
  timeframes; a strategy that only works on its build market is likely curve-fitted.
- **Monte Carlo — retest methods** — slow; each simulation is a full re-backtest with small
  random variations to check sensitivity:
  - **Randomize strategy parameters** — vary indicator periods/constants (by a probability and
    a max % change) to test parameter sensitivity.
  - **Randomize history data** — slightly alter the price history to test data dependence.
- **Out-of-Sample / OOS-IS ratio** checks — compare out-of-sample performance to in-sample to
  quantify deterioration on unseen data.

Each enabled check exposes its own filter thresholds; a strategy must pass all of them to be
kept.

## How it affects generation

Cross-checks make generation slower but the output far more trustworthy. Without any checks a
strategy might be generated and backtested in a fraction of a second; heavy checks (especially
Monte Carlo retest methods, which run hundreds of full backtests per strategy) can add tens to
hundreds of seconds per surviving candidate. Because they run as a cheapest-first funnel and
drop failures immediately, only the small fraction of strategies that clear the fast filters
pay the cost of the expensive ones — so the databank fills more slowly but with strategies
that have already demonstrated robustness across precision, trade order, other markets and
parameter variation.

## Related

- Settings index: [README.md](README.md)
- Parent: [../builder.md](../builder.md)
- Concepts (robustness, overfitting, In-sample vs Out-of-sample, Monte Carlo): [../concepts.md](../concepts.md)
- Retester (runs the same cross-checks, without filtering): [../retester.md](../retester.md)
- Each robustness test in detail: [../robustness-tests/](../robustness-tests/README.md)
- **Deep catalog (methods + settings for UI tests):** [../snippets/cross-checks.md](../snippets/cross-checks.md)
- Sibling panels: [data.md](data.md) · [ranking.md](ranking.md) · [trading-options.md](trading-options.md)
- Developer detail: [../../onboard/05-retester/README.md](../../onboard/05-retester/README.md) · [../../onboard/04-builder/README.md](../../onboard/04-builder/README.md)
