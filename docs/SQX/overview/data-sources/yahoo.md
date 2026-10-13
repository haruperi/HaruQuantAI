# Yahoo — data source

> Stocks and indices history from Yahoo Finance.

## What it provides

The Yahoo source pulls **stock and index** history from Yahoo Finance. It provides **bar
(OHLC) data** — end-of-day and intraday bars — rather than ticks. This makes it a convenient,
free way to get equity/index price history for backtesting, at the cost of the finer precision
that tick data would give.

## How to use it

1. In the **Data** section of QuantDataManager, choose (or add) a **Yahoo** connection.
2. Select the symbol(s) (e.g. a stock ticker or index) and the timeframe / date range.
3. Click **Download** (or **Update** to extend existing data).
4. QDM fetches the bars, merges them with existing data, applies the timezone, and writes them
   to the shared data store for use in SQX.

## Notes & limitations

- Yahoo data is **bar/OHLC**, not tick — backtests run on it use the coarser precision modes.
- Availability, history depth, and symbol coverage depend on what Yahoo Finance publishes and
  can change without notice; QDM does not guarantee a fixed date range per symbol.
- For broker-accurate forex/CFD data, prefer [MetaTrader 5 import](mt5-import.md),
  [Dukascopy](dukascopy.md), or [Darwinex](darwinex.md).

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [SQ data feeds](sq-data-feeds.md), [Dukascopy](dukascopy.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
