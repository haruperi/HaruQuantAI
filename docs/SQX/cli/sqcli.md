# sqcli — StrategyQuant X CLI

> Run StrategyQuant X headless: start/stop projects, manage databanks, export strategy orders,
> manage market data, and drive the app from scripts.

Parent: [CLI overview](README.md)

## Launch & entry point

```
launchers/sqcli                                  # interactive prompt
launchers/sqcli --args="-project action=list"    # one-shot command
```

- Launcher `sqcli.bat` / `sqcli.sh` runs Gradle task `:StrategyQuant:runCli`.
- Main class `SQConsoleStarter.main()` calls `SQApp.main(args, true)` — the `true` puts the app in
  console mode (no `MainWindow`).
- `SQApp` creates a `SQConsole` and calls `consoleApp.run(appArgs)`.
- `SQConsole extends ConsoleImpl`, so sqcli has **all** the shared `ConsoleImpl` commands **plus**
  the StrategyQuant-specific ones (`-project`, `-databank`, `-portfolio`, `-tools`, `-stockgroup`,
  `-sourcecode`, `-extindicators`, `-ai`).

> Source: `SQConsoleStarter.main()`; `SQApp` (`consoleAppInstance = new SQConsole(this)`);
> `SQConsole.runCommand()` / `ConsoleImpl.runCommand()`.

## Startup modes

`ConsoleImpl.run(appArgs)` decides how the process behaves based on the arguments:

| Invocation | Behaviour |
|------------|-----------|
| no arguments | Interactive prompt (`cli()`): reads commands line-by-line from stdin until you `-exit`. |
| single `license…` / `liccheck…` argument | Interactive prompt (after the license argument is handled). |
| single `-gui` argument | Starts the CLI web server, then drops into the interactive prompt. While the web server is active, other CLI commands are disabled. |
| any other argument(s) | **One-shot**: parse, run the single command, then wait for running jobs to finish and exit. |

> Source: `ConsoleImpl.run()`, `ConsoleImpl.cli()`.

## Argument syntax

- The **first token** is the command (e.g. `-project`, `-databank`).
- Remaining tokens are **`key=value`** pairs collected into a parameter map. A bare token (no `=`)
  is stored as a key with a null value (used for flags).
- **`> path`** redirects command output to a file (e.g. `-symbol action=list > out.log`).
- Quote values containing spaces: `name="Example custom project"`. The interactive parser
  (`translateCommandline`) honours single and double quotes.
- Add **`-verbose`** to have errors printed as full stack traces instead of just the message.

> Source: `ConsoleImpl.parseParams()`, `ConsoleImpl.translateCommandline()`.

## StrategyQuant-specific commands

Each command takes an `action=…` parameter selecting the operation. Values below are the exact
`case` labels in the code.

### `-project` — manage projects
> Source: `SQConsole.project()`

| action | Extra params | What it does |
|--------|--------------|--------------|
| `list` | — | List available projects. |
| `start` | `name` | Start a project (syncs its databanks from files first). |
| `startOnlyTask` | `name`, `task` (number, from 1) | Run only the given task of a project. |
| `startFromTask` | `name`, `task` (number) | Start the project from the given task onward. |
| `stop` | `name` | Stop a running project. |
| `pause` | `name` | Pause a running project. |
| `resume` | `name` | Resume a paused project. |
| `remove` | `name` | Remove the project (via `TaskManager.removeProject`). |
| `status` | `name` | Print the project's status. |
| `loadconfig` | `name`, `file` | Load a config file into the project (`.cfx`). |
| `saveconfig` | `name`, `file` | Save the project's config to a file. |

```
launchers/sqcli --args="-project action=list"
launchers/sqcli --args='-project action=start name=Builder'
launchers/sqcli --args='-project action=startOnlyTask name="Example custom project" task=2'
launchers/sqcli --args='-project action=loadconfig name=Builder file=Builder.cfx'
```

### `-databank` — manage databanks
> Source: `SQConsole.databank()`

Common params: `project` (required), `name` (databank name; not needed for `list`).

| action | Extra params | What it does |
|--------|--------------|--------------|
| `list` | — | List databanks in the project. |
| `count` | — | Number of strategies in the databank. |
| `load` | `folder`, `strategies` (default `all`) | Load report files from a folder into the databank. |
| `save` | `folder`, `strategies` (default `all`) | Save databank reports to a folder. |
| `delete` | `strategies` | Remove selected reports. |
| `clear` | — | Remove all reports from the databank. |
| `create` | `position` (optional) | Create a new databank. |
| `remove` | — | Remove a databank. |
| `copy` | `destproject`, `destdatabank` | Copy strategies into another databank. |
| `move` | `destproject`, `destdatabank` | Move strategies into another databank. |
| `synctofiles` | — | Sync the databank to files. |
| `syncfromfiles` | — | Sync the databank from files. |
| `export` | `file`, `view` (default main view) | Export databank contents to CSV/XLSX. |

```
launchers/sqcli --args="-databank action=list project=Builder"
launchers/sqcli --args="-databank action=export project=Builder name=Results file=C:/data/Export.csv"
```

### `-portfolio` — merge / split portfolio strategies
> Source: `SQConsole.portfolio()`

Common params: `project` (required), `databank` (required — the source databank). The databank is
synced from files before the action runs.

