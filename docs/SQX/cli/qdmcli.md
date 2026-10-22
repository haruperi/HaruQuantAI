# qdmcli — QuantDataManager CLI

> Run QuantDataManager headless to manage market data: add/edit/delete symbols and instruments,
> update/import/export/clone price data, and manage broker profiles — from scripts.

Parent: [CLI overview](README.md)

## Launch & entry point

```bash
launchers/qdmcli                                 # interactive prompt
launchers/qdmcli --args="-symbol action=list"    # one-shot command
```

- Launcher `qdmcli.bat` / `qdmcli.sh` runs Gradle task `:QuantDataManager:runCli`.
- Main class `QDMConsoleStarter.main()` calls `QuantDataManagerApp.main(args, true)` — console mode,
  no window.
- `QuantDataManagerApp` creates a `QDMConsole` and calls `consoleApp.run(appArgs)`.
- `QDMConsole` is a thin subclass of `ConsoleImpl` that only sets the app name/exe name — it adds
  **no** commands of its own. So qdmcli's command set is exactly the shared `ConsoleImpl` command
  set (the StrategyQuant-only `-project` / `-databank` / `-tools` / etc. are **not** available here).

> Source: `QDMConsoleStarter.main()`; `QuantDataManagerApp` (`new QDMConsole()`);
> `QDMConsole` (just `super("QuantDataManager", "qdmcli")`); command loop in `ConsoleImpl.runCommand()`.

