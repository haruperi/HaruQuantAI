# Browse Reference (`FEAT-DATA-BROWSE_REFERENCE`)

## Purpose

Own market-data series reference catalogue, broker profiles, instrument
specifications, historical bar retrieval, and market directory projections.
The feature persists to the shared workspace database (`data`, `broker`,
`instruments`, `data_bars`) and exposes every operation through the
operation-discriminated `data.browse-reference@1` capability.

## Domain

`data`

## Provides

- `data.browse-reference@1`

## Required Capabilities

None

## Optional Capabilities

None

## Configuration

| Key | Type | Default | Description |
| --- | --- | --- | --- |
| `database_path` | string / Path | `data/database/haruquantai.db` | Shared workspace SQLite database holding market reference, broker, instrument, and bar history tables. |

Unknown keys are rejected with `ValueError`.

## Runtime Effects

- Opens exactly one SQLite connection per mounted feature generation and
  ensures the `data`, `broker`, `instruments`, and `data_bars` tables exist (`IF NOT EXISTS`).
- Seeds reference catalogue records from `haruquant-dev.db` when present and tables are empty.
- Registers one scope cleanup callback closing the connection.
- Starts no sockets, listeners, or background tasks.

## Persistent State

Namespace `data.browse_reference` retaining market reference catalogue (`data`),
broker profiles (`broker`), instrument specifications (`instruments`), and
cached bar history (`data_bars`) in SQLite.

## Failure Behavior

- Requesting bars for an unrecorded symbol or timeframe returns `DATA_FEED_UNAVAILABLE`
  with problem code `UPSTREAM_UNAVAILABLE` (status 503).
- Specifying an inverted time window or invalid timeframe returns `DATA_VALIDATION_FAILED`
  (status 422).
- Updating or reading an unrecorded instrument or series returns `DATA_NOT_FOUND`
  (status 404).
- Unsupported operation discriminators return `DATA_VALIDATION_FAILED` (status 400).

## Removal Behavior

Unmounting the feature withdraws the `data.browse-reference@1` provider;
consumers fail closed. Reference and bar history records are retained in the
database; re-mounting resumes on existing rows.

## Evidence

Run the bounded executable demonstration with:

```powershell
uv run python -m app.services.data.browse_reference.browse_reference
```
