# HaruQuantAI CLI

Run these commands from the project root in PowerShell. The CLI runs headlessly without starting a Uvicorn HTTP server.

## Command organization

`app/cli.py` is the headless entry point. It registers domain command modules,
routes parsed arguments to their bound handlers, and manages host commands and
logging shutdown. Each domain owns its command definitions and execution.

Data Manager commands live in `app/workspace/data_manager/cli.py` alongside their
table formatters. Its `register_commands(commands)` registers the command tree
and binds `run_command` as the handler. That handler owns domain validation,
service calls, output, and exit codes. Additional domains can follow this same
registration pattern without adding domain-specific dispatch to `app/cli.py`.

## Login

```powershell
uv run python -m app.cli login --username YOUR_USERNAME
```

Enter your password at the prompt. Login returns a JSON response containing the session token in `data.token`. Use the username and password configured in the application settings.

## Set the session token

Copy the token from the login response into the current PowerShell session:

```powershell
$env:HARUQUANTAI_SESSION_TOKEN = "TOKEN_FROM_LOGIN"
```

Treat this token as a credential. Do not share it or commit it to source control.

## Check health

```powershell
uv run python -m app.cli health
```

Checks local settings and session storage and returns a JSON result. When `HARUQUANTAI_SESSION_TOKEN` is set, the command also validates the CLI session and refreshes its sliding 24-hour inactivity timeout. An invalid, expired, revoked, or UI-issued token fails validation.

Without a token, this command performs the basic local health check without authentication. It does not check broker connectivity or HTTP server availability.

## List symbols

```powershell
uv run python -m app.cli data-manager symbol list
```

Displays symbols from the local Data Manager catalog using the ASCII table
formatter in `app/workspace/data_manager/cli.py`, with 50 symbols per page by default.
The output includes the current page, total pages, symbol range, and next-page command.

```powershell
uv run python -m app.cli data-manager symbol list --page 2
uv run python -m app.cli data-manager symbol list --page 1 --page-size 25
```

Both options require positive integers. Pages beyond the catalog return exit code 2.
An empty
catalog displays a table with zero items. Failures return a JSON error. This read-only
command does not require a session token or a running HTTP server.

## Add a symbol

```powershell
uv run python -m app.cli data-manager symbol add --name EURUSD --datasource demo
```

Both flags are required. The service saves this example as `EURUSD_demo` and
rejects duplicates. Successful creation displays the new symbol in a table.

```powershell
uv run python -m app.cli data-manager symbol add --name EURUSD --datasource demo --description "Euro vs US Dollar" --data-type Forex --pip-size 0.0001 --point-value 100000 --default-spread 1.5 --commission 7 --order-size-multiplier 0.01 --order-size-step 0.01
```

Optional flags: `--description`, `--exchange`, `--data-type`, `--broker-id`,
`--default-spread`, `--pip-size`, `--pip-step`, `--point-value`, `--min-distance`,
`--order-size-multiplier`, `--order-size-step`, `--swap-long`, `--swap-short`,
`--triple-swap-on`, `--swap-type`, and `--commission`. Omitted values use service defaults.
Run `uv run python -m app.cli data-manager symbol add --help` for usage.

## Edit one or more symbols

```powershell
uv run python -m app.cli data-manager symbol edit EURUSD_demo --default-spread 2 --commission 5 --description "Updated description"
uv run python -m app.cli data-manager symbol edit EURUSD_demo GBPUSD_demo --commission 5
```

Use the exact saved symbol name, including its datasource suffix. Supply at least
one field option. List multiple names separated by spaces to apply the same updates
to each symbol. Only supplied fields change; omitted values are preserved.
The command supports the same optional field flags as `add`, plus `--name` to
rename a single saved symbol. `--name` requires exactly one target symbol.
Renaming uses the exact new name without appending a suffix.
`--datasource` is only used during creation.

Successful edits display the updated symbol in a table. Missing symbols and other
service failures return JSON and exit code 1; invalid CLI arguments return code 2.

```powershell
uv run python -m app.cli data-manager symbol edit --help
```

## Delete one or more symbols

```powershell
uv run python -m app.cli data-manager symbol delete EURUSD_demo
uv run python -m app.cli data-manager symbol delete EURUSD_demo GBPUSD_demo
```

Deletes symbols with the exact saved names, including their datasource suffixes.
Separate multiple names with spaces.
The command runs immediately and prints the deleted name and count on success.
Missing symbols and other service failures return JSON and exit code 1.
A missing name or unsupported arguments return exit code 2.

## Update symbols from MT5