Startup modes and argument syntax are identical to sqcli — see
[sqcli · Startup modes](sqcli.md#startup-modes) and [Argument syntax](sqcli.md#argument-syntax)
(both live in the shared `ConsoleImpl`).

## Commands

All commands below are confirmed in `ConsoleImpl`. Each `-command` takes an `action=…` selecting the
operation (there are also single-letter aliases that map directly to the same handlers).

### `-symbol` — manage symbols

> Source: `ConsoleImpl.symbol()` → `addSymbol()` / `editSymbol()` / `deleteSymbol()` / `clearSymbolData()` / `listSymbols()`

| action | Key params | What it does |
| --- | --- | --- |
| `list` | `csv` (optional) | List symbols. |
| `add` | `symbols`, `datasource` (default `dukascopy`), `datatype`, `bartype`, `postfix`, `broker`, plus source-specific params | Create/download symbols. Data sources handled in code: `dukascopy`, `file`, `darwinex`, `crypto` (`exchange`, `timeframe`), `yahoo`, `SQEquityData`, `mt5api` (`path` required, `datefrom`, `dateto` — see [MT5 import](#importing-from-metatrader-5) below). |
| `edit` | `symbol`, `name`, `instrument`, `barType` | Rename / re-tag a symbol. |
| `delete` | `symbols` | Delete symbols (and their History data). |
| `clear` | `symbols` | Clear a symbol's downloaded data. |
| `mt5symbols` | `path` | List the symbols a MetaTrader 5 terminal offers (name + category), read live from the terminal at `path` — the CLI counterpart of the import dialog's "Load available symbols". |
| `darwinexsymbols` | — | List the Darwinex tick-data symbols this license may download (symbol, first date, instrument type) — the names `add datasource=darwinex` accepts (e.g. `NDXm`, `GDAXIm`, `SP500`, `WS30`). |

Single-letter aliases: `-a` add, `-e` edit, `-d` delete, `-c` clear, `-l` list.

#### Importing from MetaTrader 5

> Source: `ConsoleImpl.addSymbol()` (`mt5api` branch) / `listMt5Symbols()` →
> `Program.get("DataSourceMt5Api")` (`DataSourceMt5ApiServlet`) → `Mt5ApiDownloaderJob` +
> `Mt5ApiManager` (drives `internal/python/scripts/mt5api.py` via the official `MetaTrader5`
> Python package).

The same import the Data manager's **Get data from MetaTrader 5** dialog runs — registering the
symbols (instrument created from the terminal's specification: tick size, point value, spread)
and downloading their history through a local MT5 terminal:

```bash
qdmcli.exe -symbol action=mt5symbols path=C:/MT5
qdmcli.exe -symbol action=add symbols=EURUSD,GBPUSD datasource=mt5api path=C:/MT5 datefrom=2020.01.01 dateto=2024.12.31
```

- `path` is **required** — the MT5 installation folder, and it must contain `terminal64.exe`.
  The terminal is started headless in **portable mode**; no MT5 window is needed.
- `datefrom`/`dateto` (`yyyy.MM.dd`) are optional — omitted, the **last year** is downloaded
  (`dateTo` = now, `dateFrom` = now − 1 year).
- Data arrives as **M1 bars** (the timeframe is fixed in the backend); MT5 downloads are
  **serialized** — one symbol at a time (`Queue`/`DownloadDispatcher`).
- An imported MT5 symbol **cannot be incrementally updated** later
  (`Mt5ApiDownloaderJob` refuses a symbol that already has data) — re-import with a wider
  range instead.

### `-instrument` — manage instruments

> Source: `ConsoleImpl.instrument()` → `addInstrument()` / `editInstrument()` / `deleteInstrument()` / `listInstruments()`

| action | Key params | What it does |
| --- | --- | --- |
| `list` | `csv` (optional) | List instruments. |
| `add` | `instrument`, plus `description`, `pointvalue`, `ticksize`, `tickstep`, `defaultspread`, `defaultslippage`, `datatype`, `broker`, `minDistance`, `orderSizeMultiplier`, `orderSizeStep`, `swap` (all optional, with defaults) | Add an instrument. |
| `edit` | `instrument` + any of the above to change | Edit an instrument's properties. |
| `delete` | `instruments` | Delete instruments. |

Single-letter aliases: `-ia` add, `-ie` edit, `-id` delete, `-il` list.

### `-data` — manage price data

> Source: `ConsoleImpl.data()`

| action | Key params | What it does |
| --- | --- | --- |
| `update` | `symbols` (optional; omit = update all), `datefrom`+`dateto` (`yyyy.MM.dd`), `overwrite` | Update downloaded data. **Without dates** the source decides the range — for a freshly added symbol that is its *entire* history (Dukascopy ticks ≈ 20 years). **With `datefrom`/`dateto`** exactly that window is downloaded (Dukascopy symbols only, see below). |
| `import` | `symbol`, `filepath`, `format`, `instrument`, `bartype`, `timeframe`, `timezone`, `errorhandling` | Import price data from a file (creates the symbol if missing). |
| `export` | `symbols`, `timeframe`, `outputdir`, `prefix`, `format`, `datefrom`, `dateto` (+ `cHeader`/`cFormat`/`cIncludeHeader` for `format=Custom`) | Export data to CSV. |
| `clone` | `symbols`, `timezone` or `hours`, `postfix`, `removeweekends` | Clone data into a different timezone. |
| `timezones` | — | List available timezones. |
| `exportToMT4` | `symbol`, `timeframe`, `appPath`, `dataPath`, `serverName`, `datefrom`, `dateto` | Export data into an MT4 installation. |
| `exportToMT5` | `symbol`, `timeframe`, `spreadType`, `spreadValue`, `outputdir`, `filename`, `datefrom`, `dateto` | Export data into MT5 format. |

Aliases: `-u` update, `-di` import, `-de` export, `-dc` clone, `-tz` timezones.

> **Downloading a bounded range** (`ConsoleImpl.updateRange()`). `-symbol action=add` only *registers*
> a symbol — it downloads nothing. The download is `-data action=update`, and by default it hands the
> source `dateType=sinceLast`, which for a symbol with no data yet resolves to the source's earliest
> available date. Passing `datefrom`+`dateto` instead calls the data source's `importData` command
> with an explicit range, so only that window is fetched. Bars vs ticks follow the symbol's registered
> timeframe (`-symbol action=add … datatype=TICK|M1`), not the update command.
>
> ```bash
> qdmcli.exe -symbol action=add symbols=EURUSD datasource=dukascopy datatype=TICK
> qdmcli.exe -data action=update symbols=EURUSD datefrom=2024.10.01 dateto=2024.11.01
> ```
>
> Currently implemented for **Dukascopy** symbols; other sources report that the range is unsupported.

### `-brokerprofile` — manage broker profiles

> Source: `ConsoleImpl.brokerProfile()`

| action | Key params | What it does |
| --- | --- | --- |
| `list` | — | List broker profiles. |
| `update` | `id` | Update data for one broker profile. |
| `updateAll` | — | Update data for all broker profiles. |
| `importstocks` | `id`, `filepath` | Import into a profile from a file. |
| `exportstocks` | `id`, `filepath` | Export a profile's list to a file. |
| `import` | `filepath` | Import a broker-profile definition (XML). |
| `export` | `id`, `filepath` | Export a broker-profile definition (XML). |

### `-license` — licensing

> Source: `ConsoleImpl.license()`

| action | Params | What it does |
| --- | --- | --- |
| `info` | — | Print license info (edition, type, licensee). |
| `update` | `code` | Verify/activate a license code. |

### Scripting & control

> Source: `ConsoleImpl` (`run()`, `execute()`, `waitFor()`, `deleteFile()`, `-gui` case)

| command | Params | What it does |
| --- | --- | --- |
| `-run` | `file` | Execute a text file of commands line-by-line (`#` lines are comments). |
| `-execute` | `file` | Run an external script/executable and wait for it to finish. |
| `-waitfor` | `action=user` or `action=file file=…` | Pause until the user presses ENTER, or until a file appears. |
| `-deletefile` | `file` | Delete a file (errors if it doesn't exist). |
| `-gui` | — | Start the CLI web server so the GUI can be accessed remotely; disables other CLI commands while active. |

### Help & exit

> Source: `ConsoleImpl.help()`, `ConsoleImpl.exit()`

| command | What it does |
| --- | --- |
| `-h` / `-help` / `help` | Print help (from `internal/web/<product>/help.txt`, with timeframe/format/exchange placeholders filled in). |
| `-exit` / `exit` / `quit` | Print "Bye", close output, exit the JVM. |
| `> path` | (parsed inside any command) redirect output to a file. |

## Not confirmable in code

- Any command **not** listed above (there are no QDM-only commands — `QDMConsole` adds none).
- The exact set of CSV export **format** names, crypto **exchanges**, and **timeframes** is generated
  at runtime (they fill the `#ExportAvailableCsvFormats#`, `#CryptoExchanges#`, `#AvailableTimeframes#`
  placeholders in `help.txt`), so run `-h` on a real install to see the current values.

## Related

- [sqcli.md](sqcli.md) — the StrategyQuant CLI (same shared commands + project/databank/tools).
- [commands-reference.md](commands-reference.md) — consolidated command table.
- [`../build-and-run.md`](../build-and-run.md) — launchers and `runCli` tasks.
