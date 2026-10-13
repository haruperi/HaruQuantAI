# Dukascopy — data source

> Free forex / CFD tick history, downloaded over StrategyQuant's CDN.

## What it provides

Dukascopy is one of the most-used sources for **forex and CFD** history. It provides
**tick data** (individual bid/ask price changes), which is the highest granularity available
and gives the most precise, real-tick backtests. Ticks are aggregated into any timeframe
(M1, M5, H1, D1, …) when the data is stored and tested.

## How to use it

1. In the **Data** section of QuantDataManager, choose (or add) a **Dukascopy** connection.
2. Select the symbol(s) and the date range you want.
3. Click **Download** (or **Update** to extend existing data). The download runs through
   StrategyQuant's CDN queue.
4. QDM downloads the tick history, merges it with any data you already have, applies the
   configured timezone, and writes it to the shared data store — where SQX can immediately
   backtest on it.

## Notes & limitations

- Because Dukascopy is served through StrategyQuant's **CDN**, its downloads use the dedicated
  CDN queue rather than the general download queue; large tick ranges can take a while.
- Downloads are **incremental** — updating a symbol fetches only the missing data and merges
  it with what you have.
- The exact instrument list and available history depend on what Dukascopy publishes; QDM does
  not guarantee a fixed date range for every symbol.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [Darwinex](darwinex.md), [SQ data feeds](sq-data-feeds.md), [Yahoo](yahoo.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
