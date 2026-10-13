# Trading knowledge base

**Trading knowledge for the SQAI assistant and the AI-control tests**: how a systematic trader
works, what the common strategy styles are, and — crucially — **how each idea maps onto
concrete SQX settings** (build mode, building blocks, money management, cross checks). This is
the bridge between a user intent like *"generate mean reversion strategies"* and the UI-action
catalog ([`docs/ui/`](../ui/README.md)) that actually drives the app.

**The process**

| Page | Content |
|------|---------|
| [`workflow.md`](workflow.md) | **The trader's journey** — data → build for a symbol → validate on other markets → robustness → portfolio → export, mapped to SQX modules |
| [`practical-guide.md`](practical-guide.md) | **Step by step, hands-on** — what to actually set in each stage, starting filter thresholds, the funnel in numbers, the most common mistakes |
| [`elimination-method.md`](elimination-method.md) | **The method itself** — edge family first, three data segments, parameter plateaus, Monte Carlo per question, the frozen-strategy test: what disqualifies a candidate |
| [`markets-and-costs.md`](markets-and-costs.md) | Instrument classes, data quality, spread/commission/slippage, test precision and fills |
| [`overfitting.md`](overfitting.md) | Curve fitting vs data-mining bias, the tells, what actually defends against them |
| [`crosscheck-funnel.md`](crosscheck-funnel.md) | Filtering funnel Basic→Standard→Extensive, cost economics, precision ladder, Builder-filters vs Retester-annotates |
| [`risk-and-position-sizing.md`](risk-and-position-sizing.md) | Risk per trade, drawdown math, research vs live sizing, portfolio-level exposure |
| [`portfolio-construction.md`](portfolio-construction.md) | Portfolio Master constraints (per-period correlation, sector caps), Composer weights, fit-to-existing-portfolio |
| [`going-live.md`](going-live.md) | Forward testing, deploying as a portfolio member, monitoring, retirement rules, operational risk |

**Strategy styles and shaping**

| Page | Content |
|------|---------|
| [`mean-reversion.md`](mean-reversion.md) | Mean reversion: what it is, which SQX blocks express it, recommended setup |
| [`momentum-trend.md`](momentum-trend.md) | Momentum / trend following: idea, blocks, setup |
| [`breakout.md`](breakout.md) | Breakout: idea, blocks, setup |
| [`strategy-refinement.md`](strategy-refinement.md) | Templates & random groups, improve-existing mode, ATM staged exits, parametrization, Stockpicker, Business Module |

Vocabulary (strategy, building block, IS/OOS, Monte Carlo, walk-forward, databank, …) is
defined once in [`docs/overview/concepts.md`](../overview/concepts.md) — these pages link
into it rather than redefining terms.

## Official SQX term map

Vendor terminology (from the official StrategyQuant documentation, absorbed into this repo's
knowledge base) → where each concept lives:

| Official term | Meaning in one line | Covered in |
|---|---|---|
| Strategy Selection Criteria | the fitness measure that ranks candidates (Net profit, Return/DD, …) | [workflow](workflow.md) Step 1 |
| Custom Conditions | hard accept/reject filters (min trades, Profit Factor, Return/DD, SQN) | [workflow](workflow.md) Step 1 |
| SQN — System Quality Number | Van Tharp's expectancy/variability score, a standard filter metric | [overview/stats-metrics](../overview/stats-metrics.md) |
| Test precision ("Selected timeframe" → M1 → real tick) | speed/accuracy ladder of the backtest engine | [crosscheck-funnel](crosscheck-funnel.md) |
| Cross checks: Basic / Standard / Extensive | cost tiers; applied cheapest-first, dismiss on first failure | [crosscheck-funnel](crosscheck-funnel.md) |
| Random Generation vs Genetic Evolution | brute sampling (less overfit-prone) vs evolved search (stronger, riskier); random output can seed a genetic build's initial population | [workflow](workflow.md), [overview/concepts](../overview/concepts.md#build-mode-random-vs-genetic) |
| Strategy style (SQ3 / SQ X signal rule / Fuzzy) | how IF-THEN rules are wired; fuzzy = N-of-M voting signal | [strategy-refinement](strategy-refinement.md) |
| Improver ("Improve existing strategy") | mutate only selected parts of survivors (entries, exits, ATM) | [strategy-refinement](strategy-refinement.md) |
| ATM / scale-out, Exit scenarios | staged partial exits; 7 predefined split scenarios; Generate ATM randomizes them | [strategy-refinement](strategy-refinement.md) |
| Existing portfolio (databank) | pool your live strategies to filter/score new builds against | [portfolio-construction](portfolio-construction.md) |
| Strategy Selection via portfolio fitness (`Use = Existing portfolio`) | score candidates by the combined portfolio's performance | [portfolio-construction](portfolio-construction.md) |
| Walk-Forward Optimization / Matrix | does reoptimization help / which reoptimization period is best — the *last* workflow step | [overview/robustness-tests/walk-forward](../overview/robustness-tests/walk-forward.md) |

## How this knowledge is used

The assistant reads these pages to turn a spoken intent into a configuration:

1. **Intent → page.** *"chcem mean reversion strategie"* → [mean-reversion.md](mean-reversion.md);
   *"otestuj robustnost"* → [crosscheck-funnel.md](crosscheck-funnel.md);
   *"zostav portfolio"* → [portfolio-construction.md](portfolio-construction.md).
2. **Page → settings.** Each style page names the build mode, money-management method, the
   signal-block families to enable and which cross checks matter for that style.
3. **Settings → actions.** Those settings are reached through the
   [UI-action catalog](../ui/README.md) — single commands (`squi.invoke`) and multi-step
   [flows](../ui/FLOWS.md) such as `builder.settings.mm.use-fixed-size`.

Block-family names in the style tables are the **visible names in the Builder's Signals grid**,
so they can be matched by substring — `RSI` selects the whole RSI family rather than one block.

`tests/ui/specs/ai-control/` proves the command path itself works end to end against live SQX
(navigate, change settings, run a robustness pass, clone a project for another symbol).

## Editing rules

- Keep the trading claims **basic and uncontroversial** — this is a configuration map plus
  standard practice, not trading advice. Deeper product knowledge belongs in
  [`docs/overview/`](../overview/README.md).
- Every flow/ref mentioned must exist in the catalog — `node docs/ui/tools/validate-flows.js`
  and the ai-control suite both check this.
- Block names must match the **visible grid names** (probe the live grid, do not guess).
