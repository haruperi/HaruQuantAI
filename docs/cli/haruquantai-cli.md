# HaruQuantAI CLI

Run these commands from the project root in PowerShell. The CLI runs headlessly without starting a Uvicorn HTTP server.

`app/cli.py` is the headless entry point. It registers domain command modules,
routes parsed arguments to their bound handlers, and manages host commands and
logging shutdown. Each domain owns its command definitions and execution.

Data Manager commands live in `app/workspace/data_manager/cli.py` alongside their
table formatters. Its `register_commands(commands)` registers the command tree
and binds `run_command` as the handler. That handler owns domain validation,
service calls, output, and exit codes. Additional domains can follow this same
registration pattern without adding domain-specific dispatch to `app/cli.py`.

## Initialization

### Login

```powershell
uv run python -m app.cli login --username YOUR_USERNAME
```

Enter your password at the prompt. Login returns a JSON response containing the session token in `data.token`. Use the username and password configured in the application settings.

### Set the session token

Copy the token from the login response into the current PowerShell session:

```powershell
$env:HARUQUANTAI_SESSION_TOKEN = "TOKEN_FROM_LOGIN"
```

Treat this token as a credential. Do not share it or commit it to source control.

### Check health

```powershell
uv run python -m app.cli health
```

Checks local settings and session storage and returns a JSON result. When `HARUQUANTAI_SESSION_TOKEN` is set, the command also validates the CLI session and refreshes its sliding 24-hour inactivity timeout. An invalid, expired, revoked, or UI-issued token fails validation.

Without a token, this command performs the basic local health check without authentication. It does not check broker connectivity or HTTP server availability.

### Logout

```powershell
uv run python -m app.cli logout
Remove-Item Env:HARUQUANTAI_SESSION_TOKEN -ErrorAction SilentlyContinue
```

Logout revokes the token supplied through `HARUQUANTAI_SESSION_TOKEN`. The second command clears it from the current shell. CLI sessions use `peer_id="cli"` in `host_session`; logout does not revoke UI sessions.

### Help

```powershell
uv run python -m app.cli --help
```

### Exit codes

| Code  | Meaning                                    |
| ----- | ------------------------------------------ |
| `0` | Command succeeded.                         |
| `1` | Command failed, or login was cancelled.    |
| `2` | Invalid or missing command-line arguments. |

Command results are written to standard output: symbol lists and created symbols use an ASCII table;
other results and errors use JSON. Operational messages use central logging.

## Data Manager

### Symbol Commands

#### List symbols

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

#### Add a symbol

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

#### Edit one or more symbols

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

#### Delete one or more symbols

```powershell
uv run python -m app.cli data-manager symbol delete EURUSD_demo
uv run python -m app.cli data-manager symbol delete EURUSD_demo GBPUSD_demo
```

Deletes symbols with the exact saved names, including their datasource suffixes.
Separate multiple names with spaces.
The command runs immediately and prints the deleted name and count on success.
Missing symbols and other service failures return JSON and exit code 1.
A missing name or unsupported arguments return exit code 2.

#### Update symbols from MT5

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

#### Clone a symbol

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

#### Load symbols from CSV

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

#### Save symbols to CSV

```powershell
uv run python -m app.cli data-manager symbol save "C:\Data\symbols.csv"
```

Exports the full catalog, including catalogs larger than 1,000 symbols, in the
CSV format accepted by `symbol load`. Accepts absolute or relative paths; quote
paths containing spaces. Missing parent directories are created, and an existing
destination file is replaced. Success prints the exported count and absolute path.

An empty catalog or a file write failure returns a JSON error and exit code 1.
A missing path returns exit code 2.

#### Symbols tab and HTTP adapter

The Data Manager Symbols tab uses the same `Symbols` service and database as the
headless CLI. The domain HTTP adapter lives in
`app/workspace/data_manager/http.py`; `app/main.py` only mounts its router.
All endpoints require a UI session and the host's data read/write scopes.

- Browse, search, sort, and filter the catalog; use Previous/Next and choose
  25, 50, or 100 rows per page. Selections persist across pages.
- Add Symbol opens the specification editor. The datasource suffix follows the
  CLI naming convention: `EURUSD` with `demo` becomes `EURUSD_demo`.
- Select one symbol to edit or clone it. Select multiple symbols for Mass Edit;
  only checked fields change. Double-click a row to edit it.
- Mass Delete removes selected symbols after confirmation. Each row also has a
  delete action. Errors are shown without removing unconfirmed rows locally.
