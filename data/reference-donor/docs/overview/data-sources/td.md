# TD — data source

> A third-party data-feed connector built into QuantDataManager.

## What it provides

**TD** is one of the built-in data sources in QuantDataManager. In the available sources it is
a **third-party data-feed connector**: like the other download sources it plugs into QDM's
download/import machinery and writes into the same shared data store.

> The current documentation set does not describe TD's exact market coverage, instrument list,
> or granularity in detail. Rather than guess, this page keeps to what the sources state: TD is
> a third-party data feed, handled like the other sources through a file/import job.

## How to use it

1. In the **Data** section of QuantDataManager, choose (or add) a **TD** connection.
2. Select the symbol(s), timeframe, and date range as with any other source.
3. Click **Download** (or **Update**); QDM processes the data through its import job and writes
   it to the shared data store for SQX.

## Notes & limitations

- Details about TD's provider, coverage, and data granularity are **not documented** in the
  current sources — treat this page as a placeholder until confirmed.
- If you need broker-accurate or well-defined coverage, prefer a documented source such as
  [MetaTrader 5 import](mt5-import.md), [Dukascopy](dukascopy.md), or the
  [SQ data feeds](sq-data-feeds.md).

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [CSV import](csv-import.md), [MT5 import](mt5-import.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
