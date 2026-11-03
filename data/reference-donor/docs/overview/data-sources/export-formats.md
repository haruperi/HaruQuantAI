# Export formats — writing data back out

> Export the data you have managed in QDM to MetaTrader formats and to configurable CSV.

## What it provides

QuantDataManager is not only for bringing data in — it can also **write data back out**, so you
can feed the clean history you have built into MetaTrader or other tools. Three export targets
are available:

- **MT4** — MetaTrader 4 history, written as **FXT / HST** files.
- **MT5** — MetaTrader 5 export.
- **CSV** — configurable delimited text export.

## How to use it

1. In the **Data** section of QuantDataManager, select the symbol(s) / timeframe you want to
   export.
2. Choose the export target — **MT4 (FXT/HST)**, **MT5**, or **CSV**.
3. For CSV, configure the format (columns, separators) as needed; for MT4/MT5, QDM writes the
   files in the format the terminal expects.
4. Run the export. QDM writes the output files, which you can then place where MetaTrader or the
   other tool expects them.

## Notes & limitations

- **MT4** export produces **FXT / HST** files (the format MT4 uses for its own history/testing);
  **MT5** has its own export.
- **CSV** export is **configurable** — you control the column layout and separators.
- Export writes out data already in your shared data store; the quality of the export is the
  quality of the source data.

## Related

- [Data Manager (QDM)](../data-manager.md)
- [Data settings panel](../settings/data.md)
- Import counterparts: [CSV import](csv-import.md), [MT5 import](mt5-import.md)
- Developer detail (`MT4ExportJob`, `MT5ExportJob`, `CsvExportJob`): [../../onboard/02-qdm/](../../onboard/02-qdm/README.md)