- Save downloads selected symbols as CSV, or the full catalog if nothing is
  selected. Exports retain nested specification fields and can exceed 1,000 rows.
- Load accepts a CSV upload up to 10 MB. Valid rows are imported and skipped rows
  are reported. Existing names are skipped rather than overwritten.
- Refresh symbols reloads the persisted catalog.
- Select one or more rows and choose **Update from MT5** to refresh their saved
  specifications from the running MT5 Expert bridge. The button is disabled during
  the update. Updated rows appear after the host confirms the batch; failures retain
  the previous snapshot and display an error in the progress area.
- When the successfully loaded catalog contains no symbols, **Update from MT5**
  imports every symbol returned by the terminal, retaining the native MT5 names.
  The import is atomic, including catalogs larger than 1,000 entries. A populated
  catalog still requires selecting rows; an empty search result does not trigger
  import mode.

CSV imports and exports use the service's existing format, including JSON within
specification columns. Browser commission and swap settings are retained in the
nested contract fields when saving, cloning, or transferring symbols.

### Session Commands

#### List sessions

```powershell
uv run python -m app.cli data-manager session list
uv run python -m app.cli data-manager session list --page 2
uv run python -m app.cli data-manager session list --page 1 --page-size 25
```

Lists calendars from `datamgr_sessions` using the session ASCII table, with 50
sessions per page by default. Output includes the current page, total pages, and
total session count. Both options require positive integers. Pages beyond the
catalog return exit code 2. An empty catalog displays page 1 of 1 with zero items.

All session commands use the same `Sessions` service as the Sessions tab and run
locally without a session token or a running HTTP server. Use exact saved names,
quoting names containing spaces. Service failures return JSON and exit code 1;
invalid CLI arguments return exit code 2.

#### Add a session

```powershell
uv run python -m app.cli data-manager session add --name London --timezone Europe/London --description "London trading hours"
```

`--name` is required and must be unique. Names are saved exactly as supplied,
without appending a broker suffix. Successful creation displays the new calendar
in a table. Optional fields are:

| Flag                                   | Value                                                   | Default when adding       |
| -------------------------------------- | ------------------------------------------------------- | ------------------------- |
| `--description`                      | Description text.                                       | Empty string.             |
| `--timezone`                         | IANA timezone, such as `UTC` or `America/New_York`. | `UTC`.                  |
| `--broker-id`                        | Integer broker ID.                                      | `-1` (Default).         |
| `--windows`                          | JSON array of trading intervals.                        | `[]` (closed calendar). |
| `--holidays`                         | JSON array of full-day holidays.                        | `[]`.                   |
| `--is-default` / `--no-is-default` | Set or clear the default-profile flag.                  | False.                    |

To include intervals and holidays, pass each JSON array as one argument:

```powershell
$windows = '[{"day_from":"Mon","day_to":"Mon","start_time":"08:00","end_time":"17:00","eod":true,"session_type":"Regular"}]'
$holidays = '[{"date_str":"2026-12-25","description":"Christmas"}]'
uv run python -m app.cli data-manager session add --name LondonMonday --timezone Europe/London --windows $windows --holidays $holidays
```

Weekdays accept English short or full names and are stored as `Mon` through `Sun`.
Times use `HH:MM` or `HH:MM:SS`; holidays use `YYYY-MM-DD`. Use the next day as
`day_to` for an overnight interval, such as Monday 22:00 to Tuesday 06:00.
Each profile accepts up to 100 intervals and 1,000 holidays. Duplicate holiday
dates, unknown fields, invalid timezones, and invalid dates or times are rejected.

#### Edit one or more sessions

```powershell
uv run python -m app.cli data-manager session edit London --description "Updated London hours"
uv run python -m app.cli data-manager session edit London LondonMonday --timezone UTC
uv run python -m app.cli data-manager session edit London --name "London Main"
uv run python -m app.cli data-manager session edit LondonMonday --no-is-default --holidays '[]'
```

Supply at least one field option. Edit accepts the same fields as add; omitted
fields retain their saved values. `--name` renames exactly one target and cannot
be used when editing multiple sessions. `--windows` and `--holidays` replace the
whole corresponding list; use `'[]'` to clear it.

Multi-session edits are atomic: missing targets, duplicate destination names, or
storage failures roll back the whole operation. Repeated target names are applied
once. Successful edits display the updated calendars in a table. Invalid field
values, missing sessions, or an empty set of updates return exit code 1.

#### Clone a session

```powershell
uv run python -m app.cli data-manager session clone London "London Copy"
```

