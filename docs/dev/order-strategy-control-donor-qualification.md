# Order and StrategyControl donor qualification: formulas, sizing, ATM, and accounting

Date: 2026-10-28.

## Overview

This report qualifies the extended execution models of `app/include/blocks/order`
and `app/include/blocks/strategy_control` against donor StrategyQuant (SQX)
concepts, documenting formula evaluation, position sizing, ATM multi-exit
orchestration, bar-validity scheduling, and explicit accounting differences.

## 1. Position sizing selection (`order/sizing.py`)

In donor SQX, trade volume parameters accept formulas (`IFormula Size`).
The canonical Python library provides explicit, typed sizing formulas with
lot-grid normalization:

- **FixedLots**: Direct scalar volume clamped to `[min_lot, max_lot]` and rounded
  to `lot_step` using Decimal arithmetic to prevent floating-point drift.
- **FixedCashRisk**: Volumes derived from monetary loss limit:
  $$\text{volume} = \frac{\text{cash\_amount}}{\text{stop\_distance\_pips} \times \text{pip\_value}}$$
- **PercentEquityRisk**: Volumes derived from percentage of account equity:
  $$\text{volume} = \frac{\text{equity} \times (\text{risk\_pct} / 100)}{\text{stop\_distance\_pips} \times \text{pip\_value}}$$
- **PercentMargin**: Volumes sized to consume an exact margin fraction:
  $$\text{margin\_per\_lot} = \frac{\text{market\_price} \times \text{contract\_size}}{\text{leverage}}$$
- **VolatilityRisk**: ATR-based risk budgeting using volatility distance:
  $$\text{volume} = \frac{\text{cash\_risk}}{\text{atr\_value} \times \text{multiplier} \times \text{point\_value}}$$

## 2. Price formula evaluation (`order/formulas.py`)

Pending entry levels, stop losses, and profit targets support:
- Exact pip offsets (`price_offset_pips`).
- Volatility ATR multiple offsets (`price_offset_atr`).
- Price percentage offsets (`price_offset_percent`).
- Instrument tick-grid alignment (`normalize_price`) ensuring order prices align
  to `SymbolInfo.price.tick_step`.

## 3. Bar-validity scheduling (`order/validity.py`)

Pending orders in SQX can specify bar validity (e.g., valid for $N$ bars):
- Donor internal engines count completed bars internally using engine state cursors.
- HaruQuantAI translates discrete bar counts on chart timeframes ("M1", "M5", "H1",
  "D1", "W1") into explicit timezone-aware expiration timestamps (`schedule_bar_validity`).
- A value of $N \le 0$ indicates Good-Till-Cancelled (GTC), returning `None`.

## 4. Advanced Trade Management (ATM) multi-bracket exits (`order/atm.py`)

Supports multi-bracket execution strategies:
- Splitting total position volume across multiple targets (`ATMBracket`),
  conserving total volume and respecting broker lot steps.
- Per-bracket profit targets, initial stops, break-even trigger and offset distances,
  trailing stop distance and activation thresholds, and bar-count timeouts.

## 5. Accounting and history qualification differences

| Aspect | Donor SQX Semantics | HaruQuantAI Semantics |
|---|---|---|
| **Account Mode** | Assumes single-direction netting or engine-specific hedged modes depending on target platform export. | Explicit typed `TradeFilter(symbol, direction, magic)` isolating positions; long and short can coexist in hedged accounts. |
| **Trade Reconstruction** | Uses internal `ClosedTrade` records emitted upon order fill events. | Pure deterministic lifecycle reconstruction from immutable `HistoryDealsGet`, accurately apportioning swap, fees, and partial closes. |
| **Pip P/L Valuation** | Often hardcodes 0.0001 or 0.01 based on symbol naming heuristics (e.g. `JPY`). | Strictly requires instrument `tick_size` and `pip_size` from `SymbolInfo`. |
| **Order/Position Queries** | Modifies backend state or relies on mutable cursors (`OrderSelect`). | Pure, non-mutating snapshots. Bar counts require explicit evaluation times and monotonically increasing timestamps. |
| **Concurrency / Retries** | Synchronous blocking loops with implicit retry on broker busy. | Serialized via `asyncio.Lock` per executor (`operation_lock`); no implicit hidden retries. |
