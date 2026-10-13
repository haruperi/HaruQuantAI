# AlgoCloud — the platform

Facts from the AlgoCloud website and help center, mirrored offline on 2026-08-07 into
[`site/`](site/) and [`help/`](help/). Quoted terms are the platform's own. For the
article-level sources see the offline index [help-center-map.md](help-center-map.md).

## What it is

A browser-based, no-code cloud platform for building, backtesting and **autonomously executing**
algorithmic strategies on **US stocks and ETFs, daily timeframe only**, through the user's own
connected brokerage account — no VPS, nothing installed. Positioning: "world-first platform
bringing stock-picking trading robots to retail traders". Claims: 2,000+ active users, 3,000+
symbols, 30+ years of history. Operated by AlgoWizardCloud LLC (same organization as
StrategyQuant; CEO & founder Mark Fric); sold separately from SQX.

## Core concepts

| Term | Meaning |
|------|---------|
| **Single-asset strategy** | Trades one stock symbol; optional **subcharts** ("trade AAPL and look at MSFT and GOOG"); Buy/Sell sections with entry conditions, order type (Market/Stop/Limit), exits (SL, PT, exit after N bars, End of day, exit-when-conditions); **Symmetrical Short** option mirrors the Buy side automatically. |
| **Stockpicker strategy** | The flagship: trades a **stock group** (e.g. S&P 500, Russell 3000). Long & Short rules are evaluated on ALL stocks in the group, candidates are ranked by the **Position score** formula, and only the top **Max positions** stocks are opened. Stated edge vs holding an index ETF: "limit your exposure and risk, and get better profit". |
| **Stock group** | The trading universe, managed in the **Data Manager**. Predefined groups are written `[[Name]]` (uneditable), custom groups `[Name]`. Custom members can carry add/remove dates (DD.MM.YYYY) — survivorship-bias-aware backtests. |
| **Position score** | "The criterium by which to sort which stocks to choose if there is more than [Max positions] stocks that could be opened at a given day." |
| **Paper vs Live account** | Live = the broker's real-money account. Paper = broker demo, or "our own AlgoCloud demo broker simulation" (real data feed, virtual money). |
| **Benchmark** | SPY buy-and-hold comparison in the equity chart, with normalization by Dollar drawdown / Percentage drawdown / Money management / Exposure (the last for seasonal strategies). |

(Marketing says "robots"; the help center consistently says "strategy" — same thing.)

## Workflow (the numbered Getting Started)

1. **Connect a broker** — one or more demo/live accounts; without one only AlgoCloud paper
   trading is available.
2. **Choose a strategy** — four sources: partner marketplaces (AlgoHubb), built-in examples
   (educational), build from scratch in the no-code **Strategy Editor**, or **generate with
   StrategyQuant X** and import (`My strategies → Import`). Validate with **Quick backtest**
   (last year) or **Full backtest** (30+ years, highest precision).
3. **Deploy** — 4-step wizard: Details (deployed name, account, main chart + subcharts, execution
   settings) → Money Management (fixed amount or % of balance; max open positions for
   stockpickers) → Checks & Verifications → Final Review (rules as "Pseudo code") → Start
   Strategy. Runs autonomously on "an institutional cloud with constant monitoring".
4. **Watch it trade** — Live trading section (Dashboard, Strategies, Open trades, Trade history,
   Equity, Trading log, Overview) + daily update e-mails with trades and full trading logs.

Execution model: "a classic trading platform, sending orders through the broker-provided API".

## Markets, data, timeframes

- US stocks (NYSE/NASDAQ/AMEX) and US ETFs (index, sector XL*, leveraged); European/global via
  Interactive Brokers (Beta). Groups incl. S&P 500, Russell 1000.
- **Daily (D1) only for live trading**; weekly/monthly in backtests. No native intraday. No
  futures/forex/options/crypto — except indirectly via **MTBridge** (MT4/MT5 bridge).
- 30+ years of history, ~3,000+ symbols; Available-symbols list carries exchange add/remove dates.

## Strategy engine & backtesting

- Editor building blocks: variables & inputs, input filters & conditions, candlestick patterns,
  conditions on multiple charts & timeframes, time conditions, strategy control conditions,
  market orders, PT/SL, money management.
- **Indicators are TA-Lib based** (SMA/EMA/…/KAMA/MAMA/T3, RSI/Stoch/MACD/CCI/ADX/…, ATR/BB/
  StdDev, OBV/AD/MFI, Hilbert set, ~60 TA-Lib candle patterns) + custom composites via math ops;
  non-TA-Lib indicators (Keltner, Donchian, TTM Squeeze) on request.
- Backtest precision = "Selected Timeframe" (daily bars). MM in backtests: "Risk fixed % of
  account" or "Fixed amount", both with fractional shares.
- **Execution timing** (deployment setting; D1 strategies trigger twice a day): **Before Bar
  Open** (evaluate on yesterday's data, orders placed pre-open; Close[0] = prior close), **On Bar
  Open**, **On Bar Close** (market orders ≈ 3:58 PM). Backtest timing should match deployment
  timing — results differ across timings.

## Brokers (help-center status, Aug 2026)

eToro (full), Alpaca.markets (full, real money), Tradestation (suited to $25k+ accounts),
Interactive Brokers (Beta, **US residents only** — IB's legal requirement), RoboMarkets (Beta),
Trading212 (Beta), XTB (beta), MTBridge for MT4/MT5 brokers. "Broker-agnostic — can work with all
brokers that provide a public API." US users get the full set; EU/Canada mostly eToro, IB or
MT4/MT5. Fractional shares vary per broker (IB: not on demo/API; Alpaca: market/day orders only;
Tradestation: none).

## Plans

Four paid tiers (30-day trial without card, 14-day money-back). Prices are deliberately not
kept in these docs — for current prices refer users to the AlgoCloud website pricing page.

| Plan | Backtests/day | Demo strategies | Real-money strategies | Open positions | AI credits/mo |
|---|---|---|---|---|---|
| Developer (no live) | 200 | 30/10 | 0 | 100 | 1 000 |
| Basic | 200 | 30/10 | 10/5 | 100 | 2 000 |
| Pro | 500 | 90/30 | 50/15 | 200 | 5 000 |
| Master | 1 000 | 300/60 | 150/30 | 400 | 10 000 |

> ⚠️ The help-center "Plans" article shows an older tier set (Free/Basic/Pro/Master with different
> numbers and a Full-vs-Quick backtest split) — when answering plan questions, prefer this table
> and say the help article may be stale. The meaning of the paired "30/10" counts and of
> "AI credits" is **not documented publicly** (unverified).

## Known gaps / unverified

- "AI credits" feature has no help-center article.
- Future brokers (Schwab/TDAmeritrade) are FAQ roadmap talk, not integrations.
- The "Introduction to Stockpicker strategies" article body did not render on fetch (headings
  only).
