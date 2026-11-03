# MetaTrader 5 import — data source

> Import broker-accurate history straight from a local MetaTrader 5 terminal.

## What it provides

Importing from a local **MetaTrader 5** installation is the fastest way to get
**broker-accurate** history — forex, CFD, index, stock, and futures data exactly as your broker
provides it. Because the data comes from the terminal you actually trade on, it best reflects
the prices, spreads, and instruments your live account would see.

## How to use it

1. Have MetaTrader 5 installed locally and the symbols you want loaded in its terminal (so the
   history is available on your machine).
2. In QuantDataManager, choose the **MetaTrader 5** (MT5 API) source and connect to the local
   terminal.
3. Select the symbol(s), timeframe, and date range.
4. Run the import. QDM pulls the history from MT5, merges it with any existing data, and writes
   it to the shared data store — immediately usable in SQX for backtesting.

## Notes & limitations

- Requires a **local MT5 terminal**; QDM reads what your broker has made available in that
  terminal, so coverage and history depth depend on your broker.
- The imported data is only as complete as what MT5 has downloaded locally — scroll the symbol's
  chart back in MT5 first if you need older history.
- This is an **import from a local install**, not an internet download source.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Sibling sources: [CSV import](csv-import.md), [Darwinex](darwinex.md), [Dukascopy](dukascopy.md)
- Export back to MT4/MT5: [export-formats.md](export-formats.md)
- Developer detail: [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
