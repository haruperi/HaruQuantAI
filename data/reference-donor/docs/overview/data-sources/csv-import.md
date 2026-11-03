# CSV / text file import — data source

> Import any history from delimited text files, with flexible column mapping and automatic
> timeframe detection.

## What it provides

The CSV / text importer brings history from **any delimited text file** into QuantDataManager.
It is the universal fallback: if you have price data in a CSV or text export from some other
tool, you can map its columns and import it. It handles both **bar (OHLC)** files and
**tick (bid/ask)** files.

## How to use it

1. In QuantDataManager, use the **Custom data / Files** import (the CSV importer).
2. Point it at your file. QDM reads the header and lets you **map each column** to a data field —
   date, date-time, time, open, high, low, close, volume, or bid/ask for tick files (unused
   columns can be ignored).
3. QDM **auto-detects the timeframe** from the spacing between rows; you can confirm or adjust
   the mapping and settings.
4. Confirm the import. QDM parses the rows, writes them to the shared data store, and registers
   the new symbol/timeframe so SQX can backtest on it.

For many files at once, the importer supports a **bulk / mass import** that processes files in
batch using the same mapping.

## Notes & limitations

- Column mapping is **flexible** — you choose which column is which — but the file must contain
  enough columns to reconstruct valid bars or ticks.
- Data quality depends entirely on your file; QDM imports what you give it (merging with existing
  data where applicable).
- Timeframe auto-detection is a best guess from row spacing — verify it if your data is irregular.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Export data back out to CSV: [export-formats.md](export-formats.md)
- Sibling sources: [MT5 import](mt5-import.md), [TD](td.md)
- Developer detail (import engine, column types, timeframe recognizer): [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
