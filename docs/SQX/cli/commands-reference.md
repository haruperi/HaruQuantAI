# CLI Commands Reference

Every command confirmed in code. sqcli = StrategyQuant X, qdmcli = QuantDataManager. Shared
commands come from `ConsoleImpl`, sqcli adds the StrategyQuant-only ones from `SQConsole`. Names
and `action=` values are cross-confirmed against the official CLI reference; the code is a superset
(`-project action=startOnlyTask/startFromTask`, `-data action=exportToMT4/5`,
`-symbol action=mt5symbols/darwinexsymbols`, `-symbol datasource=SQEquityData`). Parent:
[README.md](README.md); detail and examples: [sqcli.md](sqcli.md), [qdmcli.md](qdmcli.md); the
`Program` registry the commands call: [`../onboard/04-applications.md`](../onboard/04-applications.md).

SQAI chat: the `run_cli_command` tool runs every command (same dispatcher, output returned) except
`exit`/`-gui`/`-waitfor`/`-execute`/`-run` and `-license action=update` (refused with a pointer
to the alternative); MT5 import also has `list_mt5_symbols` + `import_mt5_data`. See
[`../sqai/catalogs-and-data.md`](../sqai/catalogs-and-data.md#clitools--sqcli-parity).

## Argument value enums

`action=` lists are in the command tables below.

| Command | Key value enums |
|---|---|
| `-databank` | export `file=` ends `.csv`/`.xlsx`; `view=` for xlsx |
| `-portfolio` | `type=`[simulated,merged,signals]; `capital=`[first,sum] |
| `-data` | `bartype=`[startofbar,endofbar]; `timeframe=`[auto,Intraday,TICK,M1,M5,M15,M30,H1,H4,D1]; `errorhandling=`[stop,ignore] |
| `-symbol` | `datatype=`[M1,TICK]; `datasource=`[dukascopy,file,darwinex,crypto,yahoo,mt5api,SQEquityData]; `bartype=`[startofbar,endofbar]; `exchange=`(e.g. Binance); mt5api: `path=`(MT5 folder with terminal64.exe, required), `datefrom=`/`dateto=`(optional, default last year) |
| `-instrument` | `datatype=`[stock,futures,forex,cfds,etf,index,crypto]; defaults: pointvalue 100000, ticksize 0.0001, tickstep 0.00001, defaultspread 2 |
| `-tools` | `data=`[main,all]; `usecomma=`[true,false] |

`-data` needs existing symbols (`-symbol action=add` first). Runtime-dependent lists (CSV export
formats, crypto exchanges, exact timeframes) are in the install's live `-h` output.

## Dispatch

- sqcli: `SQConsole.runCommand()` handles StrategyQuant-only commands, then falls through to `ConsoleImpl.runCommand()`.
- qdmcli: `QDMConsole` adds nothing; `ConsoleImpl.runCommand()` dispatches directly.
- First token = command, then `key=value` pairs; `> path` redirects output (`ConsoleImpl.parseParams()` / `translateCommandline()`).

## StrategyQuant-only commands (sqcli)

| Command | Args (key=value) | Does | Source |
|---|---|---|---|
| `-project` | `action=`list/start/startOnlyTask/startFromTask/stop/pause/resume/remove/status/loadconfig/saveconfig, `name`, `task`, `file` | Start/stop/status projects, load/save config. | `SQConsole.project()` |
| `-databank` | `action=`list/count/load/save/delete/clear/create/remove/copy/move/synctofiles/syncfromfiles/export, `project`, `name`, `folder`, `strategies`, `destproject`, `destdatabank`, `file`, `view`, `position` | Manage a project's databanks, export contents. | `SQConsole.databank()` |
| `-portfolio` | `action=`merge/split, `project`, `databank`, `strategies`, `name`, `target`, `type`, `capital`, `signalspct`, `signalsstrategy` | Merge 2+ strategies into a portfolio strategy (synchronous) or split a merged portfolio back. | `SQConsole.portfolio()` |
| `-tools` | `action=`orderstocsv/orderstoxlsx, `file`, `output`, `usecomma`, `data` | Export a strategy's orders/trades to CSV/XLSX. | `SQConsole.tools()` -> `saveOrders()` |
| `-stockgroup` (alias `-stockgroups`) | `action=`list/update/updateAll/importstocks/exportstocks/import/export, `id`, `filepath` | Manage stock groups. | `SQConsole.stockgroups()` |
| `-sourcecode` | `action=generate`, `engine`, `s`, `o` | Generate strategy source code with a generator engine. | `SQConsole.sourcecode()` -> `SourceCode.generate()` |
| `-extindicators` | `action=`list/add/import/load/save/exportvalues/updatecot, `name`, `values`, `type`, `file`, `filepath` | External/custom indicators. `save` = definition XML only; `exportvalues` = value series to CSV (`name=` + `filepath=`); `updatecot` = Data manager COT sync (CFTC download -> `COT_*` indicators). | `SQConsole.extIndicators()` |
| `-ai` | `message` (optional, one-shot), `session` | SQAI chat in the console: REPL or one turn with `message=`; tool calls print live, slash commands like `/agents` work. | `SQConsole.ai()` -> `SQAITurns.runChatTurn` |

## Shared commands (sqcli + qdmcli)

| Command | Args (key=value) | Does | Source |
|---|---|---|---|
| `-symbol` | `action=`add/edit/delete/clear/list/mt5symbols/darwinexsymbols, `symbols`, `datasource`, `datatype`, `bartype`, `instrument`, `broker`, `postfix`, source-specific (`mt5symbols`: `path`) | Manage symbols / download data. `mt5symbols` = symbols a local MT5 terminal offers, `darwinexsymbols` = Darwinex tick-data symbols the license may download. Via `run_cli_command` each command runs in console mode on its own thread: lists print, `add` waits for the registration and prints the real outcome (unknown Darwinex symbol = error, not `Data added`). | `ConsoleImpl.symbol()` |
| `-a` | (= `-symbol action=add`) | Add symbol. | `ConsoleImpl.addSymbol()` (`SQConsole.addSymbol()` adds sqequity/sqfutures) |
| `-e` | (= `-symbol action=edit`) | Edit symbol. | `ConsoleImpl.editSymbol()` |
| `-d` | (= `-symbol action=delete`) | Delete symbol. | `ConsoleImpl.deleteSymbol()` |
| `-c` | (= `-symbol action=clear`) | Clear symbol data. | `ConsoleImpl.clearSymbolData()` |
| `-l` | `csv` (optional) | List symbols. | `ConsoleImpl.listSymbols()` |
| `-instrument` | `action=`add/edit/delete/list, `instrument`, `instruments`, `description`, `pointvalue`, `ticksize`, `tickstep`, `defaultspread`, `defaultslippage`, `datatype`, `broker`, `minDistance`, `orderSizeMultiplier`, `orderSizeStep`, `swap`, `csv` | Manage instruments. | `ConsoleImpl.instrument()` |
| `-ia` | (= `-instrument action=add`) | Add instrument. | `ConsoleImpl.addInstrument()` |
| `-ie` | (= `-instrument action=edit`) | Edit instrument. | `ConsoleImpl.editInstrument()` |
| `-id` | (= `-instrument action=delete`) | Delete instrument. | `ConsoleImpl.deleteInstrument()` |
| `-il` | `csv` (optional) | List instruments. | `ConsoleImpl.listInstruments()` |
| `-data` | `action=`update/import/export/clone/timezones/exportToMT4/exportToMT5, per-action params | Manage price data. | `ConsoleImpl.data()` |
| `-u` | `symbols` (optional), `datefrom`+`dateto` (optional, Dukascopy only: exactly that range) | Update data, all or selected. | `ConsoleImpl.update()` -> `updateRange()` |
| `-di` | `symbol`, `filepath`, `format`, `instrument`, `bartype`, `timeframe`, `timezone`, `errorhandling` | Import data from a file. | `ConsoleImpl.dataImport()` |
| `-de` | `symbols`, `timeframe`, `outputdir`, `prefix`, `format`, `datefrom`, `dateto` | Export data to CSV. | `ConsoleImpl.dataExport()` |
| `-dc` | `symbols`, `timezone`/`hours`, `postfix`, `removeweekends` | Clone data to a timezone. | `ConsoleImpl.cloneData()` |
| `-tz` | - | List timezones. | `ConsoleImpl.listTimezones()` |
| `-brokerprofile` | `action=`list/update/updateAll/importstocks/exportstocks/import/export, `id`, `filepath` | Manage broker profiles. | `ConsoleImpl.brokerProfile()` |
| `-license` | `action=`info/update, `code` | Show or update license. | `ConsoleImpl.license()` |
| `-run` | `file` | Run a file of commands line-by-line. | `ConsoleImpl.run()` |
| `-execute` | `file` | Run an external script and wait. | `ConsoleImpl.execute()` |
| `-waitfor` | `action=`user/file, `file` | Wait for ENTER or for a file to appear. | `ConsoleImpl.waitFor()` |
| `-deletefile` | `file` | Delete a file. | `ConsoleImpl.deleteFile()` |
| `-gui` | - | Start the CLI web server; disables other commands. | `ConsoleImpl.runCommand()` (`-gui` case) -> `MainApp.initWebServer()` |
| `-h` / `-help` / `help` | - | Print `help.txt`. | `ConsoleImpl.help()` |
| `-exit` / `exit` / `quit` | - | Exit the JVM (sqcli first syncs all databanks). | `ConsoleImpl.exit()` (sqcli overrides in `SQConsole.exit()`) |
| `> path` | (trailing on any command) | Redirect output to a file. | `ConsoleImpl.parseParams()` |

sqcli's `-symbol action=add` (`SQConsole.addSymbol()`) additionally supports `datasource=sqequity`
and `datasource=sqfutures` (StrategyQuant data), then defers to the shared implementation.
