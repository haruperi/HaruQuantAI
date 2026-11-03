# Practical guide: your first robust strategy, step by step

The hands-on version of [workflow.md](workflow.md) — concrete settings, starting thresholds and
the mistakes that cost people the most time. Where `workflow.md` says *what* each stage is for,
this page says *what to actually set*. Numbers here are **starting points to adapt**, not
universal truths.

> StrategyQuant X is a research tool, not a factory for guaranteed-profitable robots. Most of the
> work is not generating strategies — it is discarding them.

## 1. Prepare good data first

In the [Data Manager](../overview/data-manager.md):

- download or import the history, and check symbol, timeframe and **trading hours**;
- set **spread, commission, swap and slippage** as close to your broker as you can;
- for futures or broker-specific conditions use a **Broker Profile**.

A wrong spread, wrong session hours or poor data quality produces a strategy that looks good in
SQX and behaves differently in MetaTrader. Details and the reasoning:
[markets-and-costs.md](markets-and-costs.md).

## 2. Split the data into development and verification

Never build on the whole period. A workable split:

| Segment | Share | Purpose |
|---|---|---|
| In-Sample | 60–70 % | generating and shaping the strategy |
| Out-of-Sample | 30–40 % | independent verification |

With 2015–2025 data that is roughly IS 2015–2021, OOS 2022–2025.

**The OOS must not become the criterion you keep tuning against.** Every rebuild driven by an
OOS result burns a little more of it, and eventually you have overfitted to both halves
([overfitting.md](overfitting.md)).

## 3. Open the Builder and keep the first project simple

The [Builder](../overview/builder.md) generates candidates by random generation or genetic
evolution. For a first project:

- one market, one timeframe, **single-chart** strategy (not multi-timeframe or multi-symbol);
- a simple long **and** short strategy;
- at most **2–4 entry conditions**;
- a classic stop loss, plus a profit target or a time-based exit;
- no martingale, no aggressive position scaling.

Multi-timeframe and multi-symbol builds in *What to build* are a later step, not a first one.

## 4. Restrict the building blocks

Do not let the generator use every indicator and every rule type at once. Pick one small,
logical group, for example:

| Purpose | Blocks |
|---|---|
| Trend | EMA, SMA, ADX |
| Momentum | RSI, Stochastic |
| Volatility | ATR |
| Price action | Highest/Lowest, breakout |
| Timing | time / session filter |

The more combinations you allow, the higher the chance SQX finds a historical anomaly instead of
a real edge. The per-style shortlists are in [mean-reversion.md](mean-reversion.md),
[momentum-trend.md](momentum-trend.md) and [breakout.md](breakout.md).

## 5. Set ranking and minimum filters

The [Ranking](../overview/settings/ranking.md) tab holds the fitness function, how many
strategies to keep, and the conditions that discard weak candidates automatically. Reasonable
starting filters:

- at least **200–300 trades**;
- **Profit Factor** above ~1.2;
- a maximum drawdown you could actually sit through;
- consistent behaviour in In-Sample **and** Out-of-Sample;
- **Return/Drawdown** above ~1.5;
- no single trade contributing a large share of the profit;
- average trade comfortably above total costs.

These are not universal: 100 trades can be plenty for a daily strategy and far too few for an
M5 one. Scale the trade-count requirement to the timeframe.

## 6. Run the build, then choose carefully

Successful candidates land in the [databank](../overview/results-databank.md). Because SQX can
try an enormous number of rule combinations, **a good-looking backtest is not evidence by
itself** — see [overfitting.md](overfitting.md).

Do not simply take the highest profit. Prefer:

- a smoother equity curve;
- a sensible number of trades;
- decent results across different years;
- similar behaviour in In-Sample and Out-of-Sample;
- simpler rules;
- a drawdown you can survive.

## 7. Move candidates to the Retester

Send the selected strategies from the databank to the [Retester](../overview/retester.md) and
test them:

- on a different period;
- with a higher spread;
- with commission and slippage applied;
- on better-quality tick data;
- on related markets.

## 8. Run the robustness cross checks

The most important stage. [Cross checks](../overview/settings/cross-checks.md) exist in both the
Builder and the Retester, and they answer one question: does the strategy survive small changes
to data, parameters and trading conditions?

- **Monte Carlo — randomize history data**
- randomly skipping trades
- changed spread and slippage
- **Parameter permutation**
- **Higher backtest precision**
- **What-if simulations**
- **Multi-market test**

A robust strategy does not fall apart when one parameter moves slightly or a few trades are
skipped. Order them cheapest-first and dismiss on first failure —
[crosscheck-funnel.md](crosscheck-funnel.md).

## 9. Optimize carefully

In the [Optimizer](../overview/optimizer.md) you can optimize parameters, build an optimization
profile and run walk-forward analysis. Do **not** use it to find one perfect setting; look for a
broad stable band.

A strategy that works with EMA periods 35–55 is worth far more than one that works only at 47.

## 10. Read the strategy's logic before exporting

Open the rules in [AlgoWizard](../overview/algowizard.md) and check that the strategy:

- makes economic or market sense;
- does not rely on absurdly complicated conditions;
- does not enter right before the session ends;
- has realistic stop loss and profit target distances;
- does not use future or misaligned data.

If chart data saving is on, you can also inspect the trades directly on the chart.

## The funnel in numbers

A practical shape of the process — the exact numbers vary, the *ratio* does not:

```
10 000+ generated strategies
  → basic filters              →  ~500 candidates
  → out-of-sample test         →  ~100
  → Monte Carlo + permutation  →   ~20
  → high precision + platform test →  3–5
  → demo / forward test
  → 1–2 strategies live, with very small risk
```

## The most common mistakes

The biggest one is picking the most profitable equity curve and deploying it immediately. The
others:

- poor or different data;
- zero slippage;
- an unrealistically low spread;
- too many indicators;
- too few trades;
- optimizing against out-of-sample results;
- testing on a single market only;
- ignoring the differences between SQX and the broker's platform;
- going live without a forward test ([going-live.md](going-live.md)).

## Related

- [The trader's workflow](workflow.md) — the same journey at a conceptual level
- [The elimination method](elimination-method.md) — what each test asks and what disqualifies a candidate
- [Overfitting](overfitting.md) · [The cross-check funnel](crosscheck-funnel.md)
- [Risk and position sizing](risk-and-position-sizing.md) · [Going live](going-live.md)
