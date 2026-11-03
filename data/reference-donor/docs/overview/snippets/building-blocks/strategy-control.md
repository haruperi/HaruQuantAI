# StrategyControl — Building Block Catalog

> Reference enumeration of the `StrategyControl` building-block snippets (account state, market
> position, open/closed P/L, order SL/PT levels, pending-order and recent-close checks). This is a
> lookup table; for the general building-block model see [README.md](README.md).

## How this file is organized

Source: `work_directory/StrategyQuant/internal/extend/Snippets/SQ/Blocks/StrategyControl/`
(25 files). Value-returning blocks extend `SQ.Internal.ValueBlock` (`OnBlockEvaluate`); boolean
blocks extend `SQ.Internal.ConditionBlock` (`OnBlockEvaluate` returning `boolean`). All are
annotated `@IgnoreInBuilder` — they're used from the Wizard/manual-code editors rather than the
automatic Builder — and most also restrict themselves to certain trading engines via `@ForEngine`.

Nearly every block in this folder takes the same **order-identification parameters**, used to
locate the order(s) it acts on: `Symbol` (default `"Current"`), `Direction` (Long=1/Short=-1/Any=0,
omitted on blocks that are inherently directionless), `MagicNumber` (default references the
`MagicNumber` variable), and `Comment` (substring match). These are called out only where a block
has additional, block-specific parameters worth noting.

## Account state

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (ACB) AccountBalance | `AccountBalance` | Returns account balance in account currency. | None. |
| (ACC) AccountEquity | `AccountEquity` | Returns account equity in account currency. | None. |

## Market position

| Display name | Class | Description | Parameters |
|---|---|---|---|
| (MKT) MarketPosition | `MarketPosition` | Returns current market position direction (1 long / -1 short / 0 flat) for the first matching order. | Order identification (no `Direction`). |
| Market Position(...) Is Flat | `MarketPositionIsFlat` | True if no live (non-pending) order matches the criteria. | Order identification (no `Direction`). |
| Market Position(...) is Long | `MarketPositionIsLong` | True if the first matching live order is Long. | Order identification (no `Direction`). |
| Market Position(...) is Short | `MarketPositionIsShort` | True if the first matching live order is Short. | Order identification (no `Direction`). |
| Market Position(...) is Not Long | `MarketPositionIsNotLong` | True if there is no matching Long live order. | Order identification (no `Direction`). |
| Market Position(...) is Not Short | `MarketPositionIsNotShort` | True if there is no matching Short live order. | Order identification (no `Direction`). |
| MarketPositionSize | `MarketPositionSize` | Sum of size of all open positions matching the criteria. | Order identification (incl. `Direction`). |
| MarketPositionsCount | `MarketPositionsCount` | Number of open positions matching the criteria. | Order identification (incl. `Direction`). |

## Open / closed P/L

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Open P/L (in money) | `OpenPLInMoney` | Open P/L in money for matching order(s); sums all matches if none specified. | Order identification (incl. `Direction`). |
| Open P/L (in pips) | `OpenPLInPips` | Open P/L in pips for matching order(s). | Order identification (incl. `Direction`). |
| Closed P/L (in money) | `ClosedPLInMoney` | Last closed P/L in money for the matching order; 0 if not yet closed. | Order identification (incl. `Direction`) + `TradesAgo` — default 0, min 0, max 10000, step 1 (0 = most recent trade). |
| Closed P/L (in pips) | `ClosedPLInPips` | Last closed P/L in pips for the matching order. | Order identification (incl. `Direction`) + `TradesAgo` (same as above). |

## Order price levels

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Order Open Price | `OrderOpenPrice` | Open price of the matching order. | Order identification (incl. `Direction`). |
| Order Stop Loss | `OrderSL` | Stop Loss level of the matching order. | Order identification (incl. `Direction`). |
| Order Profit Target | `OrderPT` | Profit Target level of the matching order. | Order identification (incl. `Direction`). |

## Bars since / last order

| Display name | Class | Description | Parameters |
|---|---|---|---|
| BarsSinceOrderOpen | `BarsSinceOrderOpen` | Number of bars since the matching live order was opened; -1 if none found. | Order identification (incl. `Direction`). |
| BarsSinceOrderClosed | `BarsSinceOrderClosed` | Number of bars since the matching history order was closed; -1 if none found. | Order identification (incl. `Direction`). |
| Last order(...) was #Direction# | `LastOrderWas` | True if the last executed (filled) order matches the given `Direction`. | Order identification (no top-level `Direction` param — uses `Symbol`/`MagicNumber`/`Comment`) + `Direction` — Long=1/Short=-1, default 1. |
| Last order(...) was not #Direction# | `LastOrderWasNot` | True if the last executed order does not match the given `Direction`. | Same as `LastOrderWas`. |

## Pending orders

| Display name | Class | Description | Parameters |
|---|---|---|---|
| Pending order(...) exists | `PendingOrderExists` | True if a pending order matching the criteria exists. | Order identification (incl. `Direction`). |
| Pending order doesn't exist | `PendingOrderDoesntExist` | True if no pending order matches the criteria. | Order identification (incl. `Direction`). |

## Recently-closed trade guards

Used to filter overly frequent trading / improve backtest accuracy by checking whether a trade
just closed on the current bar or minute.

| Display name | Class | Description | Parameters |
|---|---|---|---|
| TradeRecentlyClosed | `TradeRecentlyClosed` | True if a matching trade closed on this bar and/or in the last minute. | `Symbol`, `MagicNumber` + `CheckThisBar` — bool, default true. `CheckThisMinute` — bool, default true. |
| NoTradeRecentlyClosed | `NoTradeRecentlyClosed` | Inverse of `TradeRecentlyClosed` (extends it); always true on the TradeStation engine. | Same as `TradeRecentlyClosed` (inherited). |

## Related

- Building blocks hub: [README.md](README.md)
- Order actions (open/close/modify orders whose state these blocks read): [`order-actions.md`](order-actions.md)
- Comparisons (used to build conditions around these values): [`comparisons.md`](comparisons.md)
- Functions (arithmetic/pip-conversion often applied to these values): [`functions.md`](functions.md)
