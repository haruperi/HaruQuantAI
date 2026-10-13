# Core Concepts

> Shared vocabulary for StrategyQuant X — the terms every other page in this overview assumes you already understand.

## Strategy

A strategy is a complete trading algorithm: a set of **IF–THEN** rules that decide when to open and close long and short positions. In StrategyQuant X a strategy is assembled from building blocks (indicators, price patterns, order types, trade-management commands) and is fully transparent — it can be viewed as readable pseudo code or exported to platform source code (MetaTrader 4/5 Expert Advisor, NinjaTrader NinjaScript, EasyLanguage). Every strategy consists of entry orders, exit orders, and optional trade-management logic such as trailing stops or moving the stop to break-even.

## Building block / indicator / signal

A **building block** is the smallest unit a strategy is built from. StrategyQuant X ships over 250 of them: technical **indicators** and oscillators (CCI, RSI, Stochastic, Momentum, ATR, MACD, …), price patterns, time values (time of day, day of week), logical/comparison operators (and, or, >, <), and order types. Blocks are combined into conditions, and conditions combine into a **signal** — a named true/false result such as `LongEntrySignal` that the entry and exit rules then act on. You can also author your own custom building blocks and indicators to extend the program.

## Strategy template

A strategy template is a strategy skeleton that leaves certain parts blank as **random placeholders**. When building, StrategyQuant X fills each `RandomCondition` placeholder with randomly generated blocks; a `NegatedCondition` placeholder is filled with the negation of a matching random condition (so the short side mirrors the long side). Templates let you control the overall "format" or architecture of the strategies being generated. Custom templates let you go beyond the built-in styles and generate strategies to your own design.

## Strategy style

The **style** is how a strategy's rules are structured. StrategyQuant X offers three predefined styles: the older *SQ3 style* (separate long/short entry and exit rules), the *SQ X new style* (a dedicated Signal rule computes all signals, and the entry/exit rules react to them — avoiding conflicts when long and short conditions fire together), and the *SQ X style with Fuzzy Logic* (the signal is treated as a vote — e.g. "70% of these conditions must be true" — instead of strict AND/OR). Style is distinct from a strategy's trading approach such as trend-following or mean-reversion, which emerges from the blocks and data used.

## Build mode (random vs genetic)

The **build mode** determines how the Builder searches the space of possible strategies. In **Random Generation** the Builder continually creates and backtests brand-new random strategies one after another until stopped; it is fast, simple, and less prone to overfitting. In **Genetic Evolution** the Builder starts from a random population and then evolves it toward better candidates. Random can run for days generating millions of candidates; genetic can refine already-good strategies but is slower and, being an optimization process, more prone to overfitting.

## Genetic programming

Genetic evolution applies genetic-programming ideas to trading strategies. An initial **population** of random strategies forms **generation** one; in each generation the algorithm keeps the fittest strategies (by the selected performance criteria) and uses them to produce the next generation via **crossover** (combining parts of two parent strategies) and **mutation** (randomly altering blocks or parameters). Over successive generations candidates should get better in the chosen criteria. Evolution stops when a target number of generations is reached or improvement stalls.

## Backtest

A backtest is a simulation of a strategy on historical market data, producing an equity curve and a full set of performance metrics. It is the primary way StrategyQuant X evaluates every generated or edited strategy. All performance numbers come from backtests, so they describe past behavior only and do not guarantee live results — which is exactly why robustness testing matters.

## In-sample vs out-of-sample (IS / OOS)

Historical data is split into two segments. **In-sample (IS)** data is used to develop, generate, and optimize a strategy. **Out-of-sample (OOS)** data is held back, unseen during development, and used only to validate the strategy on data it never "saw." A strategy that performs well on both IS and OOS data is far less likely to be overfit; the **OOS/IS ratio** measures how much performance deteriorates from the IS to the OOS period, flagging over-optimization when it drops sharply.

## Databank

A databank is the store where strategies (their backtests and results) are kept. The Builder automatically saves its top candidates to a databank so you can review, sort, and filter them later. In Custom Projects you can create multiple databanks and wire tasks to read from one (source) and write to another (target) — for example, feeding surviving strategies into a "Final" databank.

## Fitness / ranking

Ranking decides which strategies count as "best." You configure **Strategy Selection Criteria** (the fitness measure — e.g. Profit Factor, Return/Drawdown, Net Profit) that drives which candidates are kept during building and which survive genetic selection. Alongside ranking you set **Custom Conditions** — hard filters that discard strategies failing minimum thresholds (too few trades, too little profit, weak Profit Factor, low Return/DD, low SQN, etc.).

## Cross-check

