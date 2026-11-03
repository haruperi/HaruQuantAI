# Robustness Tests — Results tab

> Shows the outcome of Monte Carlo simulations run on the strategy: bands of possible equity outcomes, confidence levels for each metric, and the risk of ruin.

## What it shows

The Robustness Tests tab displays the results of Monte Carlo (MC) cross-checks applied to a strategy. Instead of a single equity curve it shows the *distribution* of outcomes produced by many randomized simulations:

- **RT chart** — the simulated equity paths / bands drawn together, so you can see the spread of possible outcomes rather than one line.
- **Confidence levels** — for each metric, the value you can expect at a given probability. Only the confidence levels 50, 60, 70, 80, 90, 92, 95, 97, 98, 99, and 100 produce results; other levels return nothing.
- **Risk of ruin** — the probability that the strategy loses a defined portion of the account across the simulations.
- **RT views** — configurable views/columns over the simulation statistics.

## How it works

Monte Carlo tests simulate a large number of random scenarios to gauge how stable a strategy is when conditions vary. StrategyQuant X offers two families of Monte Carlo simulation, and the tab reports the confidence levels and risk of ruin derived from whichever were run:

- **Monte Carlo trade manipulation** — works on the existing trades from the main backtest (no re-backtest, so it is fast). Methods include *Randomize Trades Order* (reshuffles trades; net profit is unchanged but drawdown varies) and *Skip trades randomly* (drops trades with a set probability, mimicking missed trades in live trading).
- **Monte Carlo retest methods** — simulate changes that require a full backtest per simulation (so they can be slow). Methods include *Randomize Starting Bar*, *Randomize Strategy Parameters* (perturbs parameter values up to a max % change with a given probability), and *Randomize History Data* (perturbs OHLC prices; Max price change is expressed relative to ATR).

Across all simulations the tab collects the distribution of each metric and reports the value achievable at each supported confidence level (for example, "with 95% confidence the drawdown stays below X"), plus the risk of ruin. A robust strategy shows a tight band of outcomes and an acceptable ruin probability; a fragile one shows a wide spread.

## Options & settings

- **Confidence level selector** — read a metric at any of the supported levels (50–100 as listed above).
- **Chart controls** — the RT chart shows the simulated paths/bands for the equity outcomes.
- **Views** — switch or configure RT views/columns over the simulation statistics.
- **Which methods appear** — the confidence tables and risk-of-ruin figures reflect the Monte Carlo methods that were enabled for the run (trade manipulation and/or retest methods).

## Related

- Tab endpoint: `/rtresults/` (with `ConfidenceLevels`, `RiskOfRuins`, `RTChart`, `RTViews`)
- Retester module overview: [../retester.md](../retester.md)
- Results & Databank overview: [../results-databank.md](../results-databank.md)
- Sibling tab: [Walk-Forward](walk-forward.md) · [Optimization Profile](optimization-profile.md)
- Developer/architecture detail: [../../onboard/08-results/](../../onboard/08-results/README.md)
