# The elimination method: how a candidate earns its place

A good strategy is **not found by looking for the prettiest equity curve**. It is what remains
after thousands of candidates have been eliminated for being sensitive to data, parameters,
costs or execution. The vendor says the same thing: generating is only half the work — the other
half is proving the result is not curve fitting and survives small changes to data, parameters,
spread and fills.

Where [practical-guide.md](practical-guide.md) says *what to set in each stage*, this page is the
**method itself**: what each test is actually asking, and what answer disqualifies a candidate.
Terms: [concepts](../overview/concepts.md). Numbers below are starting points to adapt, not rules.

## 1. Decide the edge family before you build

Before opening the Builder, name the market phenomenon you want to capture: trend following,
breakout, mean reversion, volatility expansion, pullback-in-trend, or a time/session effect. You
do not have to write the rules by hand — you have to stop the generator from combining everything
with everything.

A trend family, for example:

| Role | Allowed |
|---|---|
| Entry indicators | moving averages, ADX, price channels |
| Volatility filter | ATR |
| Entry order | market or stop |
| Exit | ATR stop loss, trailing stop, or a time exit |
| Excluded | oscillators whose purpose is mean reversion |

This shrinks the search space, which is the point: the more combinations SQX tries, the higher
the chance it finds a historical coincidence. The research definition of *Probability of Backtest
Overfitting* is exactly this — a configuration picked as best In-Sample that then performs below
median Out-of-Sample. Per-style shortlists: [mean-reversion](mean-reversion.md),
[momentum-trend](momentum-trend.md), [breakout](breakout.md).

## 2. Three segments, not two

A single IS/OOS split is better than nothing, but you can hit a favourable one by accident. Use
three separated parts:

| Segment | Share | Purpose |
|---|---|---|
| Development IS | ~60 % | generating and basic filtering |
| Validation OOS | ~20 % | choosing the more robust candidates |
| Final holdout | ~20 % | the very last test |

**Do not look at the final holdout during development.** The moment you change a filter or a
parameter because of what it showed, it stops being independent — see
[overfitting.md](overfitting.md).

The official example goes further with a *double OOS*: one OOS during generation and a second,
until-then-unused period at retest time, followed by a check on another symbol, the robustness
tests and the Walk-Forward Matrix.

## 3. The data must contain several regimes

The build period should include rising and falling markets, high and low volatility, calm and
crisis periods, different rate/macro regimes, and — for intraday — different liquidity
conditions.

Length alone is not enough: ten years of one regime can be less informative than a shorter span
containing several clearly different ones. Watch continuous-contract construction on futures and
indices, and broker-specific quotes, time zones and bar alignment on forex
([markets-and-costs.md](markets-and-costs.md)).

## 4. Build simple strategies

Complexity is one of the largest sources of overfitting. For a first version, cap it:

- 2–4 entry conditions;
- one or two filters;
- one main exit mechanism;
- few optimizable parameters;
- no extremely precise time or price conditions.

A suspicious strategy reads like *"RSI(17) < 28.3, ADX(23) > 19.7, time 10:35–13:10, ATR(31)
above an exact value, plus four more conditions."* A more robust one reads like *"price breaks
the 50-bar high, volatility is sufficient, the position is protected by an ATR stop."*

Simplicity does not make a strategy profitable. It gives it fewer ways to fit historical noise.

## 5. Do not over-filter inside the Builder

During generation use basic conditions only: a minimum trade count, positive profit after costs,
a maximum acceptable drawdown, a minimum average trade, a sane Profit Factor.
[Ranking](../overview/settings/ranking.md) can apply filters separately to IS, OOS, robustness
results and the portfolio.

Filtering too hard *while generating* is itself a form of optimization — the program then stops
looking for a strategy and starts looking for a strategy shaped to a long list of metrics.

As an orientation, not a universal rule:

- at least 150–300 trades;
- Profit Factor above ~1.15–1.25;
- average trade several times larger than realistic slippage;
- no extreme drawdown;
- profit not produced by a single period or a handful of trades.

