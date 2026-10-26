# Historical broker sources

Data Manager now uses the existing clients demonstrated in
`scripts/examples/brokers_data.py` for registration and real historical downloads.
Registration creates `datamgr_datasets` records; it does not fabricate observations.
The source menus use a shared backend-connected dialog. “Add symbols” registers
only; “Add and download” registers and starts an application-owned job.

| CLI / storage source | Provider | Native historical resolutions exposed |
| --- | --- | --- |
| `darwinex` | Darwinex | M1, D1, ticks |
| `binance` | Binance spot | Supported Binance bar intervals |
| `binance_coinm` | Binance Coin-M | Supported Binance bar intervals |
| `binance_usdtm` | Binance USDT-M | Supported Binance bar intervals |
| `bitfinex` | Bitfinex | Supported Bitfinex bar intervals |
| `coinbase` | Coinbase | M1, M5, M15, H1, H6, D1 |
| `poloniex` | Poloniex | M5, M15, M30, H2, H4, D1 |
| `yahoo` | Yahoo | Supported Yahoo intervals, default D1 |
| `sq_equity` | SQ Equity | D1 CDN history |
| `sq_futures` | SQ Futures | D1 CDN history |
| `mt5` | Connected MT5 EA bridge | M1, M5, M15, M30, H1, H4, D1 |

`capabilities` returns the exact accepted intervals. Unsupported resolutions fail
validation instead of silently falling back to another timeframe. Crypto historical
trades are not presented as historical bid/ask ticks.

## Storage and completeness

All sources use the shared PyArrow writer, ZSTD level 6, integer int64 prices and UTC
timestamps. Bars have uint64 volume and use
`data/market/{source}/{timeframe}/{dataset-symbol}/{year}.parquet`; ticks use
`data/market/{source}/ticks/{dataset-symbol}/{year}/{month}.parquet`.
Native daily or five-minute records remain D1 or M5; they are not relabeled M1.
Each year/month is one file with batched row groups and recoverable publication.

The generic source storage unit defaults to `0.00000001` and is configurable with
`--tick-size` or the dialog’s “Price storage unit”. This is an encoding precision,
not an assertion about the venue’s current minimum tradable tick. Prices round
half-even to that explicitly recorded unit before integer encoding; this handles
Yahoo’s historical floating-point quotes and adjusted prices without pretending
all prices have two decimal places. Dukascopy retains its catalog instrument units.
The existing broker DataFrame’s volume semantics are preserved; no synthetic volume
is generated. Some crypto clients express volume as integer counts/whole units.

Crypto requests span at most 200 candles, below the smallest exchange page limit.
Yahoo and MT5 bar requests are bounded; SQ/Darwinex requests are divided by year.
Bounded SQ/Darwinex calls no longer apply their default recent-row limit. Only genuine
`NO_DATA` intervals may be skipped; network/provider failures fail the job. An
entirely empty download fails. Committed intervals remain available after a later
failure or cancellation.

The configured SQ client currently points at a sample CDN. Live checks found its
AAPL daily archive ended on 15 May 2024; January 2025 had no data, while 8–9 January
2024 succeeded for AAPL and @ES. Registration is not proof that a feed supplies a
particular requested date range. Real subscription feeds/minute CDN access require
the corresponding broker adapter support and credentials.

## Download modes

Every source offers **Add only missing data** (default) and **Overwrite existing
data** in the UI. The equivalent CLI flags are `--missing-only` and `--overwrite`;
they cannot be combined.

Missing-only checks the actual catalog files and their bar timestamps, including
internal gaps, before requesting data. Successful downloads record verified ranges
alongside the manifest. Confirmed empty internal intervals are remembered so market
closures are not fetched repeatedly. Unavailable leading/trailing bar history is
not marked complete, allowing later downloads to extend it. Missing physical files
invalidate coverage. Legacy ticks without verified coverage require one fetch;
their first and last timestamps cannot prove completeness.

Overwrite requests the entire selected range and replaces its observations while
preserving records outside it. Empty or failed responses do not erase existing
data. Both modes retain canonical files and integer schemas. Clearing a dataset
also clears its coverage.

## Backend and UI

- `GET /api/v1/data/sources/{provider}/capabilities`
- `POST /api/v1/data/sources/{provider}/add`, with `definitions`
- `POST /api/v1/data/providers/download`, with `provider: "market"`, persisted
  `targets: [{"id": "..."}]`, `date_from`, `date_to`, and `overwrite`
- Existing `/download-jobs/{id}` status and pause/resume/stop routes handle the
  `market.download` jobs alongside Dukascopy jobs.

The browser restores the job ID, reads actual progress, refreshes the database
catalog at completion and displays transport/provider errors. Backend restart
reconciliation marks orphaned jobs interrupted. Former browser simulations are
retired from the source-menu entry points; their stored browser data is preserved.
Update selected/all and the SQ update actions also submit real jobs.

## MT5

The UI’s MT5 dialog can start the local bridge and check the EA connection. Configure
the EA with the returned host, port and authentication token. The token field is
masked and is not written into dataset metadata. The backend owns and closes this
bridge. Data downloads do not arm trading or submit orders.

CLI downloads start their own listener using the existing `MT5_BRIDGE_HOST`,
`MT5_BRIDGE_PORT`, `MT5_BRIDGE_TOKEN` and `MT5_BRIDGE_TIMEOUT` environment settings,
then wait for the EA (`--wait-seconds`, default 30). Use an available port; the CLI
and backend cannot both own the same listener port. Without an EA connection,
downloads fail truthfully; they do not substitute simulated bars or parse a selected
terminal folder as if it were a live connection.

See [CLI examples](../cli/haruquantai-cli.md) for registration and download commands.
