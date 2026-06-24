# MQL5-to-HaruQuant Translation Audit

## Scope and safety boundary

The five supplied Expert Advisors were translated into **strategy proposals**, not
broker-specific trading scripts.  Every strategy receives immutable `MarketContext`
snapshots and emits `TradeIntent` objects.  The Risk Governor remains responsible
for final quantity, portfolio limits, prop-firm constraints, margin checks, and
approval; the execution layer owns broker calls, fills, and reconciliation.

All bundled translations are configured for `SIMULATOR` and `PAPER` only.  They
must not be promoted to `LIVE` until the source-specific acceptance tests,
execution-adapter tests, and risk-policy review have passed.

## Runtime inputs required by the translations

| Strategy | Required inputs beyond completed main bars | Why |
|---|---|---|
| Decomposing Trade | `quote`, `account`, positions with entry/SL/TP/comment | Balance-scaled lots, adverse distance, trailing, partial close, basket TP |
| Harriet Hedging | `quote`, `account`, `chart_bars["H1"]`, positions | MTF structure confirmation, TP/SL modifications |
| Market Structure | `quote`, `account`, `features["zigzag_extremes"]`, positions, pending orders, execution events | External ZigZag structure, hedge/limit ladder, `OnTrade` logic |
| RandomWalk | `quote`, positions | Layered SL/TP basket launch |
| White Fairy | `quote`, `account`, positions, restart-safe state | Balance-sized basket, averaging and pyramiding levels |

## 1. Decomposing Trade EA.mq5

| Source behavior | HaruQuant translation |
|---|---|
| RSI(14) crosses upward oversold / downward overbought | `rsi_crosses()` produces deterministic completed-bar signal values |
| First buy/sell plus opposite-side seeding condition | `FBuy` and `FSell` market intents |
| Account-balance volume formula | `balance_scaled_volume()` advisory requested quantity; Risk Governor remains authoritative |
| Adverse movement plus RSI re-signal | `CBuy`/`CSell` open intent, partial-close intent for worst existing position, basket TP amend intent |
| Trailing only before `CBuy`/`CSell` appears | Per-position `MODIFY` stop intents gated by comments and activation distance |
| No signal exit | Preserved; exits are TP/SL/external risk/execution events |

## 2. Harriet Hedging EA.mq5

| Source behavior | HaruQuant translation |
|---|---|
| H1 and M5 higher-low/lower-high confirmation | Main bars plus named `chart_bars["H1"]` |
| `Bought` / `Sold` booleans | Serialized `StrategyState.custom` fields, reset under the same no-position rules |
| Fixed TP entries and concurrent hedging | `Buy`/`Sell` market intents with absolute TP requests |
| Two-plus basket average TP | A common arithmetic-average TP `MODIFY` intent |
| One-position structural trailing | Latest lower-timeframe completed low/high as amended SL |
| Chart drawing | Omitted deliberately: UI rendering belongs to the dashboard, not strategy decisions |

## 3. Market Structure EA.mq5

| Source behavior | HaruQuant translation |
|---|---|
| `Examples\\ZigZag` with eight nonzero points | Required `features["zigzag_extremes"]`, newest first; calculation is external by design |
| Bullish/bearish break pattern | Pure `_structure()` rule over supplied extremes and last two completed closes |
| First market leg and opposite hedge stop | `FirstBuy` + `HedgeSell`, or `FirstSell` + `HedgeBuy`, with source-derived targets |
| Saved next grid levels | Serialized custom state: `next_buy`, `next_sell`, and hedge distances |
| Source `OnTrade` callback | `evaluate_execution_event(context, event_id)` after execution reconciliation |
| Counter-average limit orders | `CABuy` / `CASell` limit intents on confirmed two-sided hedge state |
| Basket TP and opposite pending cancellation | `MODIFY` and `CANCEL_PENDING` intents |
| Orphan hedge/averaging cleanup | Reconciled pending-order cleanup intents |

## 4. RandomWalk EA.mq5

| Source behavior | HaruQuant translation |
|---|---|
| New M5 bar and empty buy magic | Opens `round(total_volume / volume_per_trade)` buy layers |
| Empty sell magic | Opens the same number of sell layers independently |
| Layered SL and TP distances | Each layer uses `n × stop_loss_pips` and `n × take_profit_pips` absolute price requests |
| Separate buy/sell magic numbers | Config declares both magic numbers and each intent retains its source magic |
| Randomness | None exists in the source; the Python docstring makes this explicit |

## 5. White Fairy EA.mq5

| Source behavior | HaruQuant translation |
|---|---|
| RSI initial buy/sell crosses | Deterministic completed-bar RSI crossing rules |
| First entry stores next counter/pyramid levels | Restart-safe `StrategyState.custom` values |
| Countertrend averaging on renewed RSI signal | `C.Averaging Buy/Sell` market intent and common arithmetic-average TP amendment |
| Favorable pyramid without a renewed RSI signal | `Pyrammid Buy/Sell` intent, progressively divided lot request, clear TP and shared SL amendment |
| No hard stop on number of additions | Preserved as source behavior; mandatory portfolio/risk limits are external |

## Deliberate non-equivalences and validation requirements

1. **MQL5 execution API calls are not copied.** `CTrade.Buy`, `PositionModify`,
   `OrderSend`, and `OnTrade` become typed proposals.  This is intentional so the
   same strategy can run in simulation, paper, MT5, cTrader, or another adapter.
2. **All prices require normalized bid/ask snapshots.** A strategy refuses to
   invent a current market price when its MQL source required one.
3. **ZigZag is injected, not reimplemented.** Confirm the feature producer against
   MetaTrader's `Examples\\ZigZag` before comparing backtest results.
4. **A source's strategy-level volume formula is advisory.** Final sizing may be
   reduced or rejected by the Risk Governor.
5. **Run parity tests before live use.** Compare serialized MQL5 and Python
   decisions bar-by-bar for the same historical data, spread model, point/pip
   convention, and position/account snapshots.