Daily timeframes justify fewer trades; M5/M15 systems demand considerably more.

## 6. Generate a large and diverse pool

Do not hunt for one winning strategy — produce hundreds to thousands of candidates across
several separate runs:

1. run several builds of the same idea;
2. vary the random seed;
3. optionally vary the allowed blocks slightly;
4. keep a large enough pool;
5. remove duplicates and near-identical strategies.

The official example builds a large pool with genetic evolution and **restarts the evolution
periodically** so the population does not get stuck in one local solution
([genetic options](../overview/settings/genetic-options.md)).

## 7. Judge the distribution, not the total

For each candidate check the result per year and per month, the long and short side separately,
the trade count in each period, the best and worst 5–10 trades, the longest time without a new
equity high, the average trade, and drawdown in both money and percent
([stats-metrics](../overview/stats-metrics.md)).

The decisive question:

> Is the strategy still acceptable when I remove its five best trades?

If the whole profit disappears, the edge is either too weak or dependent on isolated events —
[What-if](../overview/robustness-tests/what-if.md) answers this directly.

Equally suspicious: 80 % of the profit made in one year; a brilliant long side with a disastrous
short side; long stagnations that the summary metrics hide; an average trade that is small
relative to costs.

## 8. Expect *proportionate* OOS degradation

The OOS does not have to beat the IS — an OOS that looks better is just as likely to be luck.
What you want is a similar equity character, still-positive expectancy, a survivable drawdown, a
sufficient trade count, and degradation that is reasonable rather than catastrophic. SQX's
[OOS/IS ratios](../overview/robustness-tests/oos-is-ratios.md) measure exactly that drop; a sharp
one points to overfitting or a regime change.

Do not spend the OOS on hundreds of repeated decisions. If you keep trying settings until the OOS
finally looks good, the OOS has effectively become training data.

## 9. Test parameter sensitivity — look for a plateau

One of the strongest tests. If a strategy uses EMA period 47, ATR stop 2.3 and breakout period
31, scan the neighbourhood (EMA ~35–60, ATR stop ~1.7–3.0, breakout ~20–45).

Good — a plateau:

```text
Parameter 42: PF 1.31
Parameter 45: PF 1.34
Parameter 47: PF 1.36
Parameter 50: PF 1.33
Parameter 54: PF 1.29
```

Suspicious — a lucky spike:

```text
Parameter 46: PF 1.06
Parameter 47: PF 1.68
Parameter 48: PF 1.02
```

The Optimization Profile and System Parameter Permutation exist for precisely this judgement:
does the strategy have a general edge, or does it work only at a narrow set of parameters? Pick
values from the **middle of the stable region**, not the absolute best cell
([Optimizer](../overview/optimizer.md)).

## 10. Split the Monte Carlo tests by the question they answer

| Method | The question it answers | Use it for |
|---|---|---|
| [Trade-order manipulation](../overview/robustness-tests/monte-carlo-trade-manipulation.md) | how else could this equity curve have unfolded? | realistic drawdown estimate, stagnation length, likely result range, position sizing |
| Randomly skipping trades | what if some trades never happen? | platform outage, latency, data differences, an unfilled limit/stop order |
| [Parameter randomization](../overview/robustness-tests/monte-carlo-retest-methods.md) | do small period/constant changes destroy the result? | curve-fitting check |
| History randomization | is the result tied to exact historical prices? | OHLC perturbed relative to ATR |
| Spread and slippage | does the edge survive worse fills? | normal costs, worse realistic costs, a stress scenario |

Trade manipulation tests dependence on trade *order* and on some trades not being executed;
retest methods each re-run the full backtest with perturbed inputs, which is why they are the
expensive end of [the funnel](crosscheck-funnel.md). A strategy that stops working after a modest
spread increase simply has too small an edge.

## 11. Retest at higher precision

