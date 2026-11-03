# Darwinex — data source

> Forex / CFD historical data from the Darwinex broker.

## What it provides

Darwinex provides **forex and CFD** historical data sourced from the Darwinex broker. It is an
alternative broker-flavored source for forex/CFD instruments, useful when you want data that
reflects a real broker's feed.

## How to use it

1. In the **Data** section of QuantDataManager, choose (or add) a **Darwinex** connection.
2. Select the symbol(s), timeframe, and date range.
3. Click **Download** (or **Update** to extend existing data).
4. QDM downloads the history, merges it with any existing data, applies the timezone, and
   writes it to the shared data store for SQX to backtest on.

## Notes & limitations

- The exact instrument list and available history depend on what Darwinex publishes; QDM does
  not guarantee a fixed date range per symbol.
- Downloads are **incremental** — updating a symbol fetches only the missing data and merges it.
- For the most precise forex/CFD backtests, compare against tick sources such as
  [Dukascopy](dukascopy.md) or a broker's [MetaTrader 5 import](mt5-import.md).

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [Dukascopy](dukascopy.md), [Yahoo](yahoo.md), [MT5 import](mt5-import.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
