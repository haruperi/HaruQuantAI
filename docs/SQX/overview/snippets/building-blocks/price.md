# Price — building block catalog

> Reference enumeration of the `Price` building-block snippets (30 classes): raw OHLC, Heiken Ashi,
> session levels, Ask/Bid/Spread, and Volume. This is a lookup table; for the general building-block
> model see [`README.md`](README.md).

## How this file is organized

All classes live in `SQ.Blocks.Price` and extend `ValueBlock` (they return a `double` from
`OnBlockEvaluate`). Every block reads price data through the `ChartData Chart` parameter and an
`int Shift` parameter (bars back); those two are omitted from the tables below since they carry no
numeric constraints and repeat on almost every block. Only parameters that meaningfully configure a
block (session start/end times, symbol) are listed. `SessionOHLCCalculator.java` is an internal
helper class shared by the four `Session*` blocks — it has no `@BuildingBlock` annotation and is not
a user-facing block, so it is omitted from the tables.

## Base OHLC

| Display name | Class | Description |
|---|---|---|
| (O) Open | `Open` | Open price of the bar (or current-symbol Stockpicker data). |
| (H) High | `High` | High price of the bar. |
| (L) Low | `Low` | Low price of the bar. |
| (C) Close | `Close` | Close price of the bar. |
| (V) Volume | `Volume` | Volume of the bar. |

## Multi-timeframe OHLC (Daily/Weekly/Monthly)

Same OHLC values, but aggregated to the daily/weekly/monthly bar containing the current bar
(useful for referencing higher-timeframe levels from a lower-timeframe chart).

| Display name | Class | Description |
|---|---|---|
| (DO) Daily Open | `OpenD` | Open of the current daily bar. |
| (DH) Daily High | `HighD` | High of the current daily bar. |
| (DL) Daily Low | `LowD` | Low of the current daily bar. |
| (DC) Daily Close | `CloseD` | Close of the current daily bar. |
| (WO) Weekly Open | `OpenW` | Open of the current weekly bar. |
| (WH) Weekly High | `HighW` | High of the current weekly bar. |
| (WL) Weekly Low | `LowW` | Low of the current weekly bar. |
| (WC) Weekly Close | `CloseW` | Close of the current weekly bar. |
| (MO) Monthly Open | `OpenM` | Open of the current monthly bar. |
| (MH) Monthly High | `HighM` | High of the current monthly bar. |
| (ML) Monthly Low | `LowM` | Low of the current monthly bar. |
| (MC) Monthly Close | `CloseM` | Close of the current monthly bar. |

## Heiken Ashi

Smoothed OHLC values computed from the Heiken Ashi candle formula rather than the raw chart.

| Display name | Class | Description |
|---|---|---|
| (HA O) Heiken Ashi Open | `HeikenAshiOpen` | Heiken Ashi open value. |
| (HA H) Heiken Ashi High | `HeikenAshiHigh` | Heiken Ashi high value. |
| (HA L) Heiken Ashi Low | `HeikenAshiLow` | Heiken Ashi low value. |
| (HA C) Heiken Ashi Close | `HeikenAshiClose` | Heiken Ashi close value. |

## Session levels

OHLC computed over a custom intraday time window ("session"), e.g. the London or New York session,
rather than a calendar day/week/month. Computed via the shared `SessionOHLCCalculator` helper.

| Display name | Class | Parameters | Description |
|---|---|---|---|
| (SO) Session Open | `SessionOpen` | StartHours: 0-23 (default 8); StartMinutes: 0-59 (default 30) | Open price at the start of the configured session window. |
| (SH) Session High | `SessionHigh` | StartHours: 0-23 (default 8); StartMinutes: 0-59 (default 30); EndHours: 0-23 (default 15); EndMinutes: 0-59 (default 15) | Highest price reached during the configured session window. |
| (SL) Session Low | `SessionLow` | StartHours: 0-23 (default 8); StartMinutes: 0-59 (default 30); EndHours: 0-23 (default 15); EndMinutes: 0-59 (default 15) | Lowest price reached during the configured session window. |
| (SC) Session Close | `SessionClose` | EndHours: 0-23 (default 15); EndMinutes: 0-59 (default 15) | Close price at the end of the configured session window. |

## Ask/Bid/Spread/Volume

Live quote-level values, sourced from `Strategy.MarketData` rather than the historical chart series.

| Display name | Class | Parameters | Description |
|---|---|---|---|
| (ASK) Ask | `Ask` | Symbol (default "Current") | Current ask price for the given symbol. |
| (BID) Bid | `Bid` | Symbol (default "Current") | Current bid price for the given symbol. |
| Spread | `Spread` | Symbol (default "Current") | Absolute difference between ask and bid. |
| Spread in pips | `SpreadInPips` | Symbol (default "Current") | Ask/bid spread converted to pips. |

## Related

- Building-block model overview: [`README.md`](README.md)
- Bar/time conditions these prices are often combined with: [`bar-and-time.md`](bar-and-time.md)
- Comparison operators (CrossesAbove/Below, IsGreater/Lower, etc.) used to build price rules: [`comparisons.md`](comparisons.md)
- Strategy/account state values (balance, position, order SL/PT): [`strategy-control.md`](strategy-control.md)