Generate with a fast model, but retest the finalists on tick or the most precise data available,
with realistic spread, commission, slippage and swaps, the broker's trading hours, and the
platform's minimum stop distance and other constraints
([higher precision](../overview/robustness-tests/higher-precision.md)).

A fast backtest is a sieve, not a confirmation. Be especially careful with strategies using a
very tight SL or PT, limit orders, intrabar entries, a trailing stop, short timeframes, or a high
trade frequency.

## 12. Use the multi-market test sensibly

A multi-market test does not require the strategy to be excellent on every symbol. It asks
whether the strategy completely falls apart on comparable markets, whether the principle survives
different conditions, and whether the result is tied to one market's quotes
([multi-market](../overview/robustness-tests/multi-market.md)).

Sensible groups: EURUSD → GBPUSD / AUDUSD / USDCHF; DAX → Euro Stoxx 50; S&P 500 → Nasdaq 100 /
Russell 2000; gold → silver (as a supplementary test only). The official forex workflow generated
on EURUSD while checking GBPUSD — not to optimize both, but to filter out rules too specific to
EURUSD.

Do not turn an unrelated market into an automatic criterion: a mean-reversion strategy on an
equity index need not work on a trending commodity, and failing there proves little.

## 13. Use walk-forward only where it applies

[Walk-forward optimization](../overview/robustness-tests/walk-forward.md) fits strategies you
intend to reoptimize periodically. The WF Matrix varies the optimization-window length, the OOS
percentage and the number of reoptimizations.

Do not look for one successful cell — look for a **contiguous cluster** of successful
combinations. The documented example is a 3 × 3 region where most combinations pass; a gradually
changing surface is far more favourable than sharp isolated peaks.

Walk-forward is not mandatory for every strategy. If it has no parameters you plan to refresh, a
simple anchored or rolling OOS test is clearer.

## 14. The frozen-strategy test

After all adjustments:

1. freeze the rules **and** the parameters;
2. run no further optimization;
3. run the strategy on the final holdout period;
4. change nothing based on the result;
5. export it to the target platform;
6. compare the trades between SQX and the platform.

If the final holdout fails, discard the candidate. Do not go back and "fix" it against holdout
data — that converts your last independent sample into training data.

## 15. Measure the forward test in trades, not weeks

Track signal agreement with SQX, real slippage, the spread difference, missing trades,
differences in SL/PT, live drawdown against the Monte Carlo distribution, and whether the trade
frequency has changed materially.

A strategy taking two trades a month tells you almost nothing after three months of demo; the
same period on an intraday system can be quite informative. Operational detail:
[going-live.md](going-live.md).

## The funnel in numbers

The exact counts are not a rule. The point is that **each further test is harder and applied to
fewer candidates**:

```text
20 000–100 000 generated candidates
        ↓  basic IS filters + minimum trade count
1 000–3 000 strategies
        ↓  first OOS + duplicate removal
200–500 strategies
        ↓  precise retest + worse costs
50–150 strategies
        ↓  parameter permutation + Monte Carlo
10–30 strategies
        ↓  second OOS / final holdout + multi-market
3–10 strategies
        ↓  platform check + forward test
a small portfolio of uncorrelated strategies
```

## What raises quality the most

In rough order of value:

1. a simple, logical rule family;
2. several independent OOS periods;
3. realistic trading costs;
4. a stable parameter plateau;
5. randomization of parameters and of history data;
6. discarding strategies that depend on their best trades;
7. a test on a related market;
8. a completely untouched final holdout;
9. verification in the target platform;
10. a portfolio of several different edges instead of one "super robot".

None of this guarantees profit. Its purpose is to cut down the number of falsely good backtests
and to estimate future drawdown more realistically.

## Related

- [Practical guide](practical-guide.md) — what to set, stage by stage
- [Overfitting](overfitting.md) · [The cross-check funnel](crosscheck-funnel.md)
- [Markets and costs](markets-and-costs.md) · [Risk and position sizing](risk-and-position-sizing.md)
- [The trader's workflow](workflow.md) · [Going live](going-live.md)
