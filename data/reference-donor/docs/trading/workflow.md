# The trader's workflow in StrategyQuant X

The end-to-end journey a systematic trader walks with SQX — from raw data to a live
portfolio — and what each step maps to in the application. Terms used here are defined in
[`docs/overview/concepts.md`](../overview/concepts.md); each step links to the module page
with full detail. For the hands-on version — concrete settings, starting thresholds and the
usual mistakes — see [`practical-guide.md`](practical-guide.md); for the elimination procedure
behind it — what each test asks and what disqualifies a candidate — see
[`elimination-method.md`](elimination-method.md). Every step can also be driven by AI commands
through the [UI-action catalog](../ui/README.md) and [flows](../ui/FLOWS.md).

```
Data → 1 Build (one symbol) → 2 Validate on other markets → 3 Robustness tests → 4 Portfolio → Export
         ↑ style pages              Retester / rebuilds          cross-checks        Portfolio Master
```

This matches the vendor's official blueprint: *import data →
configure Builder → run build → evaluate → retest/optimize with more checks*, with two optional
tail steps — **improve** the survivors (the Improve-existing mode, historically called
"Improver") and **optimize** them last: simple optimization for parameters, then Walk-Forward
optimization to see whether periodic reoptimization helps, then Walk-Forward Matrix to pick the
reoptimization period.

## Step 0 — Have good data ([Data Manager](../overview/data-manager.md))

Everything downstream is a backtest, and a backtest is only as good as its data. In the
**Data Manager** you import and maintain instruments:

- **Forex/CFD** — free Dukascopy history (EURUSD, GBPJPY, GOLD, DJ/NQ CFDs, …);
- **Futures** — imports from TradeStation and file-based sources (this install's
  EW/NQ FUTURES projects use TradeStation data);
- **Stocks/ETFs, crypto** — Yahoo, TD, Darwinex, Binance/crypto and custom CSV imports.

Check the **from–to range** (you want years, covering different market regimes), the
timeframe you will trade (H1/H4/M30 are typical for FX/CFD systems), and set realistic
**spread, commission and slippage** — mean-reversion and breakout edges are especially
sensitive to fills ([markets-and-costs.md](markets-and-costs.md)). A trader command like *"import EURUSD H1 from Dukascopy"* maps to the
`dm.datasource-dukascopy.*` catalog refs.

## Step 1 — Generate strategies for one symbol ([Builder](../overview/builder.md))

Pick ONE market + timeframe you understand and generate candidates there:

