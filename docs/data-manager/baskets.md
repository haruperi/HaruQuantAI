# Basket service API

`app.workspace.data_manager.baskets.Baskets` owns stock groups in
`datamgr_stock_group` and constituent histories in `datamgr_stock`. All methods
return `StandardResponse` dictionaries with operation names under `baskets.*`.
An optional `HostPersistence` gateway isolates the service for tests or another
database. Database access stays behind that gateway.

```python
from app.workspace.data_manager.baskets import Baskets

baskets = Baskets()
baskets.add("Watchlist", description="My stocks")
baskets.edit_stocks("Watchlist", "AAPL;01.01.2020\nMSFT")
```

## Operations

| Method | Behavior |
| --- | --- |
| `list(include_stocks=True)` | Existing catalog listing and calculated counts. |
| `add(name, *, description="", system=False)` | Create an empty group. |
| `edit(baskets, updates=None, **fields)` | Update `name` and/or `description`; renaming requires one target. |
| `delete(baskets)` | Delete groups and their full membership histories; downloaded market data remains. |
| `list_stocks(basket)` | Return all historical constituent records. |
| `edit_stocks(basket, stocks)` | Replace the complete membership history, including clearing it with `[]`. |
| `import_stocks(basket, csv_path)` | Replace memberships from semicolon-separated CSV. |
| `export_stocks(basket, csv_path)` | Export memberships as semicolon-separated CSV. |
| `save(json_path, baskets=None)` | Export all groups, or selected groups, with complete histories as JSON. |
| `load(json_path)` | Import new groups and their histories from JSON. |
| `update_data(baskets, *, client=None, data_dir=None)` | Acquire D1 constituent bars, persist Parquet, and register saved datasets. |

A target is an exact saved group name or a positive integer database ID. Bulk
methods accept one target or a sequence of targets. Names are stripped and
unique without regard to case; the database has no name uniqueness constraint,
so the service checks this inside its write transactions. Ambiguous legacy
names must be selected by integer ID. Names have at most 50 characters and
descriptions at most 250.

As in the donor, system groups can be listed, exported, and updated, but cannot
be edited, deleted, or have their memberships replaced. System flags are set
on creation/import and preserved in exports. Metadata edits write both `DESC`
and the application's `description` compatibility column.

Group CRUD, complete membership replacements, and JSON imports are atomic,
including batches larger than 1,000 records. A missing target, duplicate group
name, malformed membership, or storage failure rolls back the operation.
Imports reject existing group names rather than overwriting them.

## Membership records and CSV

Structured membership input uses the following fields; `BasketStockItem`
instances are accepted too:

```python
baskets.edit_stocks("Watchlist", [
    {"ticker": "AAPL", "date_from": "01.01.2020", "date_to": -1},
    {"ticker": "MSFT", "date_from": "2010-01-01", "date_to": "2015-12-31"},
])
```

Dates accept Unix milliseconds (including negative timestamps for dates before 1970), `DD.MM.YYYY`, or `YYYY-MM-DD`.
Missing starts become `0` (unspecified), and missing/null ends become `-1`
(ongoing). End dates must not precede starts. Boolean timestamps, unknown
fields, and duplicate ticker/start/end intervals are rejected. Multiple
historical intervals for a ticker are supported. Membership identifiers and
basket IDs supplied in structured records are ignored; local identities are
assigned by persistence.

CSV is UTF-8 (an optional BOM is accepted on import), without a header:

```text
AAPL
TSLA;01.12.2020
AMZN;15.04.2007;30.05.2015
```

CSV dates use UTC. Empty date cells preserve the unspecified/ongoing sentinels.
Exports normally format dates as `DD.MM.YYYY`; timestamps containing a time
component are exported as integer milliseconds to preserve them exactly.
Both stock-file methods use CSV: the donor's XML export picker label was
inconsistent with its `writeStocksToCsv` implementation.

## JSON group files

Save/Load use JSON instead of the donor's XML:

```json
[
  {
    "name": "Watchlist",
    "description": "My stocks",
    "system": false,
    "stocks": [
      {"ticker": "AAPL", "date_from": 1577836800000, "date_to": -1}
    ]
  }
]
```

Only `name` is required. Missing descriptions, system flags, and stocks default
to `""`, `false`, and `[]`. Database group IDs and membership IDs are regenerated;
exports omit them. Unknown JSON fields are rejected. Empty catalogs round-trip
as `[]`. Save exports all groups unless targets are supplied explicitly:

