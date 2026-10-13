# Command-Line Interface (sqcli / qdmcli)

Headless StrategyQuant X / QuantDataManager (no Electron GUI): the same Java process starts with
no window and reads text commands, one-shot or from an interactive prompt, printing text/JSON.
Uses: scheduled automation (start a Builder or Custom Project, export the databank, from a script),
servers/VPS without a display, batch data jobs (update/import/export/clone many symbols, the main
use of qdmcli), chaining (`-run file=...` runs a command file, `-waitfor` / `-execute` hooks
orchestrate).

| CLI | Drives | Console class | Starter |
|---|---|---|---|
| sqcli | StrategyQuant X (build / optimize / retest projects, databanks, data) | `SQConsole` | `SQConsoleStarter` -> `SQApp.main(args, true)` |
| qdmcli | QuantDataManager (market data, symbols, instruments) | `QDMConsole` | `QDMConsoleStarter` -> `QuantDataManagerApp.main(args, true)` |

`App.main(args, runInConsole)`: GUI starters pass `false` (a `MainWindow` is created), console
starters `true` (no window, command loop). App/starter map, the `Program` registry the commands
call and the CLI web-server (`-gui`) mode: [`../onboard/04-applications.md`](../onboard/04-applications.md).

## Launch from a dev checkout

Launchers wrap a Gradle `runCli` task; commands go through Gradle's `--args`:

```
launchers/sqcli                                   # interactive prompt
launchers/sqcli --args="-h"                        # one-shot
launchers/sqcli --args='-project action=start name=Builder'
launchers/qdmcli --args="-symbol action=list"
```

| Launcher | Gradle task | Main class |
|---|---|---|
| `launchers/sqcli` | `:StrategyQuant:runCli` | `com.strategyquant.strategyquant.SQConsoleStarter` |
| `launchers/qdmcli` | `:QuantDataManager:runCli` | `com.strategyquant.quantdatamanager.QDMConsoleStarter` |

- `runCli` = `JavaExec` with `standardInput = System.in` (interactive prompt) and `setIgnoreExitValue(true)` (non-zero CLI exit does not fail the build).
- Gradle splits `--args="..."` on spaces: `--args="-project action=list"` arrives as `["-project", "action=list"]`.
- Packaged release: `sqcli.exe` / `qdmcli.exe` in the install folder, same syntax as the built-in `help`.
- First run: `sqcli.exe license=XXXXX` once (valid SQX license); then the CLI and `-gui` start normally. `-gui` starts the internal web server, UI at `http://localhost:8080`.
- Source: `sqcli.bat`/`.sh`, `qdmcli.bat`/`.sh`; `runCli` tasks in `projects/app/StrategyQuant/build.gradle` and `projects/app/QuantDataManager/build.gradle`.

## Pages

- [sqcli.md](sqcli.md): launch, startup modes, argument syntax, every command (projects, databanks, tools, stockgroups, source code, external indicators, MCP, shared data/symbol commands).
- [qdmcli.md](qdmcli.md): launch and the data-management commands.
- [commands-reference.md](commands-reference.md): every command of both CLIs with source class + method.
- [`../build-and-run.md`](../build-and-run.md): launchers and `runCli` in the wider build.
- [`../overview/custom-projects.md`](../overview/custom-projects.md): the project/task model `-project` drives.