| action | Extra params | What it does |
|--------|--------------|--------------|
| `merge` | `strategies` (default `all`), `name` (merged strategy name, default `Portfolio`), `target` (destination databank, default = `databank`), `type` (`simulated`\|`merged`\|`signals`, default `simulated`), `capital` (`first`\|`sum`, simulated only, default `first`), `signalspct` (signals only, default `70`), `signalsstrategy` (signals only, required for `type=signals`) | Merge 2+ strategies into one portfolio strategy — the databank **Portfolio → Merge strategies** action. Runs synchronously (`mergeStrategiesSync`), so the one-shot mode waits for the merge and prints the created portfolio name. |
| `split` | `strategies` (required) | Split merged portfolio strategies back into their original strategies — the **Portfolio → Split strategies** action. The parts are added next to the portfolio in the same databank. Only strategies created by `merge` can be split. |

```
launchers/sqcli --args="-portfolio action=merge project=Builder databank=Results strategies=all name=MyPortfolio"
launchers/sqcli --args="-portfolio action=merge project=Builder databank=Results strategies=Strategy1,Strategy2 type=signals signalspct=70 signalsstrategy=Strategy1"
launchers/sqcli --args="-portfolio action=split project=Builder databank=Results strategies=MyPortfolio"
```

### `-tools` — strategy order export
> Source: `SQConsole.tools()` → `saveOrders()`

| action | Params | What it does |
|--------|--------|--------------|
| `orderstocsv` | `file`, `output` (optional), `usecomma` (default `false`), `data` (default `all`) | Export a strategy's orders/trades to CSV. `file` may be a `.sqx` file or a folder. |
| `orderstoxlsx` | same as above | Export a strategy's orders/trades to XLSX. |

### `-stockgroup` (alias `-stockgroups`) — manage stock groups
> Source: `SQConsole.stockgroups()`

| action | Params | What it does |
|--------|--------|--------------|
| `list` | — | List available stock groups. |
| `update` | `id` | Update stock data for one group. |
| `updateAll` | — | Update stock data for all groups. |
| `importstocks` | `id`, `filepath` | Import a stock list into a group from a file. |
| `exportstocks` | `id`, `filepath` | Export a group's stock list to a file. |
| `import` | `filepath` | Import a group definition (XML). |
| `export` | `id`, `filepath` | Export a group definition (XML). |

### `-sourcecode` — generate strategy source code
> Source: `SQConsole.sourcecode()` → `SourceCode.generate()`

| action | Params | What it does |
|--------|--------|--------------|
| `generate` | `engine`, `s` (input file), `o` (output file) | Generate source code for a strategy with the named generator engine. |

### `-extindicators` — external (custom) indicators
> Source: `SQConsole.extIndicators()`

| action | Params | What it does |
|--------|--------|--------------|
| `list` | — | List external indicators. |
| `add` | `name`, `values` (comma-separated), `type` (byte data-type code) | Add an external indicator with the given value columns. |
| `import` | `name`, `file` | Import indicator data from a CSV file. |
| `load` | `filepath` | Load an indicator definition from a file. |
| `save` | `filepath`, `name` | Save an indicator definition to a file. |

### `-ai` — SQAI interactive chat
> Source: `SQConsole.ai()`

`-ai` opens the SQAI assistant chat in the console — the same turn pipeline the in-app chat panel
uses (`SQAITurns.runChatTurn`): the model, its tools, slash commands and conversation history. Tool
calls are printed live as the assistant works.

| Param | Extra | What it does |
|-------|-------|--------------|
| (none) | — | Interactive REPL: one chat turn per line; `/exit` or `quit` leaves. |
| `message` | `session` (optional, default `sqcli`) | Run a single turn with the given message and return. |

Slash commands work inside the chat, exactly as in the panel: `/agents`, `/skills`, `/plugins`,
`/tools`, `/usage` (remaining AI credits), `/allow-path`, any plugin `/command`, and `/<agent-name>`
to delegate.

```
launchers/sqcli --args="-ai"
launchers/sqcli --args='-ai message="How many projects do I have?"'
```

Full detail: [`../sqai/sqcli-ai.md`](../sqai/sqcli-ai.md).

## Shared commands (from `ConsoleImpl`)

sqcli also supports every shared command — data, symbol, instrument, broker-profile, license, run,
gui, and utility commands. These are documented once on the [qdmcli page](qdmcli.md#commands) and
listed together in the [commands reference](commands-reference.md). In brief:

- **Data / symbols / instruments**: `-data`, `-symbol`, `-instrument` (plus single-letter aliases
  `-a -e -d -c -l -ia -ie -id -il -u -di -de -dc -tz`).
- **Broker profiles**: `-brokerprofile`.
- **Licensing**: `-license action=info|update`.
- **Scripting / control**: `-run file=…`, `-execute file=…`, `-waitfor action=user|file`,
  `-deletefile file=…`, `-gui`.
- **Help / exit**: `-h` / `-help` / `help`; `-exit` / `exit` / `quit`.

> On exit, `SQConsole.exit()` first synchronises all databanks to files (via
> `Program.get("Project").call("synchronizeAllDatabanks")`) before the base `exit()` shuts down the JVM.

## Notes on behaviour

- Commands call the **`Program` registry** — e.g. `Program.get("Project").call("start", args)` — and
  the JSON response is formatted to text by `CLILogger`. See
  [`../onboard/04-applications.md`](../onboard/04-applications.md).
- One-shot invocations block in `waitAndFinish()` until the grid has no running jobs, then exit — so
  a `-project action=start` call stays alive until the run completes.
- Unrecognized commands / actions print `Unrecognized command …` (or `Unrecognized action …`) and
  set a non-zero exit status.

## Related

- [qdmcli.md](qdmcli.md) — the shared data-management commands in full.
- [commands-reference.md](commands-reference.md) — consolidated command table.
- [`../overview/custom-projects.md`](../overview/custom-projects.md) — the project/task model.
- [`../onboard/04-applications.md`](../onboard/04-applications.md) — CLI internals & the `Program` registry.