Copies the source calendar into a new database entry with a fresh ID. Broker,
timezone, description, intervals, holidays, and the default-profile flag are
preserved. The source remains unchanged. The target name must be unique.
Success displays the cloned calendar in a table; missing sources and duplicate
targets return JSON errors and exit code 1.

#### Delete one or more sessions

```powershell
uv run python -m app.cli data-manager session delete "London Copy"
uv run python -m app.cli data-manager session delete London LondonMonday
```

Deletes the exact saved names immediately, without a confirmation prompt, and
prints the deleted calendars in a table. Batch deletion is atomic: a missing
session or a database reference that prevents deletion leaves the whole batch
unchanged and returns exit code 1. Repeated target names are deleted once.

#### Load sessions from JSON

```powershell
uv run python -m app.cli data-manager session load "C:\Data\sessions.json"
```

Accepts an absolute path or a path relative to the current directory. Quote paths
containing spaces. The file must contain a JSON array of session objects, using
the same fields as add. For example:

```json
[
  {
    "name": "LondonMonday",
    "description": "London Monday trading hours",
    "timezone": "Europe/London",
    "broker_id": -1,
    "is_default": false,
    "windows": [
      {
        "day_from": "Mon",
        "day_to": "Mon",
        "start_time": "08:00",
        "end_time": "17:00",
        "eod": true,
        "session_type": "Regular",
        "day_of_week": 0
      }
    ],
    "holidays": [
      {"date_str": "2026-12-25", "description": "Christmas"}
    ]
  }
]
```

For each interval, omitted fields default to Monday 00:00-23:59, `eod: false`,
`session_type: "Regular"`, and `day_of_week: null`. When supplied, `day_of_week`
is an integer from 0 (Monday) to 6 (Sunday); it is normalized to match `day_from`.
Holiday descriptions default to an empty string.

Imports add new entries and do not overwrite existing names. A duplicate name in
the file or database, an invalid entry, or a storage failure rolls back the entire
import, including imports larger than 1,000 sessions. Optional imported `id` and
`broker_name` fields are ignored; new database IDs are assigned. Other unknown
fields are rejected. Success displays the imported calendars in a table. Missing
files, invalid JSON, or rejected imports return exit code 1.

#### Save sessions to JSON

```powershell
uv run python -m app.cli data-manager session save "C:\Data\sessions.json"
```

Exports the full persisted catalog, including catalogs larger than 1,000 sessions,
as a UTF-8 JSON array accepted by `session load` and the Sessions tab's Load action.
An empty catalog exports as `[]`. Database IDs and derived broker names are omitted;
calendar settings, broker IDs, intervals, and holidays are preserved.

Accepts absolute or relative paths; quote paths containing spaces. The parent
directory must already exist. An existing destination is replaced only after
successful serialization. Success prints the exported count and destination path.
File or storage failures return JSON and exit code 1.

For command-specific help:

```powershell
uv run python -m app.cli data-manager session --help
uv run python -m app.cli data-manager session add --help
uv run python -m app.cli data-manager session edit --help
```

### Broker profiles

The Brokers tab connects Add new, Edit selected, Mass delete, Save, and Load to
these same service operations through authenticated HTTP routes. Add and edit
open field editors; editing multiple selected rows opens a bulk field editor.
System flags are editable. Record IDs and creation/update timestamps are shown
read-only because persistence assigns them. Successful operations update the
catalog automatically. Refresh and automatic broker-update buttons are not
part of this toolbar.

Broker commands use the `Brokers` service and the `datamgr_broker` table directly.
They run locally without a session token or a running HTTP server. Targets are
exact saved broker names; quote names containing spaces.

#### List brokers

```powershell
uv run python -m app.cli data-manager broker list
uv run python -m app.cli data-manager broker list --page 2 --page-size 25
```

Lists broker profiles in an ASCII table, including customization counts. The
default is page 1 with 50 profiles per page. Both options require positive
integers; requesting a page beyond the available pages is an argument error.

#### Add a broker

```powershell
uv run python -m app.cli data-manager broker add --name Demo --description "Demo account" --server-timezone Europe/London --postfix _demo --mt-use
```

Names are required and saved without an automatic suffix. The service assigns
the database ID and UTC creation/update timestamps. Optional flags are:

| Flag                                             | Value                                                        | Default on add |
| ------------------------------------------------ | ------------------------------------------------------------ | -------------- |
| `--description`                                | Description string.                                          | Empty string.  |
| `--server-timezone`                            | IANA timezone or the supported `EETUS` broker clock label. | `UTC`.       |
| `--postfix`                                    | Symbol/data postfix string.                                  | Empty string.  |
| `--is-system` / `--no-is-system`             | System profile flag.                                         | False.         |
| `--stockpicker-use` / `--no-stockpicker-use` | Stock filtering flag.                                        | False.         |
| `--mt-use` / `--no-mt-use`                   | Symbols and sessions flag.                                   | False.         |
| `--enabled` / `--no-enabled`                 | Enabled flag.                                                | True.          |
| `--clock-policy`                               | JSON object with JSON-compatible values.                     | `{}`.        |
| `--clock-policy-revision`                      | Non-negative integer.                                        | `0`.         |

For example, to supply clock metadata in PowerShell:

```powershell
$policy = '{"mode":"fixed","offset_minutes":120}'
uv run python -m app.cli data-manager broker add --name "Demo Clock" --server-timezone UTC --clock-policy $policy --clock-policy-revision 1
```

Clock policy is stored as metadata; these commands do not perform timezone
conversion. Successful creation displays the saved profile in a table.

#### Edit one or more brokers

```powershell
uv run python -m app.cli data-manager broker edit Demo --description "Updated account"
uv run python -m app.cli data-manager broker edit Demo "Demo Clock" --no-enabled
uv run python -m app.cli data-manager broker edit Demo --name "Demo Main"
uv run python -m app.cli data-manager broker edit "Demo Clock" --clock-policy '{}'
```

Accepts the same optional flags as add, plus `--name` to rename one profile.
At least one update is required. Renaming multiple targets is rejected. Omitted
fields retain their current values; `--clock-policy` replaces the whole policy
object. Repeated target names are edited once.

Bulk edits are atomic. A missing target, invalid update, or conflicting name
leaves all selected profiles unchanged. Creation timestamps are preserved and
update timestamps are refreshed.

#### Delete one or more brokers

```powershell
uv run python -m app.cli data-manager broker delete "Demo Main"
uv run python -m app.cli data-manager broker delete Demo "Demo Clock"
```

Deletes the named broker records atomically and displays the removed profiles.
Repeated names are processed once. A missing target or a database reference
that prevents deletion rolls back the entire batch. This command does not
cascade deletion to stock memberships, symbols, sessions, or datasets.

The browser adapter additionally checks symbol, session, and dataset usage, and
removes stock memberships when deleting an unused profile. System profiles can
be edited or deleted from the browser as well. Usage checks still apply. These
browser policies are not CLI service checks.

#### Load brokers from JSON

```powershell
uv run python -m app.cli data-manager broker load "C:\Data\brokers.json"
```

Imports a JSON array using the service field names, for example:

```json
[
  {
    "name": "Imported Demo",
    "description": "Demo account",
    "is_system": false,
    "stockpicker_use": false,
    "mt_use": true,
    "server_timezone": "UTC",
    "postfix": "_demo",
    "enabled": true,
    "clock_policy": {},
    "clock_policy_revision": 0
  }
]
```

Only `name` is required; omitted fields use the add defaults. Boolean fields
must be JSON booleans. Imports create new records and do not overwrite existing
names. A duplicate name, invalid entry, or storage failure rolls back the entire
import, including files larger than 1,000 profiles. An empty array imports zero
profiles.

Imported `id`, `created_at_utc`, `updated_at_utc`, `customized_stocks`,
`customized_instruments`, and `customized_sessions` fields are ignored. IDs and
timestamps are generated locally; other unknown fields are rejected. Files may
use UTF-8 with or without a BOM. Success displays the imported profiles.

#### Save brokers to JSON

```powershell
uv run python -m app.cli data-manager broker save "C:\Data\brokers.json"
```

Exports the complete catalog as a UTF-8 JSON array accepted by `broker load`
and the Brokers tab's Load action. An empty catalog exports as `[]`. Exports
preserve broker settings, including system flags and clock policy metadata, and
omit database IDs, timestamps, and calculated customization counts. Stock
memberships, symbol definitions, and session calendars are separate data and
are not included.

Both transfer commands accept absolute or relative paths. Quote paths containing
spaces. For save, the parent directory must already exist; an existing file is
replaced only after successful serialization. Success prints the exported count
and destination path.

Service and file failures print a JSON error response and return exit code 1.
Parser errors return exit code 2. Successful commands return exit code 0.

For command-specific help:

```powershell
uv run python -m app.cli data-manager broker --help
uv run python -m app.cli data-manager broker add --help
uv run python -m app.cli data-manager broker edit --help
```