Cross-checks are automated robustness tests applied to strategies. They can run during the build (filtering out weak strategies as they are generated) or later in the Retester. Because good strategies must survive scrutiny, cross-checks are how StrategyQuant X separates strategies with a real market edge from those that merely fit the history data — often only a tiny fraction of profitable candidates pass rigorous cross-checks.

## Robustness test

A robustness test checks whether a strategy still works when conditions change slightly. A robust strategy keeps performing when parameters, price data, spread/slippage, or the starting bar are perturbed, or when a few trades are missed — a fragile one breaks. StrategyQuant X's robustness toolkit includes IS/OOS testing, Monte Carlo simulations, multi-market tests (running the strategy on other instruments), and walk-forward analysis. The goal is to confirm the strategy has a genuine edge rather than a curve-fit equity curve.

## Monte Carlo

Monte Carlo testing runs many random scenarios to gauge how stable a strategy is. **Trade-manipulation** Monte Carlo works on the existing backtest trades (reshuffling their order, randomly skipping some) — it is fast and reveals how much results depend on trade order or on catching every trade. **Retest** Monte Carlo introduces random changes that require a full re-backtest each time — randomizing the starting bar, strategy parameters, or history data — and so is much slower but tests deeper sensitivities. Confidence levels are chosen from a fixed set (50, 60, 70, 80, 90, 92, 95, 97, 98, 99, 100).

## Walk-forward optimization (WFO) & WF Matrix

**Walk-forward optimization** is a backtest made of several smaller optimization-then-run periods. In each period the strategy is optimized on an in-sample slice, then traded forward on the following out-of-sample slice with those optimized parameters, and the window rolls forward. It simulates how you would periodically reoptimize a strategy in real trading, and it tells you whether the strategy is robust and whether it benefits from reoptimization — if the reoptimized version does worse than the plain one, that is a warning of curve-fitting. The **Walk-Forward Matrix** extends this by testing many combinations of reoptimization period and OOS size to find the best reoptimization schedule.

## Overfitting / curve-fitting

Overfitting (curve-fitting) is when a strategy is tuned so tightly to the historical data that its great backtest reflects noise rather than a real edge, and it fails on new data. It is easy to generate strategies with beautiful equity curves that are actually overfit — so generating a strategy is only about half the work; the rest is proving it is not curve-fit. IS/OOS testing, Monte Carlo, multi-market tests, and walk-forward analysis all exist primarily to detect and avoid overfitting.

## Portfolio

A portfolio combines several strategies so that their strengths offset each other's weaknesses. Strategies that perform consistently across multiple markets are prime portfolio candidates, and combining diverse strategies reduces overall risk and smooths returns. StrategyQuant X assembles portfolios with Portfolio Master (finding good combinations) and Portfolio Composer (composing and weighting them).

## Custom Project / task

A **Custom Project** is an automated pipeline that chains individual **tasks** into a repeatable workflow — for example: clear the databanks, build strategies, retest them several times with different settings, and drop the survivors into a Final databank. A task is a single unit of work (Build, Retest, Optimize, Go To Task, …). Projects support conditional loops: a *Go To Task* step can jump back to an earlier task until a condition is met (e.g. keep building until at least 100 strategies survive the whole workflow).

## Key performance metrics

These come from the backtest and describe past performance only:

- **Net / Total Profit** — total money made over the backtest.
- **Drawdown (absolute and %)** — the largest downswing of equity; the core risk measure.
- **Profit Factor** — gross profit divided by gross loss; roughly 1.3 or higher is a common minimum.
- **Return/DD ratio** — return weighed against drawdown risk; widely used for comparing strategies.
- **Sharpe Ratio** — return earned in excess of the risk-free rate per unit of volatility (risk).
- **Stability** — a proprietary linear-regression measure of how straight the equity curve is (1 = a perfectly straight rising line).
- **SQN / STR Quality Number** — Van Tharp's System Quality Number rating the quality of the system; **SQN Score** adjusts it for testing length and trade count.
- **Winning Percentage** — share of winning trades (typically 40–60%; a low % can still be fine with a good reward/risk).
- **Average Trade / Expectancy / R Expectancy** — expected profit per trade, the R-variants weighing it against risk (maximum potential loss).
- **CAGR / Yearly AVG % Return** — annualized appreciation of the account.
- **Exposure** — percentage of time the strategy holds a position.
- **Stagnation** — the longest period (in days or %) the equity spends without making a new high.
- **Symmetry** — how balanced profit and trade counts are between the long and short sides.

## Go deeper

- [Functional overview](README.md) — this overview set and how the modules relate.
- Module pages: [builder.md](builder.md) · [optimizer.md](optimizer.md) · [retester.md](retester.md) · [results-databank.md](results-databank.md)