```python
baskets.save("groups.json")
baskets.save("selected-groups.json", ["Watchlist", "Other group"])
baskets.load("groups.json")
baskets.export_stocks("Watchlist", "stocks.csv")
baskets.import_stocks("Watchlist", "stocks.csv")
```

Export parent directories must exist. CSV and JSON exports use a temporary file
and replace an existing destination only after serialization completes.

## Data updates

`update_data()` deduplicates constituent tickers across all selected groups,
including historical members. By default it uses the existing `SQEquityClient`
to retrieve up to 100,000 daily bars per ticker, using its daily CDN data rather
than unrelated provider caches. The default output directory is `data/baskets`.
Downloads are normalized to UTC, sorted, deduplicated by timestamp, and stored
as versioned Parquet files. Dataset identities are stable per ticker and use
`source="sq-equity"`, `timeframe="D1"`, and the Default broker. Repeated updates
replace catalog metadata while retaining previously downloaded files.

Without an injected job manager the method blocks until the updates finish:

```python
result = baskets.update_data("Watchlist", data_dir="data/baskets")
```

Inject the host job manager to submit work to its I/O thread pool:

```python
service = Baskets(gateway, jobs=job_manager)
result = service.update_data(["Watchlist", "Other group"])
```

The response then contains the submitted job record. Job progress is reported
per ticker, and pause/cancel requests are checked between tickers. The caller
owns the job manager's lifecycle. An injected `client` must implement
`get_bars(ticker, "D1", count=100000)` and return a nonempty pandas DataFrame
with a DatetimeIndex and `Open`, `High`, `Low`, and `Close` columns. Caller-owned
clients are not closed by the service.

Each ticker is saved independently. Completed downloads remain available when
another ticker fails; the synchronous failure response includes `completed`,
`failed`, and `updated_count` in `error.details`. Background jobs fail on partial
failure as well. If catalog registration fails, the new unregistered Parquet
file is removed. Network requests and multi-file downloads are not one database
transaction.

CLI commands for all eleven methods are registered under `data-manager basket`.
See `docs/cli/haruquantai-cli.md` for arguments and examples. CLI formatting helpers
live in `cli_formatters.py` and remain re-exported from `cli.py`.

The workspace `http.py` owns all authenticated basket routes:

| Route | Service method |
| --- | --- |
| `GET /api/v1/data/baskets` | `list` |
| `POST /api/v1/data/baskets` | `add` or `edit` when an ID is present |
| `POST /api/v1/data/baskets/edit` | Bulk `edit` |
| `POST /api/v1/data/baskets/delete` | `delete` |
| `GET /api/v1/data/baskets/{id}/stocks` | `list_stocks` |
| `PUT /api/v1/data/baskets/{id}/stocks` | `edit_stocks` |
| `POST /api/v1/data/baskets/{id}/import-stocks` | `import_stocks` |
| `POST /api/v1/data/baskets/{id}/export-stocks` | `export_stocks` |
| `POST /api/v1/data/baskets/save` | `save` |
| `POST /api/v1/data/baskets/load` | `load` |
| `POST /api/v1/data/baskets/update-data` | `update_data` through the host job manager |

Browser requests use string IDs and body `ids` for selected groups. Membership
PUT accepts `symbols`, an array of ticker;from;to lines. File imports accept a
`content` string; exports return `content` and `count`. JSON/CSV transfers are
limited to 20 MiB. These adapters use temporary files to invoke the same service
methods rather than reproducing import/export behavior in the browser.

The Stock groups tab exposes Add, Edit selected (including bulk descriptions),
Update data, Edit stocks, Mass delete, Save, and Load. Its stock editor fetches
saved memberships before editing and uses the service for CSV import/export.
Group JSON imports are atomic and reject duplicate names. Counts and readiness
come from the backend's basket summaries. Names created by the CLI are displayed
as saved, with no bracket requirement.

Browser updates run on the host's I/O thread pool. The UI polls
`GET /api/v1/data/basket-jobs/{job_id}` for authoritative progress and refreshes
the catalog on completion or failure. Pause, resume, and cancel use POST to
`/api/v1/data/basket-jobs/{job_id}/pause`, `/resume`, and `/stop`. GET requests
never change job state. The backend lazily owns the basket job manager and
cancels its outstanding work during application shutdown.
