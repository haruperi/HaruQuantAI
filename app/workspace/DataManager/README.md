# Data Manager workspace

Status: integration candidate, 2026-10-01. Full release qualification and shared
live activation remain pending. Historical implementation descriptions remain in
Git; they do not qualify this candidate. No independent SQX parity is claimed.

Package: `workspace.data_manager`. The approved plan and execution evidence are
under `.agents/logs/20260930_datamanager_script_integration/`.

## Ownership and feature registry

| Feature | Owner | Current behavior |
| --- | --- | --- |
| `FEAT-DM-COORDINATOR` / `FR-DATA-003` | `workspace.py` | Discovered child bindings, actual update job admission, capability forwarding; candidate |
| `FEAT-DM-ACTIONS` / `FR-DATA-002` | `operations.py`, retained inspection helpers in `actions.py` | Dataset-ID export, clone, definition transfer, revision-checked edits and management through host custody; candidate |
| `FEAT-DM-PERSISTENCE` | Host market custody, consumed through `MarketAccess` | Immutable source identities and verified retained partitions; no plugin SQL; candidate |
| `FEAT-DM-CATALOGS` | `catalogs.py` | Instruments, brokers, sessions and stock groups through revision-checked host settings; candidate |

`FR-DM-RETAINED-INSPECTION` covers actual data/chart/numerical quality reads.
`FR-DM-EXPORT`, `FR-DM-CLONE`, and `FR-DM-DEFINITIONS` cover retained-resource
operations in `operations.py`. `FR-DM-CATALOG-SCHEMA` and
`FR-DM-CATALOG-PERSIST` cover configuration validation and durable revisions.
Each provider and External Indicators owns its feature registry under
`app/plugin/DataSource/`; the workspace imports no concrete provider.

## Public workflow and durable truth

The host publishes `actions.*`, `catalogs.get`, `catalogs.replace`, and accepted
`sources.<provider>.*` operations. Each provider attaches exclusively through
`data_source.acquisition@1.0.0`; SQData supplies presentation for separate equity
and futures backends. Unknown operations and missing capabilities fail explicitly.
No acquisition plugin is required to read and export retained source partitions.

Dataset IDs distinguish owner, source, symbol, underlying instrument, timeframe,
timezone and broker. Symbols alone must resolve uniquely. Successful empty
inventory stays empty. A failed refresh retains a stale snapshot and blocks data
actions until refreshed. No browser definitions or fabricated progress become
backend inventory. Update actions submit real jobs and report rejected selections.
Empty definitions require an explicit initial date range.

The UI holds presentation state and polls actual host jobs. Instruments, brokers,
sessions and stock groups persist through scoped host settings. Legacy browser
catalog transfer is explicit and preserves its original bytes. External Indicator
legacy transfer belongs to its plugin. State replacements reject stale revisions.

Exports return actual CSV/MT5 text or MT4 HST401/FXT405 bytes. MT4 consumer import
has not been independently validated. Clone transforms explicit fixed/IANA wall
time and optionally removes weekends. Data edits require the complete partition
revision map and valid source numeric values; whole-year removal and replacement
are atomic in source custody. Legacy path-based editing refuses to report success.
Quality measures numerical validity only, not exchange completeness or parity.

## Qualification boundaries

Focused tests are `tests/workspace/DataManager/` and the provider tests. Actual
package file removal/restart/restore and producer-independent retained reads are
exercised in `tests/host/test_composition.py`. These tests do not replace the full
browser/removal qualification matrix. The shared database is untouched.

Bounded live acquisition passed for Yahoo, Dukascopy, Darwinex, MT5, authenticated
SQ equity/futures and all six crypto exchanges. Ten deterministic offline examples
passed. Actual UI rebuilds after thirteen cohort removal cases and removal of all
optional workspaces passed, with fresh backend composition and independent retained
reads. These checks do not establish complete browser coverage or full release
qualification. Non-default session filtering, consumer verification of MT4 exports,
durable job recovery, complete browser/removal qualification and live activation
remain outstanding. The walkthrough records exact evidence and limits.

Verification commands:

```sh
uv run pytest tests/workspace/DataManager tests/plugin/DataSource --no-cov
uv run python scripts/ci_check.py
uv run python scripts/package_inventory.py
node scripts/ui_architecture_check.cjs
npm --prefix app/ui run typecheck
npm --prefix app/ui run test
npm --prefix app/ui run build
```

## Command-line client ownership

`scripts/data_manager_cli.py` and `tests/test_data_manager_cli.py` belong to this
workspace and are removed during its cascade. The CLI imports the universal host
client only and invokes the same published operations as the UI. Provider removal
leaves inventory, catalogs and retained-data actions available; acquisition commands
report an absent provider explicitly. Start the app host first, then run:

```powershell
uv run python scripts/data_manager_cli.py --data --url http://127.0.0.1:8000
uv run python scripts/data_manager_cli.py --instruments
```

Use `HARU_CLIENT_PASSWORD` when authentication requires a password. `--db` and
`--data-dir` are rejected: custody is configured on the host. Local export/file
options are handled by the client after the host validates and produces content.
Operational log read/clear options lack published host contracts and fail explicitly.
No direct plugin/workspace implementation imports or ad-hoc SQL remain in the CLI.