1. **What to build** — choose the trading style you actually want, not "everything":
   [mean reversion](mean-reversion.md), [momentum/trend](momentum-trend.md) or
   [breakout](breakout.md). Each page lists the exact signal-block families to enable.
   Set **build mode**: *random generation* for a
   broad honest scan, *genetic evolution* to search deeper (more power, more overfitting
   risk — see [concepts](../overview/concepts.md#build-mode-random-vs-genetic)).
2. **Data** — select the symbol/TF and split history into **IS/OOS**
   ([in-sample-out-of-sample](../overview/robustness-tests/in-sample-out-of-sample.md));
   a common start is 70/30 with OOS at the end. The *data range parts* editor also supports a
   three-way **IST/ISV/OOS** split (in-sample training / in-sample validation / out-of-sample,
   "Most used configs" presets) — validation catches overfitting earlier than OOS alone.
3. **Money management** — *Fixed size* while researching, so candidates are comparable
   (`builder.settings.mm.use-fixed-size` flow). Real position sizing comes later, on the
   portfolio ([risk-and-position-sizing.md](risk-and-position-sizing.md)).
4. **Ranking** — set **Strategy Selection Criteria** (the fitness measure, e.g. Return/DD)
   and **Custom Conditions** (minimum trades, minimum Profit Factor, Return/DD, **SQN**) so
   the databank keeps only meaningful candidates ([stats-metrics](../overview/stats-metrics.md)).
   Generate at the fast *Selected timeframe* test precision — the
   [cross-check funnel](crosscheck-funnel.md) promotes survivors to higher precision later.
5. Set **stop conditions** (databank full / after N minutes / N strategies generated) and let
   it run; the best candidates land in the **Results databank**.

Light cross-checks during the build (MC retest with mild settings) keep junk out early;
heavy tests are better run afterwards on the survivors (see the
[Retester overview](../overview/retester.md) for this build-fast/test-later pattern).
Two power moves at this stage, both detailed in [strategy-refinement.md](strategy-refinement.md):
**templates + random groups** to control the exact strategy architecture, and the
**Improve existing strategy** mode to iterate on survivors instead of restarting from zero.

## Step 2 — Does the edge exist beyond your symbol?

A strategy that only works on GBPJPY H1 is probably fitted to GBPJPY H1. Two complementary
moves:

- **Retest on additional markets** — the [multi-market cross-check](../overview/robustness-tests/multi-market.md)
  backtests each strategy on related symbols/TFs (e.g. a GBPJPY system on GBPUSD, EURJPY,
  H4). Consistent profitability across related markets = transferable edge.
- **Re-generate on other symbols** — run the same build config on the next symbols
  (clone the project / `projects.tasks.ctx.clone-below`, change the Data tab symbol).
  Different symbols reward different styles — that is expected; what you are looking for
  is whether your *style + blocks* family keeps producing viable candidates.

Watch the **OOS/IS ratio** ([oos-is-ratios](../overview/robustness-tests/oos-is-ratios.md)):
sharp deterioration out-of-sample is the classic overfit signature — the other tells, and the
defenses that actually work, are in [overfitting.md](overfitting.md).

## Step 3 — Robustness: try to kill the strategy ([Retester](../overview/retester.md))

Only strategies that survive deliberate attack deserve real money. Run the heavy
[robustness tests](../overview/robustness-tests/README.md) on the filtered set:

| Test | Question it answers |
|------|----------------------|
| [Monte Carlo trade manipulation](../overview/robustness-tests/monte-carlo-trade-manipulation.md) | Does the result depend on trade order / catching every trade? (fast) |
| [Monte Carlo retest methods](../overview/robustness-tests/monte-carlo-retest-methods.md) | Does it survive randomized parameters, start bar, data perturbation? (slow, deep) |
| [Higher precision retest](../overview/robustness-tests/higher-precision.md) | Does it survive tick-level simulation instead of the build's approximation? |
| [What-if](../overview/robustness-tests/what-if.md) | Does the edge survive without the best trades (exclude N biggest winners), on fixed 0.01 lots, or trading only certain days/hours? An outlier-dependency check. |
| [Walk-forward + WF Matrix](../overview/robustness-tests/walk-forward.md) | Does periodic reoptimization help or reveal curve-fitting? |
| Sequential optimization / System Parameter Permutation | Is the parameter neighborhood stable, or is your setting a lucky spike? |

Rule of thumb: at each stage expect to throw most candidates away — passing rigorous
cross-checks is *supposed* to be rare ([concepts → cross-check](../overview/concepts.md#cross-check)).
Order the tests cheapest-first and dismiss on first failure — the economics and the
recommended ordering are in [crosscheck-funnel.md](crosscheck-funnel.md).
Survivors go to a dedicated databank (e.g. "Robust").

## Step 4 — Assemble the portfolio ([Portfolio Master](../overview/portfolio-master.md))

Individually good strategies are not yet a portfolio — what matters is how their equity
curves combine:

- Feed the "Robust" databank into **Portfolio Master**; it searches strategy
  *combinations* (brute-force for small pools, genetic for large ones).
- Cap **pairwise correlation per period** (Day/Week/Month/Year each with its own threshold)
  so drawdowns don't cluster; tag strategies with **sector notes** and cap same-sector members
  (this is why Step 2's multi-symbol work matters — it feeds uncorrelated candidates).
- Score with portfolio-level fitness (Return/DD of the combined curve), then **retest the
  final portfolio** as a whole.
- Weighting alternative: [Portfolio Composer](../overview/portfolio-composer.md) assigns
  per-strategy **weights**, manually or by automatic search over Sharpe / Return-DD /
  CAGR-MaxDD fitness.

Full mechanics — correlation settings, sector caps, fit-to-existing-portfolio during the
build, merge/split — in [portfolio-construction.md](portfolio-construction.md).

Finally set real **money management** per strategy (risk-based sizing instead of the
research-time fixed size) and export via the [export engines](../overview/export-engines/README.md)
(MT4/MT5 Expert Advisors, TradeStation, NinjaTrader, …) — or package a strategy as a sellable
EA through the Business Module ([strategy-refinement.md](strategy-refinement.md#packaging-for-sale-business-module)).

## Step 5 — Trade it ([going-live.md](going-live.md))

Export is not the finish line: forward-test on demo or minimum size (the only data that was
never used for selection), add the strategy to the portfolio at reduced size, and fix the
monitoring and retirement rules *before* the first drawdown rather than during it.

## Automating the loop ([Custom Projects](../overview/custom-projects.md))

The whole pipeline above is repeatable as a **Custom Project**: chained tasks
`Build → Retest (MC) → Retest (multi-market) → filter → Final databank`, each reading from
the previous task's databank. A vendor-recommended chain: a *random-generation* build task
feeding a *genetic-evolution* one — the random survivors become the genetic build's initial
population ([concepts → Build mode](../overview/concepts.md#build-mode-random-vs-genetic)). The user's existing projects (GBPJPY BREAKOUT H1, GOLD
BREAKOUT M30, NQ CFD H1, …) are exactly this pattern — one project per symbol/style.
A trader command like *"clone the GBPJPY project for EURJPY"* maps to
`projects.list.ctx.clone` + `projects.list.ctx.modify-symbols`.

## Driving all of this by AI commands

Every step is addressable through the [UI-action catalog](../ui/README.md): single
commands (`squi.invoke`) and multi-step intents ([flows](../ui/FLOWS.md)); the style pages in
this folder say which settings a given trading intent implies. The executable proof lives in
`tests/ui/specs/ai-control/` — its scenario ladder covers this workflow from "open the
retester" up to "configure a mean-reversion build".