```powershell
uv run python -m app.cli data-manager symbol update EURUSD_demo
uv run python -m app.cli data-manager symbol update EURUSD_demo GBPUSD_demo
uv run python -m app.cli data-manager symbol update
```

Reads specifications from the authenticated MT5 Expert bridge and updates existing
catalog entries. Names may match MT5 exactly or include a datasource suffix; the
longest matching terminal symbol is used. Catalog names and broker IDs are retained.
All requested snapshots are fetched before the database transaction starts. A missing
symbol, bridge failure, or storage failure leaves the batch unchanged.

With no names, `update` imports all available MT5 symbols into an empty catalog.
The Python equivalent is `Symbols().mt5update()`. Imported entries retain native
terminal names without a datasource suffix. Imports are batched and atomic; if
the catalog is no longer empty, the host rejects the import rather than merging
or replacing records.

The Python API is `Symbols().mt5update("EURUSD_demo")` or
`Symbols().mt5update(["EURUSD_demo", "GBPUSD_demo"])` and returns a standard response
with the updated specifications in `data`.

Run the bundled Expert in MT5. Bridge configuration is shared with the trading
example: `MT5_BRIDGE_TOKEN`, `MT5_BRIDGE_HOST` (default `127.0.0.1`),
`MT5_BRIDGE_PORT` (default `8765`), and `MT5_BRIDGE_TIMEOUT` (default `10` seconds).
The bundled development token is the default when no token override is set.
The listener port must be free; concurrent updates are rejected as unavailable.
This command reads terminal metadata and does not place orders.

Local slippage, margin rate, and configured numeric commission values are preserved;
MT5 commission rules are stored with their availability status and any local model.

## Clone a symbol

```powershell
uv run python -m app.cli data-manager symbol clone EURUSD_demo EURUSD_COPY
```

Copies the source symbol's specifications into a new catalog entry and displays
the created symbol in a table. The source remains unchanged. The service inherits
the source datasource suffix, so this example creates `EURUSD_COPY_demo`.
You can also supply the full target name `EURUSD_COPY_demo`.

To choose another datasource suffix:

```powershell
uv run python -m app.cli data-manager symbol clone EURUSD_demo EURUSD --new-datasource other
```

This creates `EURUSD_other`. Missing sources and duplicate targets return JSON
errors and exit code 1. Missing or unsupported arguments return exit code 2.

## Load symbols from CSV

```powershell
uv run python -m app.cli data-manager symbol load "C:\Data\symbols.csv"
```

Accepts an absolute path or a path relative to the current directory. Quote paths
containing spaces. For example:

```csv
name,datasource,description,commission
EURUSD,demo,Euro vs US Dollar,7
GBPUSD,demo,British Pound vs US Dollar,5
```

This creates `EURUSD_demo` and `GBPUSD_demo`. Files exported by `Symbols.save()`
are also supported, including their JSON specification columns. If `datasource`
is omitted, the loader derives it from the last underscore in the saved name,
or uses `SQ default` when the name has no suffix.

The command prints the import summary, previews up to 50 imported symbols in a
table, and reports each skipped row. Valid rows are imported even when other rows
fail; existing symbols are skipped rather than overwritten. Partial imports return
exit code 0 when at least one row loads. Missing files, empty files, and imports
where every row fails return JSON errors and exit code 1. A missing path returns
exit code 2. Use `symbol list --page N` to browse the catalog after importing.

## Save symbols to CSV

```powershell
uv run python -m app.cli data-manager symbol save "C:\Data\symbols.csv"
```

Exports the full catalog, including catalogs larger than 1,000 symbols, in the
CSV format accepted by `symbol load`. Accepts absolute or relative paths; quote
paths containing spaces. Missing parent directories are created, and an existing
destination file is replaced. Success prints the exported count and absolute path.

An empty catalog or a file write failure returns a JSON error and exit code 1.
A missing path returns exit code 2.

## Logout

```powershell
uv run python -m app.cli logout
Remove-Item Env:HARUQUANTAI_SESSION_TOKEN -ErrorAction SilentlyContinue
```

Logout revokes the token supplied through `HARUQUANTAI_SESSION_TOKEN`. The second command clears it from the current shell. CLI sessions use `peer_id="cli"` in `host_session`; logout does not revoke UI sessions.

## Help

```powershell
uv run python -m app.cli --help
```

## Exit codes

| Code | Meaning |
| --- | --- |
| `0` | Command succeeded. |
| `1` | Command failed, or login was cancelled. |
| `2` | Invalid or missing command-line arguments. |

Command results are written to standard output: symbol lists and created symbols use an ASCII table;
other results and errors use JSON. Operational messages use central logging.
